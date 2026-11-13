import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
const local = path.join(
  process.cwd(),
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const exe =
  process.env.SUMAFIRE_PYTHON ||
  (existsSync(local)
    ? local
    : process.platform === "win32"
      ? "python"
      : "python3");
const r = spawnSync(
  exe,
  ["pipeline/import_data.py", ...process.argv.slice(2)],
  { stdio: "inherit" },
);
if (r.error) console.error("Create .venv and install requirements.txt first.");
process.exit(r.status ?? 1);
