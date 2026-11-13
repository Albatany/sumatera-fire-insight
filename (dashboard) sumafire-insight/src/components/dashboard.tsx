"use client";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { MotionConfig, motion } from "motion/react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  CalendarDays,
  ChartNoAxesCombined,
  ChevronLeft,
  ChevronRight,
  Database,
  ExternalLink,
  Filter,
  FlaskConical,
  Layers,
  LayoutDashboard,
  MapPin,
  Menu,
  Orbit,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  X,
} from "lucide-react";
import type { Filters, Meta, Row, Stats, View, Artifact } from "@/lib/types";
import { initialFilters } from "@/lib/types";
import { useData } from "@/lib/use-data";
import { day, num } from "@/lib/utils";
import { Panel, Empty, Loading, ErrorBox } from "./common";
import { Button } from "./ui/button";
import { ImportHelp, Tip } from "./ui/help";
import { Trend, Bars, Heatmap, ComparePlot } from "./charts";
const HotspotMap = dynamic(() => import("./hotspot-map"), {
  ssr: false,
  loading: () => <Loading />,
});
const pages = [
  { id: "overview", title: "Overview", icon: LayoutDashboard },
  { id: "explorer", title: "Hotspot explorer", icon: MapPin },
  { id: "analytics", title: "Historical analytics", icon: ChartNoAxesCombined },
  { id: "clusters", title: "Cluster explorer", icon: Layers },
  { id: "predictions", title: "Prediction lab", icon: FlaskConical },
  { id: "transparency", title: "Data transparency", icon: ShieldCheck },
  { id: "research", title: "About the research", icon: BookOpen },
] as const;
const subtitles: Record<View, string> = {
  overview: "A clearer view of Sumatra’s thermal landscape.",
  explorer: "Explore satellite observations in their geographic context.",
  analytics: "Find patterns. Keep the observation limits in view.",
  clusters:
    "Explore imported scientific clusters, without rerunning the experiment.",
  predictions:
    "Validated research predictions, when the evidence is available.",
  transparency:
    "Every observation has a source. Every transformation leaves a trace.",
  research: "An independent research project, built to be understood.",
};
function Table({
  rows,
  columns,
}: {
  rows: Row[];
  columns: [string, string][];
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map(([k, label]) => (
              <th key={k}>{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map(([k]) => (
                <td key={k}>
                  {r[k] === null || r[k] === undefined
                    ? "—"
                    : typeof r[k] === "number"
                      ? num(r[k])
                      : String(r[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <p className="table-empty">No matching records.</p>}
    </div>
  );
}
function Metric({
  label,
  value,
  note,
  icon: Icon,
}: {
  label: string;
  value: string;
  note: string;
  icon: typeof Database;
}) {
  return (
    <motion.div
      className="metric"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div>
        <span>{label}</span>
        <Icon size={16} />
      </div>
      <strong key={value}>{value}</strong>
      <small>{note}</small>
    </motion.div>
  );
}
function FilterBar({
  filters,
  set,
  meta,
}: {
  filters: Filters;
  set: (v: Filters) => void;
  meta: Meta | null;
}) {
  const [more, setMore] = useState(false);
  const change = (k: keyof Filters, v: string) => set({ ...filters, [k]: v });
  return (
    <div className="filters">
      <div className="filter-first">
        <span className="filter-label">
          <Filter size={14} />
          Filters
        </span>
        <label>
          From
          <input
            type="date"
            value={filters.from}
            onInput={(e) => change("from", e.currentTarget.value)}
            onChange={(e) => change("from", e.target.value)}
          />
        </label>
        <span className="date-dash">—</span>
        <label>
          To
          <input
            type="date"
            value={filters.to}
            onInput={(e) => change("to", e.currentTarget.value)}
            onChange={(e) => change("to", e.target.value)}
          />
        </label>
        <label>
          Region
          <select
            value={filters.region}
            onChange={(e) => change("region", e.target.value)}
            disabled={!meta?.region_verified}
          >
            <option value="">All regions</option>
            {meta?.regions.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <label>
          Satellite
          <select
            value={filters.satellite}
            onChange={(e) => change("satellite", e.target.value)}
          >
            <option value="">All satellites</option>
            {(meta?.satellites || ["Terra", "Aqua"]).map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setMore(!more)}
          aria-expanded={more}
        >
          More filters{" "}
          <span className="filter-count">
            {Object.values(filters).filter(Boolean).length}
          </span>
        </Button>
        <Button size="sm" variant="ghost" onClick={() => set(initialFilters)}>
          Reset
        </Button>
      </div>
      {more && (
        <div className="filter-more">
          <label>
            Minimum confidence
            <input
              type="number"
              min="0"
              max="100"
              placeholder="0–100"
              value={filters.confidence}
              onChange={(e) => change("confidence", e.target.value)}
            />
          </label>
          <label>
            Day / night
            <select
              value={filters.daynight}
              onChange={(e) => change("daynight", e.target.value)}
            >
              <option value="">Both</option>
              <option value="D">Day</option>
              <option value="N">Night</option>
              <option value="Unspecified">Unspecified</option>
            </select>
          </label>
          <label>
            Minimum FRP (MW)
            <input
              type="number"
              min="0"
              value={filters.frpMin}
              onChange={(e) => change("frpMin", e.target.value)}
              placeholder="Any"
            />
          </label>
          <label>
            Maximum FRP (MW)
            <input
              type="number"
              min="0"
              value={filters.frpMax}
              onChange={(e) => change("frpMax", e.target.value)}
              placeholder="Any"
            />
          </label>
          <label>
            Literal version
            <select
              value={filters.version}
              onChange={(e) => change("version", e.target.value)}
            >
              <option value="">All versions</option>
              {meta?.versions.map((v) => (
                <option key={v.value}>{v.value}</option>
              ))}
            </select>
          </label>
        </div>
      )}
    </div>
  );
}
function Comparison({
  meta,
  query,
  refresh,
}: {
  meta: Meta;
  query: string;
  refresh: number;
}) {
  const [a, setA] = useState(meta.years.at(-2) || meta.years[0]);
  const [b, setB] = useState(meta.years.at(-1) || meta.years[0]);
  const r = useData<{
    rows: Row[];
    years: number[];
    end_mmdd: string;
    note: string;
  }>(`/api/data?kind=compare&${query}&yearA=${a}&yearB=${b}`, refresh);
  return (
    <Panel
      title="Compare years"
      sub="Equivalent calendar windows; shared filters except dates."
      action={
        <div className="compare-controls">
          <select
            aria-label="First comparison year"
            value={a}
            onChange={(e) => setA(Number(e.target.value))}
          >
            {meta.years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
          <span>vs</span>
          <select
            aria-label="Second comparison year"
            value={b}
            onChange={(e) => setB(Number(e.target.value))}
          >
            {meta.years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
        </div>
      }
    >
      {r.error ? (
        <ErrorBox message={r.error} />
      ) : r.data ? (
        <>
          <ComparePlot rows={r.data.rows} years={r.data.years} />
          <p className="caption">
            January 1 – {r.data.end_mmdd}. {r.data.note}
          </p>
        </>
      ) : (
        <Loading />
      )}
    </Panel>
  );
}
function Clusters({
  meta,
  query,
  refresh,
}: {
  meta: Meta | null;
  query: string;
  refresh: number;
}) {
  const r = useData<{ summary: Row; rows: Row[]; artifact: Artifact }>(
    meta?.artifacts.clustering ? `/api/data?kind=clusters&${query}` : null,
    refresh,
  );
  const [selected, setSelected] = useState("");
  if (!meta?.artifacts.clustering)
    return (
      <Panel title="Scientific clustering">
        <Empty
          title="Clustering research artifact not connected"
          text="Import verified observation memberships and experiment metadata to explore scientific clusters."
        />
      </Panel>
    );
  if (r.error) return <ErrorBox message={r.error} />;
  if (!r.data) return <Loading />;
  const s = r.data.summary;
  return (
    <>
      <div className="metric-grid three">
        <Metric
          label="Scientific clusters"
          value={num(s.clusters)}
          note="Represented under active filters"
          icon={Layers}
        />
        <Metric
          label="Noise observations"
          value={num(s.noise)}
          note={`${num((Number(s.noise) / Math.max(Number(s.members), 1)) * 100)}% of imported memberships in filter`}
          icon={ScanLine}
        />
        <Metric
          label="Clustered + noise members"
          value={num(s.members)}
          note="Imported research assignments"
          icon={Database}
        />
      </div>
      <div className="notice">
        {r.data.artifact.algorithm}. Parameters:{" "}
        {JSON.stringify(r.data.artifact.parameters)}. Filters change the
        displayed membership, not the original cluster definitions.
      </div>
      <Panel
        title="Cluster geography"
        sub="Select a scientific cluster; large groups are aggregated for rendering."
        action={
          <select
            aria-label="Scientific cluster"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">All observations</option>
            <option value={meta.artifacts.clustering.noise_label || "NOISE"}>
              Noise
            </option>
            {r.data.rows.map((x) => (
              <option key={String(x.cluster_id)} value={String(x.cluster_id)}>
                {String(x.cluster_id)} · {num(x.detections)}
              </option>
            ))}
          </select>
        }
      >
        <HotspotMap
          connected
          query={query}
          cluster={selected}
          refresh={refresh}
          height={460}
        />
      </Panel>
      <Panel
        title="Cluster membership summary"
        sub="Up to 100 largest represented clusters. Dates describe observed members, not fire duration."
      >
        <Table
          rows={r.data.rows}
          columns={[
            ["cluster_id", "Cluster ID"],
            ["detections", "Members"],
            ["region", "Modal region"],
            ["start_date", "First date"],
            ["end_date", "Last date"],
          ]}
        />
      </Panel>
      {r.data.artifact.limitations.map((x) => (
        <p className="caption" key={x}>
          {x}
        </p>
      ))}
    </>
  );
}
function Predictions({
  meta,
  refresh,
}: {
  meta: Meta | null;
  refresh: number;
}) {
  const r = useData<{ artifact: Artifact; rows: Row[] }>(
    meta?.artifacts.prediction ? "/api/data?kind=predictions" : null,
    refresh,
  );
  if (!meta?.artifacts.prediction)
    return (
      <div className="prediction-empty">
        <span className="lab-symbol">
          <FlaskConical size={37} />
        </span>
        <span className="eyebrow">RESEARCH GATE · NOT ACTIVATED</span>
        <h2>Evidence comes before prediction.</h2>
        <p>
          Classification results are not available. Hotspot-only records do not
          establish adequately observed negative labels.
        </p>
        <div className="gate-grid">
          <div>
            <b>01</b>
            <strong>Observation coverage</strong>
            <span>Verify fire, non-fire, cloud and missing observations.</span>
          </div>
          <div>
            <b>02</b>
            <strong>Temporal validation</strong>
            <span>Fit on 2015–2023, validate on 2024, final test on 2025.</span>
          </div>
          <div>
            <b>03</b>
            <strong>Validated artifact</strong>
            <span>
              Import predictions, model metadata and evaluation evidence.
            </span>
          </div>
        </div>
        <p className="caption">
          No XGBoost model is trained by this dashboard. No accuracy or
          prediction is inferred from descriptive counts.
        </p>
      </div>
    );
  return (
    <>
      {r.error ? (
        <ErrorBox message={r.error} />
      ) : r.data ? (
        <>
          <Panel
            title={r.data.artifact.model_name || "Imported model"}
            sub="Imported validation evidence; these figures are not recalculated by the dashboard."
          >
            <p className="body-copy">{r.data.artifact.validation_evidence}</p>
            {r.data.artifact.evaluation && (
              <pre className="code-block">
                {JSON.stringify(r.data.artifact.evaluation, null, 2)}
              </pre>
            )}
            <p className="caption">
              Evaluation source:{" "}
              {r.data.artifact.evaluation_source || "No metrics supplied"}
            </p>
          </Panel>
          <Panel
            title="Historical predictions"
            sub="Latest 200 imported records. Independent of observation filters."
          >
            <Table
              rows={r.data.rows}
              columns={[
                ["region", "Region"],
                ["issue_time", "Issued (UTC)"],
                ["target_time", "Target (UTC)"],
                ["predicted_class", "Class"],
                ["probability", "Probability"],
                ["actual_class", "Actual"],
                ["split", "Split"],
              ]}
            />
          </Panel>
          {r.data.artifact.limitations.map((x) => (
            <p key={x} className="notice">
              {x}
            </p>
          ))}
        </>
      ) : (
        <Loading />
      )}
    </>
  );
}
function Transparency({ meta }: { meta: Meta | null }) {
  if (!meta)
    return (
      <Panel title="A traceable data foundation">
        <Empty />
        <p className="caption">
          An import manifest records SHA-256, source rows, dates, literal
          versions, exclusions and missing values. No status is guessed from a
          filename.
        </p>
      </Panel>
    );
  return (
    <>
      <div className="metric-grid">
        <Metric
          label="Input observations"
          value={num(meta.input_rows)}
          note={`${meta.file_count} dashboard input file(s)`}
          icon={Database}
        />
        <Metric
          label="Retained"
          value={num(meta.retained_rows)}
          note="After explicit validation and filtering"
          icon={ShieldCheck}
        />
        <Metric
          label="Rejected"
          value={num(meta.rejected_rows)}
          note="Invalid records; reasons logged"
          icon={ScanLine}
        />
        <Metric
          label="Filtered"
          value={num(meta.filtered_rows)}
          note="Outside boundary / cutoff / explicit duplicates"
          icon={Filter}
        />
      </div>
      {meta.original_research_audit && (
        <div className="notice">
          <b>Original research audit:</b>{" "}
          {num(meta.original_research_audit.raw_rows)} raw observations across{" "}
          {num(meta.original_research_audit.raw_files)} CSV files. The dashboard
          adapter imports an already processed copy; its input count is
          different by design. Evidence:{" "}
          {String(meta.original_research_audit.evidence)}.
        </div>
      )}
      <div className="two-col">
        <Panel title="Provenance & coverage">
          <dl className="metadata">
            <dt>Source</dt>
            <dd>
              <a href={meta.source_url} target="_blank" rel="noreferrer">
                NASA FIRMS <ExternalLink size={12} />
              </a>
            </dd>
            <dt>Instrument</dt>
            <dd>MODIS; unknown values remain unspecified</dd>
            <dt>Observation range (UTC)</dt>
            <dd>
              {meta.observation_start} → {meta.observation_end}
            </dd>
            <dt>Requested cutoff (UTC)</dt>
            <dd>{meta.cutoff_utc}</dd>
            <dt>Downloaded at</dt>
            <dd>
              {meta.downloaded_at || "Not supplied; import time is separate"}
            </dd>
            <dt>Imported at</dt>
            <dd>{meta.imported_at}</dd>
            <dt>Spatial scope</dt>
            <dd>{meta.scope}</dd>
            <dt>Boundary verified</dt>
            <dd>
              {meta.region_verified
                ? "Yes, geometry validated"
                : "No; regions not asserted"}
            </dd>
            <dt>Duplicate keys</dt>
            <dd>
              {meta.import_report.duplicate_keys}; policy:{" "}
              {meta.import_report.duplicate_policy}
            </dd>
            <dt>Snapshot</dt>
            <dd className="mono">{meta.snapshot}</dd>
          </dl>
        </Panel>
        <Panel
          title="Version audit"
          sub="Literal strings are preserved. Processing status requires provenance evidence."
        >
          <Table
            rows={meta.versions.map((v) => ({
              value: v.value,
              rows: v.rows,
              status: v.status,
            }))}
            columns={[
              ["value", "Value"],
              ["rows", "Rows"],
              ["status", "Evidence status"],
            ]}
          />
          {meta.versions.map((v) => (
            <p className="caption" key={v.value}>
              <b>{v.value}:</b>{" "}
              {v.evidence || "No interpretation evidence supplied."}
            </p>
          ))}
          {meta.provisional_years.length > 0 && (
            <div className="notice">
              {meta.provisional_years.join(", ")} is flagged provisional by the
              imported metadata. Do not compare with a complete year without
              matching calendar windows.
            </div>
          )}
        </Panel>
      </div>
      <div className="two-col">
        <Panel
          title="Missing values in inputs"
          sub="Missing optional numeric fields are retained, not filled with zero."
        >
          <Table
            rows={Object.entries(meta.import_report.missing_values).map(
              ([name, count]) => ({ name, count }),
            )}
            columns={[
              ["name", "Attribute"],
              ["count", "Missing"],
            ]}
          />
        </Panel>
        <Panel title="Interpretation limits">
          {meta.limitations.map((x) => (
            <p className="limitation" key={x}>
              {x}
            </p>
          ))}
          <p className="limitation">
            No recorded detection does not establish absence of fire. Satellite
            overpass, clouds, sensor sensitivity and data availability affect
            coverage.
          </p>
        </Panel>
      </div>
      <Panel
        title="Input manifest"
        sub="SHA-256 identifies the exact bytes imported."
      >
        <Table
          rows={meta.import_report.files.map((f) => ({
            file: String(f.file),
            rows: Number(f.rows),
            sha256: String(f.sha256),
            start: String(f.start),
            end: String(f.end),
          }))}
          columns={[
            ["file", "File"],
            ["rows", "Rows"],
            ["sha256", "SHA-256"],
            ["start", "First UTC"],
            ["end", "Last UTC"],
          ]}
        />
      </Panel>
    </>
  );
}
function Research() {
  return (
    <>
      <div className="research-hero">
        <span className="eyebrow">
          INDEPENDENT RESEARCH | UNIVERSITAS JAMBI
        </span>
        <h2>
          Making satellite observations
          <br />
          easier to examine.
        </h2>
        <p>
          SUMAFIRE INSIGHT is a companion to an undergraduate data mining study
          of thermal anomaly observations across mainland Sumatra. It supports
          exploration, reproducibility and critical discussion.
        </p>
      </div>
      <div className="two-col">
        <Panel title="The researcher">
          <dl className="metadata">
            <dt>Name</dt>
            <dd>Muhammad Aziz Syah Dani</dd>
            <dt>Student ID</dt>
            <dd>F1E325063</dd>
            <dt>Majoring</dt>
            <dd>Informatika</dd>
            <dt>University</dt>
            <dd>Universitas Jambi</dd>
            <dt>Course</dt>
            <dd>Penambangan Data</dd>
          </dl>
        </Panel>
        <Panel title="Research boundaries">
          <p className="body-copy">
            The intended classification task is next-day hotspot surge
            detection, subject to valid labels and observation coverage. The
            website displays independently imported research artifacts; it does
            not train models.
          </p>
          <p className="body-copy">
            Descriptive counts and ST-DBSCAN memberships can support
            retrospective examination. They do not measure burned area,
            confirmed wildfire incidents, damage or health effects.
          </p>
        </Panel>
      </div>
      <Panel title="Method & reference trail">
        <div className="method-steps">
          {[
            "Preserve original files",
            "Audit provenance",
            "Validate copied data",
            "Apply documented boundary",
            "Import research artifacts",
            "Explore with limitations",
          ].map((s, i) => (
            <div key={s}>
              <span>0{i + 1}</span>
              <b>{s}</b>
            </div>
          ))}
        </div>
        <div className="reference-links">
          <a
            href="https://firms.modaps.eosdis.nasa.gov/"
            target="_blank"
            rel="noreferrer"
          >
            NASA FIRMS <ExternalLink size={14} />
          </a>
          <a
            href="https://www.earthdata.nasa.gov/data/tools/firms"
            target="_blank"
            rel="noreferrer"
          >
            NASA Earthdata documentation <ExternalLink size={14} />
          </a>
          <a href="https://www.big.go.id/" target="_blank" rel="noreferrer">
            Badan Informasi Geospasial <ExternalLink size={14} />
          </a>
        </div>
        <p className="caption">
          This independent educational project is not an official NASA or
          university service. See Data transparency for the current imported
          snapshot, actual method artifacts and update time.
        </p>
      </Panel>
    </>
  );
}
export default function Dashboard({ view = "overview" }: { view?: View }) {
  const [refresh, setRefresh] = useState(0);
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [query, setQuery] = useState("");
  const [exportError, setExportError] = useState("");
  useEffect(() => {
    const timer = setInterval(() => setRefresh((v) => v + 1), 30000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    const timer = setTimeout(
      () =>
        setQuery(
          new URLSearchParams(
            Object.entries(filters).filter(([, v]) => v),
          ).toString(),
        ),
      250,
    );
    return () => clearTimeout(timer);
  }, [filters]);
  const status = useData<Meta | { connected: false }>("/api/data", refresh);
  const meta = status.data?.connected ? status.data : null;
  const st = useData<Stats>(
    meta ? `/api/data?kind=stats&${query}` : null,
    refresh,
  );
  const rows = useData<{ rows: Row[] }>(
    view === "explorer" && meta ? `/api/data?kind=observations&${query}` : null,
    refresh,
  );
  const connected = !!meta;
  const data = st.data;
  const has = connected && data && Number(data.kpi.detections) > 0;
  async function exportCSV() {
    setExportError("");
    try {
      const r = await fetch(`/api/data?kind=export&${query}`);
      if (!r.ok) throw Error((await r.json()).error);
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "sumafire-observations.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setExportError(e instanceof Error ? e.message : "Export failed");
    }
  }
  const chart = (node: React.ReactNode) =>
    st.loading && !data ? (
      <Loading />
    ) : has ? (
      node
    ) : (
      <Empty
        compact
        title={connected ? "No matching observations" : "Dataset not connected"}
        text={
          connected
            ? "Adjust the filters to explore retained observations."
            : "Connect observations to reveal the historical record."
        }
      />
    );
  return (
    <MotionConfig reducedMotion="user">
      <div
        className={`app ${collapsed ? "collapsed" : ""} ${mobile ? "nav-open" : ""}`}
      >
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        {mobile && (
          <button
            className="nav-scrim"
            aria-label="Close navigation"
            onClick={() => setMobile(false)}
          />
        )}
        <aside className="sidebar">
          <Link
            href="/"
            className="brand"
            aria-label="Sumafire Insight overview"
          >
            <span className="brand-mark">
              <ScanLine size={23} />
            </span>
            <span>
              SUMAFIRE<small>INSIGHT</small>
            </span>
          </Link>
          <button
            className="mobile-close"
            aria-label="Close menu"
            onClick={() => setMobile(false)}
          >
            <X size={19} />
          </button>
          <div className="nav-label">WORKSPACE</div>
          <nav aria-label="Main navigation">
            {pages.map(({ id, title, icon: Icon }, i) => (
              <div key={id}>
                {i === 5 && (
                  <div className="nav-label research-label">RESEARCH</div>
                )}
                <Tip label={title}>
                  <Link
                    href={id === "overview" ? "/" : "/" + id}
                    aria-current={view === id ? "page" : undefined}
                    onClick={() => setMobile(false)}
                  >
                    <Icon size={18} />
                    <span>{title}</span>
                    {view === id && <i />}
                  </Link>
                </Tip>
              </div>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="source-label">
              <Orbit size={17} />
              <span>
                NASA FIRMS<small>MODIS observation data</small>
              </span>
            </div>
            <div className="profile">
              <img 
              src="https://media.discordapp.net/attachments/787014823737032716/1568161309994778794/avatar.JPEG?ex=6aeecf87&is=6aed7e07&hm=9304f7a26fe3aef63b33e8feb0f712974b5752876b94b776b55777209ce4467a&=&format=webp&width=1024&height=1024" 
              alt="Muhammad Aziz" 
              className="avatar-img" 
              />
              <div>
                <b>Muhammad Aziz</b>
                <small>Independent researcher</small>
              </div>
            </div>
            <button
              className="collapse-btn"
              onClick={() => setCollapsed(!collapsed)}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? (
                <ChevronRight size={17} />
              ) : (
                <>
                  <ChevronLeft size={17} />
                  <span>Collapse sidebar</span>
                </>
              )}
            </button>
          </div>
        </aside>
        <div className="workspace">
          <header className="topbar">
            <div>
              <button
                className="mobile-menu"
                aria-label="Open navigation"
                onClick={() => setMobile(true)}
              >
                <Menu size={21} />
              </button>
              <span className="breadcrumb">
                Workspace <ChevronRight size={12} />{" "}
                <b>{pages.find((p) => p.id === view)?.title}</b>
              </span>
            </div>
            <div className="topbar-actions">
              <span className={`dataset-badge ${connected ? "connected" : ""}`}>
                <i />
                {connected ? "Snapshot connected" : "Dataset not connected"}
              </span>
              <Tip label="Refresh imported snapshot">
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Refresh data"
                  onClick={() => setRefresh((v) => v + 1)}
                >
                  <RefreshCw size={16} />
                </Button>
              </Tip>
              <span className="header-avatar">AS</span>
            </div>
          </header>
          <main id="main" tabIndex={-1}>
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22 }}
            >
              <div className="page-heading">
                <div>
                  <span className="eyebrow">
                    SUMATRA · INDONESIA / RESEARCH WORKSPACE
                  </span>
                  <h1>
                    {view === "overview"
                      ? "Research overview"
                      : pages.find((p) => p.id === view)?.title}
                  </h1>
                  <p>{subtitles[view]}</p>
                </div>
                <div className="page-actions">
                  <ImportHelp />
                  {connected && (
                    <Button variant="outline" size="sm" onClick={exportCSV}>
                      <ArrowDownToLine size={14} />
                      Export CSV
                    </Button>
                  )}
                </div>
              </div>
              {status.error && <ErrorBox message={status.error} />}{" "}
              {exportError && <ErrorBox message={exportError} />}{" "}
              {status.loading && !status.data && <Loading />}
              {["overview", "explorer", "analytics", "clusters"].includes(
                view,
              ) && (
                <FilterBar filters={filters} set={setFilters} meta={meta} />
              )}{" "}
              {st.error &&
                ["overview", "explorer", "analytics", "clusters"].includes(
                  view,
                ) && <ErrorBox message={st.error} />}
              {view === "overview" && (
                <>
                  <div className="metric-grid">
                    <Metric
                      label="Hotspot detections"
                      value={connected ? num(data?.kpi.detections) : "—"}
                      note="Satellite-detected thermal anomalies"
                      icon={ScanLine}
                    />
                    <Metric
                      label="Observation period"
                      value={
                        connected && data?.kpi.first_date
                          ? `${day(data.kpi.first_date).slice(0, 4)}—${day(data.kpi.last_date).slice(0, 4)}`
                          : "—"
                      }
                      note={
                        connected
                          ? `${day(data?.kpi.first_date)} to ${day(data?.kpi.last_date)} · UTC`
                          : "Awaiting imported observations"
                      }
                      icon={CalendarDays}
                    />
                    <Metric
                      label="Represented regions"
                      value={
                        meta?.region_verified ? num(data?.kpi.regions) : "—"
                      }
                      note={
                        meta?.region_verified
                          ? "Documented administrative boundary"
                          : "Requires a verified boundary"
                      }
                      icon={MapPin}
                    />
                    <Metric
                      label="Data freshness"
                      value={meta ? day(meta.imported_at) : "Not connected"}
                      note="Manual snapshot · no live NASA feed"
                      icon={Activity}
                    />
                  </div>
                  <div className="overview-grid">
                    <Panel
                      title="Hotspot geography"
                      sub="Mainland Sumatra · geographic context"
                      action={
                        <Link className="text-link" href="/explorer">
                          Open explorer <ArrowRight size={14} />
                        </Link>
                      }
                    >
                      <HotspotMap
                        connected={connected}
                        query={query}
                        refresh={refresh}
                      />
                    </Panel>
                    <Panel
                      title="Annual distribution"
                      sub="Detections by observation year"
                      action={<span className="chip">2015–2026 scope</span>}
                    >
                      {chart(<Trend data={data?.annual || []} annual />)}
                      <p className="caption">
                        Counts describe detections. Partial years and processing
                        versions require separate interpretation.
                      </p>
                    </Panel>
                  </div>
                  <div className="overview-bottom">
                    <Panel
                      title="Monthly activity"
                      sub="Observed detections over time"
                    >
                      {chart(<Trend data={data?.monthly || []} />)}
                    </Panel>
                    <Panel
                      title="Top regions"
                      sub="Ranked within the active filter"
                    >
                      {chart(<Bars data={(data?.regions || []).slice(0, 5)} />)}
                    </Panel>
                    <Panel
                      title="Satellite observations"
                      sub="Different overpass times and coverage"
                    >
                      {chart(<Bars data={data?.satellites || []} />)}
                      <div className="mini-note">
                        <Orbit size={16} /> Terra and Aqua are reported
                        separately.
                      </div>
                    </Panel>
                  </div>
                  <div className="integrity-strip">
                    <ShieldCheck size={18} />
                    <div>
                      <b>Built around the evidence.</b>
                      <span>
                        Explore the provenance, exclusions and limits behind
                        this snapshot.
                      </span>
                    </div>
                    <Link href="/transparency">
                      Data transparency <ArrowRight size={15} />
                    </Link>
                  </div>
                </>
              )}
              {view === "explorer" && (
                <>
                  <Panel
                    title="Observation explorer"
                    sub="Map loads a bounded subset or grid aggregates; the raw dataset stays on the server."
                  >
                    <HotspotMap
                      connected={connected}
                      query={query}
                      refresh={refresh}
                      height={560}
                    />
                  </Panel>
                  <Panel
                    title="Observation attributes"
                    sub="First 100 matching records, ordered by acquisition time. Export is limited to 50,000 rows."
                  >
                    {rows.error ? (
                      <ErrorBox message={rows.error} />
                    ) : connected && rows.data ? (
                      <Table
                        rows={rows.data.rows}
                        columns={[
                          ["observation_id", "Observation ID"],
                          ["date", "UTC date"],
                          ["region", "Region"],
                          ["satellite", "Satellite"],
                          ["confidence", "Confidence /100"],
                          ["frp", "FRP (MW)"],
                          ["version", "Version"],
                        ]}
                      />
                    ) : (
                      <Empty compact />
                    )}
                  </Panel>
                </>
              )}
              {view === "analytics" && (
                <>
                  <div className="two-col">
                    <Panel
                      title="Annual trend"
                      sub="Detections; year completeness may vary"
                    >
                      {chart(<Trend data={data?.annual || []} annual />)}
                    </Panel>
                    <Panel
                      title="Monthly trend"
                      sub="Retained observed dates only"
                    >
                      {chart(<Trend data={data?.monthly || []} />)}
                    </Panel>
                  </div>
                  <Panel
                    title="Seasonal pattern · month by year"
                    sub="Numbers are detections. A dash means no retained records, not verified absence of fire."
                  >
                    {chart(<Heatmap data={data?.heatmap || []} />)}
                  </Panel>
                  {meta ? (
                    <Comparison meta={meta} query={query} refresh={refresh} />
                  ) : (
                    <Panel title="Compare years">
                      <Empty
                        compact
                        text="Connect data to compare equivalent calendar windows."
                      />
                    </Panel>
                  )}
                  <div className="two-col">
                    <Panel
                      title="FRP distribution"
                      sub="Fire radiative power · MW"
                    >
                      {chart(<Bars data={data?.frp || []} />)}
                    </Panel>
                    <Panel
                      title="Confidence distribution"
                      sub="MODIS confidence · 0–100"
                    >
                      {chart(<Bars data={data?.confidence || []} />)}
                    </Panel>
                    <Panel
                      title="Satellite & time of day"
                      sub="Acquisition characteristics"
                    >
                      {chart(
                        <>
                          <Bars data={data?.satellites || []} />
                          <Bars data={data?.daynight || []} />
                        </>,
                      )}
                    </Panel>
                    <Panel
                      title="Regional comparison"
                      sub="Counts reflect observation opportunity as well as thermal activity."
                    >
                      {chart(<Bars data={data?.regions || []} />)}
                    </Panel>
                  </div>
                </>
              )}
              {view === "clusters" && (
                <Clusters meta={meta} query={query} refresh={refresh} />
              )}
              {view === "predictions" && (
                <Predictions meta={meta} refresh={refresh} />
              )}
              {view === "transparency" && <Transparency meta={meta} />}
              {view === "research" && <Research />}
              <footer>
                <p>
                  This dashboard visualizes satellite-detected thermal anomalies
                  for research and educational purposes. A hotspot detection
                  does not necessarily represent a confirmed wildfire.
                </p>
                <span>
                  SUMAFIRE INSIGHT <i />{" "}
                  {meta
                    ? `Snapshot imported ${day(meta.imported_at)}`
                    : "Independent research dashboard"}
                </span>
              </footer>
            </motion.div>
          </main>
        </div>
      </div>
    </MotionConfig>
  );
}
