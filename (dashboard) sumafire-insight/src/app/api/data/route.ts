import { NextRequest, NextResponse } from "next/server";
import {
  snapshot,
  stats,
  mapData,
  clusters,
  compare,
  observations,
  sql,
  InputError,
} from "@/lib/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;
export async function GET(req: NextRequest) {
  try {
    const s = await snapshot();
    if (!s)
      return NextResponse.json(
        { connected: false, reason: "Dataset not connected" },
        { headers: { "Cache-Control": "no-store" } },
      );
    const p = req.nextUrl.searchParams;
    let result: object;
    switch (p.get("kind") || "status") {
      case "status":
        result = s.meta;
        break;
      case "stats":
        result = await stats(s.dir, p);
        break;
      case "map":
        result = await mapData(s.dir, p, s.meta);
        break;
      case "clusters":
        result = s.meta.artifacts.clustering
          ? {
              ...(await clusters(s.dir, p)),
              artifact: s.meta.artifacts.clustering,
            }
          : { available: false };
        break;
      case "compare":
        result = await compare(s.dir, p, s.meta);
        break;
      case "observations":
        result = { rows: await observations(s.dir, p) };
        break;
      case "predictions":
        result = s.meta.artifacts.prediction
          ? {
              artifact: s.meta.artifacts.prediction,
              rows: await sql(
                s.dir,
                "SELECT * FROM predictions ORDER BY target_time DESC LIMIT 200",
              ),
            }
          : { available: false };
        break;
      case "export": {
        const rows = await observations(s.dir, p, true);
        const keys = [
          "observation_id",
          "date",
          "latitude",
          "longitude",
          "region",
          "satellite",
          "confidence",
          "frp",
          "version",
          "daynight",
        ];
        const esc = (v: unknown) => {
          let x = v === null ? "" : String(v);
          if (typeof v === "string" && /^[=+\-@\t\r]/.test(x)) x = "'" + x;
          return '"' + x.replaceAll('"', '""') + '"';
        };
        return new Response(
          [
            keys.join(","),
            ...rows.map((r) => keys.map((k) => esc(r[k])).join(",")),
          ].join("\r\n"),
          {
            headers: {
              "Content-Type": "text/csv; charset=utf-8",
              "Content-Disposition":
                'attachment; filename="sumafire-observations.csv"',
              "Cache-Control": "no-store",
            },
          },
        );
      }
      default:
        throw new InputError("Unknown endpoint");
    }
    return NextResponse.json(
      { connected: true, snapshot: s.meta.snapshot, ...result },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (e) {
    if (e instanceof InputError)
      return NextResponse.json({ error: e.message }, { status: 400 });
    console.error("Dataset query:", e);
    return NextResponse.json(
      {
        error:
          "Dataset could not be read. Run data:verify or restore a valid snapshot.",
      },
      { status: 503 },
    );
  }
}
