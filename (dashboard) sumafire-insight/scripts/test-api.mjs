import assert from "node:assert/strict";
import fs from "node:fs/promises";
import ts from "typescript";
import { NextRequest } from "next/server.js";
// Test real route handlers in-process without starting another server.
await fs.mkdir("test-results", { recursive: true });
for (const [input, output] of [
  ["src/lib/server.ts", "test-results/server-test.mjs"],
  ["src/app/api/data/route.ts", "test-results/route-test.mjs"],
]) {
  const source = await fs.readFile(input, "utf8");
  const compiled = ts
    .transpileModule(source, {
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
      },
    })
    .outputText.replace(/import ['"]server-only['"];?/, "")
    .replaceAll("@/lib/server", "./server-test.mjs")
    .replaceAll("next/server", "next/server.js");
  await fs.writeFile(output, compiled);
}
const { GET } = await import("../test-results/route-test.mjs");
const request = process.env.SUMAFIRE_TEST_URL
  ? fetch
  : async (url) => GET(new NextRequest(url));
const base = process.env.SUMAFIRE_TEST_URL || "http://localhost:3000";
let passed = 0;
const check = (name, fn) => {
  fn();
  passed++;
  console.log("PASS " + name);
};
async function get(q, code = 200) {
  const r = await request(base + "/api/data?" + q);
  assert.equal(r.status, code, q);
  return r.json();
}
const m = await get("kind=status");
check("research count", () => assert.equal(m.retained_rows, 154184));
check("classification not fitted", () =>
  assert.equal(m.artifacts.prediction, null),
);
const s = await get("kind=stats");
check("KPI matches import", () =>
  assert.equal(s.kpi.detections, m.retained_rows),
);
for (const k of [
  "annual",
  "monthly",
  "regions",
  "satellites",
  "daynight",
  "confidence",
  "frp",
  "heatmap",
])
  check(k + " balances", () =>
    assert.equal(
      s[k].reduce((a, r) => a + r.detections, 0),
      m.retained_rows,
    ),
  );
const c = await get("kind=clusters");
check("cluster count", () => assert.equal(c.summary.clusters, 3678));
check("noise count", () => assert.equal(c.summary.noise, 74383));
const yr = await get("kind=stats&from=2026-01-01&to=2026-10-30");
check("2026 count", () => assert.equal(yr.kpi.detections, 20252));
const reg = await get("kind=stats&region=Jambi&satellite=Terra");
check("combined filters", () => {
  assert.equal(reg.regions.length, 1);
  assert.equal(reg.regions[0].name, "Jambi");
  assert.equal(reg.satellites[0].name, "Terra");
});
const map = await get("kind=map");
check("bounded map", () => {
  assert.equal(map.mode, "aggregation");
  assert.ok(map.features.features.length <= 5000);
  assert.equal(map.total, 154184);
});
const points = await get("kind=map&from=2025-01-01&to=2025-01-01");
check("point cap", () => assert.ok(points.features.features.length <= 4000));
const comp = await get("kind=compare&yearA=2025&yearB=2026");
check("matched cutoff", () => assert.equal(comp.end_mmdd, "10-30"));
check("2025 matched count", () =>
  assert.equal(
    comp.rows
      .filter((r) => r.year === 2025)
      .reduce((a, r) => a + r.detections, 0),
    4203,
  ),
);
for (const q of [
  "kind=stats&confidence=101",
  "kind=stats&from=2025-02-30",
  "kind=stats&from=2026-01-01&to=2025-01-01",
  "kind=map&bbox=0,0,NaN,1",
  "kind=stats&frpMin=100&frpMax=5",
  "kind=export",
]) {
  await get(q, 400);
  passed++;
  console.log("PASS rejected " + q);
}
const inj = await get(
  "kind=stats&region=" + encodeURIComponent("x' OR 1=1 --"),
);
check("bound parameters", () => assert.equal(inj.kpi.detections, 0));
const absent = await get("kind=predictions");
check("prediction gate", () => assert.equal(absent.available, false));
const ex = await request(
  base + "/api/data?kind=export&from=2025-01-01&to=2025-01-31",
);
check("CSV export", () => assert.equal(ex.status, 200));
console.log(
  JSON.stringify({
    status: "PASS",
    passed,
    snapshot: m.snapshot,
    mode: process.env.SUMAFIRE_TEST_URL ? "HTTP" : "in-process route handler",
  }),
);
