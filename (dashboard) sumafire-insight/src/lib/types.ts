import type { FeatureCollection } from "geojson";
export type Row = Record<string, string | number | null>;
export interface Artifact {
  noise_label?: string;
  algorithm?: string;
  model_name?: string;
  parameters?: Record<string, string | number>;
  limitations: string[];
  rows: number;
  sha256: string;
  evaluation?: Record<string, unknown>;
  evaluation_source?: string;
  validation_evidence?: string;
}
export interface Meta {
  connected: true;
  schema_version: number;
  snapshot: string;
  name: string;
  imported_at: string;
  observation_start: string;
  observation_end: string;
  cutoff_utc: string;
  input_rows: number;
  retained_rows: number;
  rejected_rows: number;
  filtered_rows: number;
  file_count: number;
  regions: string[];
  years: number[];
  region_verified: boolean;
  versions: {
    value: string;
    rows: number;
    status: string;
    evidence: string | null;
  }[];
  satellites: string[];
  downloaded_at: string | null;
  source_url: string;
  scope: string;
  boundary: Record<string, unknown>;
  provisional_years: number[];
  limitations: string[];
  original_research_audit: Record<string, string | number> | null;
  artifacts: { clustering: Artifact | null; prediction: Artifact | null };
  import_report: {
    duplicate_keys: number;
    duplicate_policy: string;
    missing_values: Record<string, number>;
    issue_counts: Record<string, number>;
    files: Record<string, unknown>[];
  };
  test_fixture: boolean;
  refresh_mode: string;
}
export type View =
  | "overview"
  | "explorer"
  | "analytics"
  | "clusters"
  | "predictions"
  | "transparency"
  | "research";
export interface Filters {
  from: string;
  to: string;
  region: string;
  satellite: string;
  version: string;
  daynight: string;
  confidence: string;
  frpMin: string;
  frpMax: string;
}
export const initialFilters: Filters = {
  from: "",
  to: "",
  region: "",
  satellite: "",
  version: "",
  daynight: "",
  confidence: "",
  frpMin: "",
  frpMax: "",
};
export interface Stats {
  connected: boolean;
  kpi: Row;
  annual: Row[];
  monthly: Row[];
  regions: Row[];
  satellites: Row[];
  daynight: Row[];
  confidence: Row[];
  frp: Row[];
  heatmap: Row[];
}
export interface MapData {
  connected: boolean;
  mode: "points" | "aggregation";
  total: number;
  returned: number;
  capped: boolean;
  cell_degrees?: number;
  features: FeatureCollection;
}
