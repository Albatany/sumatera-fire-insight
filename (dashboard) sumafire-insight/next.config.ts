import type { NextConfig } from "next";
const config: NextConfig = {
  serverExternalPackages: ["@duckdb/node-api", "@duckdb/node-bindings"],
  outputFileTracingIncludes: {
    "/api/data": ["./data/active.json", "./data/processed/**/*"],
    "/api/boundary": [
      "./data/active.json",
      "./data/processed/**/*",
      "./public/geo/*",
    ],
  },
  poweredByHeader: false,
  devIndicators: false,
};
export default config;
