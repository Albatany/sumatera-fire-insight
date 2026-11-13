import "server-only";
import fs from "node:fs/promises";
import path from "node:path";
import { DuckDBInstance, type DuckDBValue } from "@duckdb/node-api";
import { z } from "zod";
import type { Meta, Row } from "./types";
const root = path.resolve(process.env.SUMAFIRE_DATA_DIR || "./data");
const instances = new Map<string, Promise<DuckDBInstance>>();
export class InputError extends Error {}
export async function snapshot() {
  let a;
  try {
    a = JSON.parse(await fs.readFile(path.join(root, "active.json"), "utf8"));
  } catch (e) {
    if ((e as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw e;
  }
  if (!/^[\w-]+$/.test(a.snapshot)) throw Error("Invalid pointer");
  const dir = path.join(root, "processed", a.snapshot);
  const meta = JSON.parse(
    await fs.readFile(path.join(dir, "metadata.json"), "utf8"),
  ) as Meta;
  if (meta.schema_version !== 1 || meta.snapshot !== a.snapshot)
    throw Error("Metadata mismatch");
  if (meta.test_fixture && process.env.SUMAFIRE_ALLOW_TEST_FIXTURES !== "1")
    throw Error("Test fixture blocked");
  return { dir, meta };
}
export async function sql(
  dir: string,
  query: string,
  values: DuckDBValue[] = [],
): Promise<Row[]> {
  const file = path.join(dir, "observations.duckdb");
  if (!instances.has(file))
    instances.set(
      file,
      DuckDBInstance.create(file, {
        access_mode: "READ_ONLY",
        threads: "2",
        memory_limit: "256MB",
      }),
    );
  const c = await (await instances.get(file)!).connect();
  try {
    return (await c.runAndReadAll(query, values)).getRowObjectsJson() as Row[];
  } finally {
    c.closeSync();
  }
}
const date = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/)
  .refine(
    (x) =>
      !isNaN(Date.parse(x)) && new Date(x).toISOString().slice(0, 10) === x,
  );
const filters = z.object({
  from: date.optional(),
  to: date.optional(),
  region: z.string().max(120).optional(),
  satellite: z.enum(["Terra", "Aqua", "Unspecified"]).optional(),
  version: z.string().max(40).optional(),
  daynight: z.enum(["D", "N", "Unspecified"]).optional(),
  confidence: z.coerce.number().min(0).max(100).optional(),
  frpMin: z.coerce.number().min(0).max(1e7).optional(),
  frpMax: z.coerce.number().min(0).max(1e7).optional(),
});
function where(p: URLSearchParams, noDate = false) {
  const r = filters.safeParse(
    Object.fromEntries([...p].filter(([, v]) => v !== "")),
  );
  if (!r.success)
    throw new InputError(
      "Invalid filter: " +
        r.error.issues
          .map((x) => x.path.join(".") + " " + x.message)
          .join("; "),
    );
  const f = r.data;
  if (f.from && f.to && f.from > f.to)
    throw new InputError("Start date exceeds end date");
  if (f.frpMin !== undefined && f.frpMax !== undefined && f.frpMin > f.frpMax)
    throw new InputError("Minimum FRP exceeds maximum");
  const parts: string[] = [];
  const values: DuckDBValue[] = [];
  const add = (s: string, v: DuckDBValue) => {
    parts.push(s);
    values.push(v);
  };
  if (!noDate) {
    if (f.from) add("o.date >= ?", f.from);
    if (f.to) add("o.date <= ?", f.to);
  }
  for (const k of ["region", "satellite", "version", "daynight"] as const)
    if (f[k]) add(`o.${k} = ?`, f[k]!);
  if (f.confidence !== undefined) add("o.confidence >= ?", f.confidence);
  if (f.frpMin !== undefined) add("o.frp >= ?", f.frpMin);
  if (f.frpMax !== undefined) add("o.frp <= ?", f.frpMax);
  return { clause: parts.join(" AND ") || "TRUE", values };
}
export async function stats(dir: string, p: URLSearchParams) {
  const w = where(p);
  const base = `FROM observations o WHERE ${w.clause}`;
  const q = (s: string) => sql(dir, s, w.values);
  const [
    kpi,
    annual,
    monthly,
    regions,
    satellites,
    daynight,
    confidence,
    frp,
    heatmap,
  ] = await Promise.all([
    q(
      `SELECT count(*)::DOUBLE detections,count(DISTINCT CASE WHEN region<>'Unassigned' THEN region END)::DOUBLE regions,min(date) first_date,max(date) last_date,avg(frp) mean_frp ${base}`,
    ),
    q(
      `SELECT year::VARCHAR period,count(*)::DOUBLE detections ${base} GROUP BY year ORDER BY year`,
    ),
    q(
      `SELECT substr(date,1,7) period,count(*)::DOUBLE detections ${base} GROUP BY 1 ORDER BY 1`,
    ),
    q(
      `SELECT region name,count(*)::DOUBLE detections ${base} GROUP BY 1 ORDER BY 2 DESC LIMIT 30`,
    ),
    q(
      `SELECT satellite name,count(*)::DOUBLE detections ${base} GROUP BY 1 ORDER BY 1`,
    ),
    q(
      `SELECT daynight name,count(*)::DOUBLE detections ${base} GROUP BY 1 ORDER BY 1`,
    ),
    q(
      `SELECT CASE WHEN confidence IS NULL THEN 'Unknown' WHEN confidence<30 THEN '0–29' WHEN confidence<80 THEN '30–79' ELSE '80–100' END name,count(*)::DOUBLE detections ${base} GROUP BY 1 ORDER BY 1`,
    ),
    q(
      `SELECT CASE WHEN frp IS NULL THEN 'Unknown' WHEN frp<10 THEN '0–<10' WHEN frp<50 THEN '10–<50' WHEN frp<100 THEN '50–<100' ELSE '100+' END name,count(*)::DOUBLE detections ${base} GROUP BY 1 ORDER BY min(frp)`,
    ),
    q(
      `SELECT year::DOUBLE AS year,month::DOUBLE AS month,count(*)::DOUBLE detections ${base} GROUP BY 1,2 ORDER BY 1,2`,
    ),
  ]);
  return {
    kpi: kpi[0],
    annual,
    monthly,
    regions,
    satellites,
    daynight,
    confidence,
    frp,
    heatmap,
  };
}
export async function mapData(dir: string, p: URLSearchParams, meta: Meta) {
  const w = where(p);
  const b = (p.get("bbox") || "93,-7,109,8").split(",").map(Number);
  const zoom = Math.min(14, Math.max(0, Number(p.get("zoom") || 5)));
  if (
    b.length !== 4 ||
    b.some((x) => !Number.isFinite(x)) ||
    !Number.isFinite(zoom) ||
    b[0] >= b[2] ||
    b[1] >= b[3] ||
    b[0] < -180 ||
    b[2] > 180 ||
    b[1] < -90 ||
    b[3] > 90
  )
    throw new InputError("Invalid map bounds");
  const cid = p.get("cluster");
  if (cid && (!meta.artifacts.clustering || cid.length > 150))
    throw new InputError("Cluster unavailable");
  const base = `FROM observations o ${cid ? "JOIN cluster_members c USING(observation_id)" : ""} WHERE ${w.clause} AND longitude BETWEEN ? AND ? AND latitude BETWEEN ? AND ? ${cid ? "AND cluster_id = ?" : ""}`;
  const values = [...w.values, b[0], b[2], b[1], b[3], ...(cid ? [cid] : [])];
  const total = Number(
    (await sql(dir, `SELECT count(*)::DOUBLE n ${base}`, values))[0].n,
  );
  const mode =
    total <= 4000 && p.get("mode") !== "aggregation" ? "points" : "aggregation";
  const step = Math.max(0.025, 8 / 2 ** Math.floor(zoom - 1));
  const rows =
    mode === "points"
      ? await sql(
          dir,
          `SELECT observation_id,latitude,longitude,date,region,satellite,confidence,frp,version,type ${base} ORDER BY observation_id LIMIT 4000`,
          values,
        )
      : await sql(
          dir,
          `SELECT floor(longitude/${step})*${step}+${step / 2} longitude,floor(latitude/${step})*${step}+${step / 2} latitude,count(*)::DOUBLE detections,avg(frp) frp ${base} GROUP BY 1,2 ORDER BY 3 DESC LIMIT 5000`,
          values,
        );
  return {
    mode,
    total,
    returned: rows.length,
    capped: mode === "aggregation" && rows.length === 5000,
    cell_degrees: step,
    features: {
      type: "FeatureCollection",
      features: rows.map((r) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [r.longitude, r.latitude] },
        properties: r,
      })),
    },
  };
}
export async function compare(dir: string, p: URLSearchParams, meta: Meta) {
  const years = [Number(p.get("yearA")), Number(p.get("yearB"))];
  if (years.some((y) => !meta.years.includes(y)))
    throw new InputError("Choose years present in dataset");
  const bound = await sql(
    dir,
    "SELECT max(substr(date,6,5)) mmdd FROM observations WHERE year IN (?,?) GROUP BY year",
    years,
  );
  const end = bound.map((x) => String(x.mmdd)).sort()[0];
  const w = where(p, true);
  const rows = await sql(
    dir,
    `SELECT year::DOUBLE AS year,month::DOUBLE AS month,count(*)::DOUBLE detections FROM observations o WHERE ${w.clause} AND year IN (?,?) AND substr(date,6,5)<=? GROUP BY 1,2 ORDER BY 1,2`,
    [...w.values, ...years, end],
  );
  return {
    years,
    end_mmdd: end,
    rows,
    note: "Same January 1 to month/day window, bounded by the earlier last recorded date. Observation completeness is not verified. This replaces the global date filter.",
  };
}
export async function clusters(dir: string, p: URLSearchParams) {
  const w = where(p);
  const base = `FROM observations o JOIN cluster_members c USING(observation_id) WHERE ${w.clause}`;
  const [s, rows] = await Promise.all([
    sql(
      dir,
      `SELECT count(*)::DOUBLE members,count(*) FILTER(WHERE point_role='noise')::DOUBLE noise,count(DISTINCT CASE WHEN point_role<>'noise' THEN cluster_id END)::DOUBLE clusters ${base}`,
      w.values,
    ),
    sql(
      dir,
      `SELECT cluster_id,count(*)::DOUBLE detections,min(date) start_date,max(date) end_date,avg(latitude) latitude,avg(longitude) longitude,mode(region) region ${base} AND point_role<>'noise' GROUP BY 1 ORDER BY 2 DESC LIMIT 100`,
      w.values,
    ),
  ]);
  return { summary: s[0], rows };
}
export async function observations(
  dir: string,
  p: URLSearchParams,
  exporting = false,
) {
  const w = where(p);
  if (
    exporting &&
    Number(
      (
        await sql(
          dir,
          `SELECT count(*)::DOUBLE n FROM observations o WHERE ${w.clause}`,
          w.values,
        )
      )[0].n,
    ) > 50000
  )
    throw new InputError("Export limited to 50,000 rows. Narrow your filters.");
  return sql(
    dir,
    `SELECT observation_id,date,latitude,longitude,region,satellite,confidence,frp,version,daynight FROM observations o WHERE ${w.clause} ORDER BY observed_at,observation_id LIMIT ${exporting ? 50000 : 100}`,
    w.values,
  );
}
