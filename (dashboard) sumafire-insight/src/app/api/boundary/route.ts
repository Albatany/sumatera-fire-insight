import fs from "node:fs/promises";
import path from "node:path";
import { snapshot } from "@/lib/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET() {
  try {
    const s = await snapshot();
    const p = s?.meta.region_verified
      ? path.join(s.dir, "boundary.json")
      : path.join(process.cwd(), "public/geo/sumatra-context.geojson");
    const text = await fs.readFile(p, "utf8");
    return new Response(text, {
      headers: {
        "Content-Type": "application/geo+json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json({ type: "FeatureCollection", features: [] });
  }
}
