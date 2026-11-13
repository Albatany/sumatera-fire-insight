import { spawn } from "node:child_process";
const args = process.argv.slice(2);
const val = (k, v) => (args.includes(k) ? args[args.indexOf(k) + 1] : v);
const child = spawn(
  process.execPath,
  [
    "node_modules/next/dist/bin/next",
    "dev",
    "--hostname",
    val("--host", "127.0.0.1"),
    "--port",
    val("--port", "3000"),
  ],
  { stdio: "inherit" },
);
for (const signal of ["SIGINT", "SIGTERM"])
  process.on(signal, () => child.kill(signal));
child.on("exit", (code) => process.exit(code ?? 1));
