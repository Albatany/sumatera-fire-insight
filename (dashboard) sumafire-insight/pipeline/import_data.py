"""Independent, auditable dashboard adapter. Never executes research code."""

from __future__ import annotations
import argparse, csv, hashlib, io, json, os, shutil, sys, time, uuid, zipfile
from datetime import datetime, timezone
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from shapely import STRtree, points
from shapely.geometry import shape, mapping

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["latitude", "longitude", "acq_date", "acq_time"]
OPTIONAL = [
    "brightness",
    "scan",
    "track",
    "confidence",
    "frp",
    "bright_t31",
    "type",
    "satellite",
    "instrument",
    "version",
    "daynight",
    "row_id",
    "province",
]
NUMERIC = [
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "confidence",
    "frp",
    "bright_t31",
    "type",
]


class ImportFailure(ValueError):
    pass


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def resolve(p):
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def config(p):
    c = read(p)
    for k, v in [
        ("mapping", {}),
        ("source_metadata", {}),
        ("version_evidence", {}),
        ("duplicate_policy", "error"),
    ]:
        c.setdefault(k, v)
    if c["duplicate_policy"] not in ["error", "retain", "keep_first"]:
        raise ImportFailure("Invalid duplicate policy")
    t = pd.Timestamp(c["cutoff_utc"])
    if t.tzinfo is None:
        raise ImportFailure("Cutoff requires explicit UTC timezone")
    c["cutoff_utc"] = t.tz_convert("UTC").isoformat()
    return c


def sources(p):
    p = resolve(p)
    for f in sorted(p.rglob("*")) if p.is_dir() else [p]:
        if not f.is_file():
            continue
        if f.suffix.lower() == ".csv":
            yield f.name, f.read_bytes()
        elif f.suffix.lower() == ".zip":
            with zipfile.ZipFile(f) as z:
                for e in sorted(z.infolist(), key=lambda x: x.filename):
                    if e.filename.lower().endswith(".csv") and not e.is_dir():
                        if e.file_size > 1024**3:
                            raise ImportFailure("ZIP member exceeds 1 GiB")
                        yield f.name + "::" + e.filename, z.read(e)


def boundaries(c):
    if not c.get("boundary"):
        if not c.get("allow_unbounded", False):
            raise ImportFailure(
                "Supply valid WGS84 polygons or explicitly choose allow_unbounded=true"
            )
        return None, None, None
    p = resolve(c["boundary"])
    g = read(p)
    key = c.get("region_property", "name")
    if g.get("type") != "FeatureCollection" or not g.get("features"):
        raise ImportFailure("GeoJSON FeatureCollection required")
    crs = g.get("crs", {}).get("properties", {}).get("name", "")
    if crs and "4326" not in crs and "CRS84" not in crs:
        raise ImportFailure("Boundary CRS must be WGS84")
    geometries = []
    names = []
    for f in g["features"]:
        geom = shape(f["geometry"])
        name = f.get("properties", {}).get(key)
        if (
            geom.is_empty
            or not geom.is_valid
            or geom.geom_type not in ["Polygon", "MultiPolygon"]
            or not name
        ):
            raise ImportFailure(
                "Invalid boundary geometry or missing region name; no automatic repair"
            )
        a, b, x, y = geom.bounds
        if a < -180 or x > 180 or b < -90 or y > 90:
            raise ImportFailure("Boundary outside WGS84 coordinate range")
        geometries.append(geom)
        names.append(str(name))
    return (
        STRtree(geometries),
        names,
        {
            "sha256": sha(p),
            "source": c.get("boundary_source", "Not supplied"),
            "geometry": g,
            "region_property": key,
        },
    )


def validate(c, data, allow_test=False):
    tree, names, boundary = boundaries(c)
    frames = []
    files = []
    schema_errors = []
    missing = {}
    if c.get("test_fixture") and not allow_test:
        raise ImportFailure("TEST_FIXTURE_NOT_RESEARCH_DATA blocked")
    for name, content in sources(c["input"]):
        if b"TEST_FIXTURE_NOT_RESEARCH_DATA" in content[:4096] and not allow_test:
            raise ImportFailure("TEST_FIXTURE_NOT_RESEARCH_DATA blocked")
        headers = next(
            csv.reader(io.StringIO(content.decode("utf-8-sig", errors="replace"))), []
        )
        if len(headers) != len(set(headers)):
            schema_errors.append({"file": name, "error": "Duplicate column headers"})
            continue
        try:
            d = pd.read_csv(
                io.BytesIO(content),
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
                on_bad_lines="error",
            )
        except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as e:
            schema_errors.append({"file": name, "error": str(e)})
            continue
        columns = list(d.columns)
        for target, source in c["mapping"].items():
            if source in d and source != target:
                if target in d:
                    raise ImportFailure("Ambiguous mapping: " + target)
                d = d.rename(columns={source: target})
        entry = {
            "file": name,
            "rows": len(d),
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "columns": columns,
            "download_metadata": c["source_metadata"].get(name, {}),
        }
        files.append(entry)
        if not set(REQUIRED) <= set(d):
            schema_errors.append(
                {"file": name, "missing_columns": sorted(set(REQUIRED) - set(d))}
            )
            continue
        for k in OPTIONAL:
            if k not in d:
                d[k] = ""
        for k in REQUIRED + OPTIONAL:
            d[k] = d[k].str.strip()
        d["source_file"] = name
        d["source_row"] = np.arange(2, len(d) + 2)
        d["observation_id"] = d.row_id.where(
            d.row_id.ne(""),
            pd.Series(
                [entry["sha256"][:16] + ":L" + str(i) for i in range(2, len(d) + 2)]
            ),
        )
        d["issues"] = ""

        def bad(mask, reason):
            d.loc[mask, "issues"] += reason + ";"

        time_text = d.acq_time.str.replace(r"\.0$", "", regex=True)
        t = pd.to_datetime(
            d.acq_date + " " + time_text.str.zfill(4),
            format="%Y-%m-%d %H%M",
            errors="coerce",
            utc=True,
        )
        bad(
            ~d.acq_date.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
            | ~time_text.str.fullmatch(r"\d{1,4}")
            | t.isna(),
            "invalid_datetime",
        )
        d["observed_at"] = t
        for col in NUMERIC:
            val = pd.to_numeric(d[col], errors="coerce")
            bad(d[col].ne("") & (val.isna() | ~np.isfinite(val)), "invalid_" + col)
            if col in ["latitude", "longitude"]:
                bad(d[col].eq(""), "missing_" + col)
            d[col] = val
            missing[col] = missing.get(col, 0) + int(val.isna().sum())
        bad(
            ~d.latitude.between(-90, 90) | ~d.longitude.between(-180, 180),
            "invalid_coordinates",
        )
        bad(d.confidence.notna() & ~d.confidence.between(0, 100), "invalid_confidence")
        bad(d.frp.notna() & (d.frp < 0), "invalid_frp")
        bad(d["type"].notna() & ~d["type"].isin([0, 1, 2, 3]), "invalid_type")
        bad(
            d.instrument.ne("") & d.instrument.str.upper().ne("MODIS"),
            "invalid_instrument",
        )
        bad(d.daynight.ne("") & ~d.daynight.isin(["D", "N"]), "invalid_daynight")
        bad(
            d.satellite.ne("") & ~d.satellite.isin(["Terra", "Aqua"]),
            "invalid_satellite",
        )
        for col in ["version", "satellite", "instrument", "daynight"]:
            d[col] = d[col].replace("", "Unspecified")
        d["region"] = "Unassigned"
        d["region_verified"] = False
        valid = d.issues.eq("")
        if tree is not None and valid.any():
            indexes = d.index[valid].to_numpy()
            a, b = tree.query(
                points(
                    d.loc[valid, "longitude"].to_numpy(),
                    d.loc[valid, "latitude"].to_numpy(),
                ),
                predicate="intersects",
            )
            counts = np.bincount(a, minlength=len(indexes))
            d.loc[indexes[counts == 0], "issues"] += "outside_boundary;"
            d.loc[indexes[counts > 1], "issues"] += "ambiguous_boundary;"
            unique = counts[a] == 1
            good_indexes = indexes[a[unique]]
            d.loc[good_indexes, "region"] = [names[i] for i in b[unique]]
            d.loc[good_indexes, "region_verified"] = True
        bad(t > pd.Timestamp(c["cutoff_utc"]), "after_cutoff")
        entry.update(
            {
                "versions": d.version.value_counts().to_dict(),
                "start": t.min().isoformat() if t.notna().any() else None,
                "end": t.max().isoformat() if t.notna().any() else None,
            }
        )
        frames.append(d)
    if schema_errors:
        write(
            data / "manifests/latest_validation.json",
            {"status": "BLOCKED_SCHEMA", "files": files, "errors": schema_errors},
        )
        raise ImportFailure(
            "Schema errors: inspect latest_validation.json; active snapshot unchanged"
        )
    if not frames:
        raise ImportFailure("No CSV files available in the configured input")
    d = pd.concat(frames, ignore_index=True)
    dup = pd.Series(False, index=d.index)
    valid = d.issues.eq("")
    dup.loc[valid] = d.loc[valid].duplicated(
        ["latitude", "longitude", "observed_at", "satellite", "instrument", "version"]
    )
    n_dups = int(dup.sum())
    if c["duplicate_policy"] == "keep_first":
        d.loc[dup, "issues"] += "duplicate_key;"
    errors = []
    if d.observation_id.duplicated().any():
        errors.append("Observation IDs are not unique")
    if n_dups and c["duplicate_policy"] == "error":
        errors.append("Duplicate acquisition keys require an explicit policy")
    rejected = d.issues.str.contains("invalid_|missing_|ambiguous_", regex=True)
    filtered = d.issues.ne("") & ~rejected
    keep = d.issues.eq("")
    report = {
        "status": "BLOCKED" if errors else "VALIDATED",
        "raw_rows": len(d),
        "retained_rows": int(keep.sum()),
        "rejected_rows": int(rejected.sum()),
        "filtered_rows": int(filtered.sum()),
        "duplicate_keys": n_dups,
        "duplicate_policy": c["duplicate_policy"],
        "missing_values": missing,
        "issue_counts": d.loc[~keep, "issues"]
        .str.split(";")
        .explode()
        .value_counts()
        .drop("", errors="ignore")
        .to_dict(),
        "files": files,
        "errors": errors,
    }
    assert (
        len(d)
        == report["retained_rows"] + report["rejected_rows"] + report["filtered_rows"]
    )
    write(data / "manifests/latest_validation.json", report)
    d.loc[~keep, ["observation_id", "source_file", "source_row", "issues"]].to_csv(
        data / "manifests/row_issues.csv", index=False
    )
    if errors:
        raise ImportFailure("; ".join(errors))
    if not keep.any():
        raise ImportFailure("No retained rows; active snapshot unchanged")
    return d.loc[keep].copy(), report, boundary


def artifacts(c, d, con):
    out = {"clustering": None, "prediction": None}
    for kind in ["clustering", "prediction"]:
        spec = c.get("artifacts", {}).get(kind)
        if not spec:
            continue
        p = resolve(spec["file"])
        mp = resolve(spec["metadata"])
        meta = read(mp)
        x = pd.read_csv(p, dtype=str, keep_default_na=False).rename(
            columns=spec.get("rename", {})
        )
        if not meta.get("limitations"):
            raise ImportFailure("Artifact limitations are required")
        if kind == "clustering":
            cols = ["observation_id", "cluster_id", "point_role"]
            if (
                not set(cols) <= set(x)
                or not meta.get("algorithm")
                or not meta.get("parameters")
            ):
                raise ImportFailure("Cluster columns/metadata missing")
            x = x[cols]
            if x.observation_id.duplicated().any() or not set(x.observation_id) <= set(
                d.observation_id
            ):
                raise ImportFailure("Cluster membership join is not one-to-one")
            if not x.point_role.isin(["core", "border", "noise"]).all():
                raise ImportFailure("Invalid point role")
            if (
                (x.point_role == "noise")
                != (x.cluster_id == meta.get("noise_label", "NOISE"))
            ).any():
                raise ImportFailure("Inconsistent noise label")
            table = "cluster_members"
        else:
            if (
                meta.get("validated") is not True
                or not meta.get("validation_evidence")
                or not meta.get("model_name")
            ):
                raise ImportFailure("Prediction validation evidence missing")
            cols = [
                "prediction_id",
                "region",
                "issue_time",
                "target_time",
                "predicted_class",
                "split",
            ]
            if not set(cols) <= set(x):
                raise ImportFailure("Prediction columns missing")
            if x.prediction_id.duplicated().any():
                raise ImportFailure("Duplicate prediction IDs")
            for col in ["issue_time", "target_time"]:
                if not x[col].str.contains(r"(?:Z|[+-]\d\d:\d\d)$", regex=True).all():
                    raise ImportFailure("Prediction timestamps need explicit timezone")
                x[col] = pd.to_datetime(x[col], utc=True, errors="coerce")
            if (
                x[["issue_time", "target_time"]].isna().any().any()
                or (x.issue_time >= x.target_time).any()
            ):
                raise ImportFailure("Invalid forecast order")
            if (
                not x.predicted_class.isin(["0", "1"]).all()
                or not x.split.isin(
                    ["train", "validation", "test_2025", "case_2026"]
                ).all()
            ):
                raise ImportFailure("Invalid class/split")
            for col in ["probability", "actual_class"]:
                if col not in x:
                    x[col] = ""
                x[col] = pd.to_numeric(x[col].replace("", np.nan), errors="raise")
            if (x.probability.notna() & ~x.probability.between(0, 1)).any() or (
                x.actual_class.notna() & ~x.actual_class.isin([0, 1])
            ).any():
                raise ImportFailure("Invalid probability/actual class")
            if meta.get("evaluation") and not meta.get("evaluation_source"):
                raise ImportFailure("Metrics need a source")
            table = "predictions"
        con.register("artifact", x)
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM artifact")
        con.unregister("artifact")
        out[kind] = {
            **meta,
            "rows": len(x),
            "sha256": sha(p),
            "metadata_sha256": sha(mp),
        }
    return out


def activate(data, sid):
    active = data / "active.json"
    if active.exists():
        shutil.copy2(active, data / "previous.json")
    tmp = data / ".active.tmp"
    write(tmp, {"snapshot": sid})
    os.replace(tmp, active)


def verify(stage):
    for n, h in read(stage / "checksums.json").items():
        if sha(stage / n) != h:
            raise ImportFailure("Checksum mismatch: " + n)
    m = read(stage / "metadata.json")
    con = duckdb.connect(str(stage / "observations.duckdb"), read_only=True)
    n = con.execute("SELECT count(*) FROM observations").fetchone()[0]
    for table in ["daily", "monthly", "annual"]:
        if con.execute(f"SELECT sum(detections) FROM {table}").fetchone()[0] != n:
            raise ImportFailure("Aggregation total mismatch")
    con.close()
    if n != m["retained_rows"]:
        raise ImportFailure("Metadata total mismatch")
    return {"status": "PASS", "snapshot": stage.name, "retained_rows": n}


def build(c, data, allow_test=False):
    d, report, bound = validate(c, data, allow_test)
    if c.get("expected_rows") is not None and len(d) != c["expected_rows"]:
        raise ImportFailure("Research count mismatch; active snapshot unchanged")
    sid = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    stage = data / "processed" / sid
    stage.mkdir(parents=True)
    d["date"] = d.observed_at.dt.strftime("%Y-%m-%d")
    d["year"] = d.observed_at.dt.year
    d["month"] = d.observed_at.dt.month
    cols = [
        "observation_id",
        "source_file",
        "source_row",
        "observed_at",
        "date",
        "year",
        "month",
        "latitude",
        "longitude",
        "region",
        "region_verified",
        "version",
        "satellite",
        "instrument",
        "confidence",
        "frp",
        "brightness",
        "bright_t31",
        "scan",
        "track",
        "type",
        "daynight",
    ]
    con = duckdb.connect(str(stage / "observations.duckdb"))
    try:
        con.register("input", d[cols])
        con.execute("CREATE TABLE observations AS SELECT * FROM input")
        con.unregister("input")
        con.execute("CREATE INDEX obs_id ON observations(observation_id)")
        con.execute("CREATE INDEX obs_date ON observations(date)")
        for name, group in [
            ("daily", "date"),
            ("monthly", "substr(date,1,7)"),
            ("annual", "year"),
        ]:
            con.execute(
                f"CREATE TABLE {name} AS SELECT {group} period,region,satellite,version,count(*) detections FROM observations GROUP BY ALL"
            )
            con.execute(
                f"COPY {name} TO '{(stage/(name+'.parquet')).as_posix()}' (FORMAT PARQUET)"
            )
        con.execute(
            f"COPY observations TO '{(stage/'observations.parquet').as_posix()}' (FORMAT PARQUET)"
        )
        research = artifacts(c, d, con)
    finally:
        con.close()
    if bound:
        key = bound["region_property"]
        geo = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": f["properties"][key]},
                    "geometry": mapping(
                        shape(f["geometry"]).simplify(0.004, preserve_topology=True)
                    ),
                }
                for f in bound["geometry"]["features"]
            ],
        }
        write(stage / "boundary.json", geo)
    versions = [
        {
            "value": str(v),
            "rows": int(n),
            "status": c["version_evidence"].get(v, {}).get("status", "Unverified"),
            "evidence": c["version_evidence"].get(v, {}).get("evidence"),
        }
        for v, n in d.version.value_counts().items()
    ]
    m = {
        "schema_version": 1,
        "connected": True,
        "snapshot": sid,
        "name": c.get("name", "NASA FIRMS import"),
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "observation_start": d.observed_at.min().isoformat(),
        "observation_end": d.observed_at.max().isoformat(),
        "cutoff_utc": c["cutoff_utc"],
        "input_rows": report["raw_rows"],
        "retained_rows": len(d),
        "rejected_rows": report["rejected_rows"],
        "filtered_rows": report["filtered_rows"],
        "file_count": len(report["files"]),
        "regions": sorted(d.region.unique().tolist()),
        "years": sorted(d.year.unique().tolist()),
        "region_verified": bool(d.region_verified.all()),
        "versions": versions,
        "satellites": sorted(d.satellite.unique().tolist()),
        "downloaded_at": c.get("downloaded_at"),
        "source_url": c.get(
            "source_url", "https://firms.modaps.eosdis.nasa.gov/download/"
        ),
        "scope": c.get("scope", "Not documented"),
        "boundary": {k: v for k, v in (bound or {}).items() if k != "geometry"},
        "provisional_years": c.get("provisional_years", []),
        "limitations": c.get("limitations", []),
        "original_research_audit": c.get("original_research_audit"),
        "artifacts": research,
        "import_report": report,
        "test_fixture": bool(c.get("test_fixture")),
        "refresh_mode": "Imported snapshots; browser checks every 30 seconds",
    }
    write(stage / "metadata.json", m)
    write(stage / "config.json", c)
    write(
        stage / "checksums.json",
        {f.name: sha(f) for f in stage.iterdir() if f.is_file()},
    )
    verify(stage)
    activate(data, sid)
    return m


def connect(source, data):
    source = Path(source).resolve()
    dest = ROOT / "incoming/research-copy"
    dest.mkdir(parents=True, exist_ok=True)
    needed = [
        "hasil/data_sesudah_diolah.csv",
        "hasil/sumatera_daratan_utama.geojson",
        "hasil/audit_paket_final.json",
        "clustering/hasil_st_dbscan.csv",
        "clustering/ringkasan_eksperimen.json",
        "clustering/protokol_sebelum_eksperimen.json",
    ]
    for name in needed:
        if not (source / name).is_file():
            raise ImportFailure(
                "Extract the original research package first; missing " + name
            )
    for name in needed:
        shutil.copy2(source / name, dest / Path(name).name)
    a = read(source / "hasil/audit_paket_final.json")
    protocol = read(source / "clustering/protokol_sebelum_eksperimen.json")
    spatial, temporal, minimum = protocol["primary"]
    write(
        dest / "cluster_metadata.json",
        {
            "algorithm": "ST-DBSCAN two-threshold variant",
            "parameters": {
                "spatial_km": spatial,
                "temporal_hours": temporal,
                "minimum_samples": minimum,
                "strata": protocol["partition"],
            },
            "noise_label": "NOISE",
            "limitations": [
                "Clusters group thermal detections, not confirmed wildfire incidents.",
                "Density chaining and year/version partitions affect interpretation.",
            ],
            "reference_summary": read(source / "clustering/ringkasan_eksperimen.json"),
        },
    )
    c = config(ROOT / "config/dataset.json")
    c.update(
        {
            "name": "Sumatra MODIS research snapshot 2015–2026",
            "input": str(dest / "data_sesudah_diolah.csv"),
            "boundary": str(dest / "sumatera_daratan_utama.geojson"),
            "region_property": "WADMPR",
            "boundary_source": "BIG STIG through the original research package",
            "expected_rows": a["retained_detections_mainland_sumatra"],
            "scope": "Largest mainland polygon of eight Sumatra provinces; offshore islands excluded",
            "provisional_years": [2026],
            "original_research_audit": {
                "raw_files": a["raw_csv_count"],
                "raw_rows": a["raw_rows"],
                "retained_rows": a["retained_detections_mainland_sumatra"],
                "evidence": "hasil/audit_paket_final.json",
                "sha256": sha(source / "hasil/audit_paket_final.json"),
            },
            "version_evidence": {
                "6.03": {
                    "status": "Documented C6 standard code; export provenance unresolved",
                    "evidence": "Original NASA GIBS code mapping; M-C61 filename conflict and export metadata remain unresolved",
                },
                "61.03": {
                    "status": "Unresolved",
                    "evidence": "Literal code unresolved in original audit",
                },
                "6.1NRT": {
                    "status": "NRT",
                    "evidence": "Documented literal code in original NASA audit",
                },
            },
            "artifacts": {
                "clustering": {
                    "file": str(dest / "hasil_st_dbscan.csv"),
                    "metadata": str(dest / "cluster_metadata.json"),
                    "rename": {"row_id": "observation_id"},
                }
            },
            "limitations": [
                "The dashboard input is already processed data; original raw counts are shown separately.",
                "Observation coverage and first availability are not verified. Classification was not fitted.",
                "2026 is partial/provisional; missing type in NRT is not filled.",
            ],
        }
    )
    write(ROOT / "config/research.local.json", c)
    return build(c, data)


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "command",
        choices=[
            "validate",
            "build",
            "verify",
            "rollback",
            "reset",
            "watch",
            "connect-research",
            "install-snapshot",
            "test",
        ],
    )
    p.add_argument("source", nargs="?")
    p.add_argument("--config", default=str(ROOT / "config/dataset.json"))
    p.add_argument(
        "--data-dir", default=os.environ.get("SUMAFIRE_DATA_DIR", str(ROOT / "data"))
    )
    p.add_argument("--allow-test-fixtures", action="store_true")
    a = p.parse_args()
    data = resolve(a.data_dir)
    try:
        if a.command == "test":
            import pytest

            return pytest.main([str(ROOT / "tests"), "-q"])
        if a.command == "connect-research":
            if not a.source:
                raise ImportFailure(
                    "Pass the extracted original research package directory"
                )
            out = connect(a.source, data)
        elif a.command == "install-snapshot":
            if not a.source:
                raise ImportFailure("Pass a prepared snapshot directory")
            folder = Path(a.source).resolve()
            sid = read(folder / "active.json")["snapshot"]
            if not sid.replace("-", "").replace("_", "").isalnum():
                raise ImportFailure("Invalid snapshot identifier")
            stage = folder / "processed" / sid
            verify(stage)
            if read(stage / "metadata.json").get("test_fixture"):
                raise ImportFailure("Test fixtures cannot be installed")
            target = data / "processed" / sid
            if not target.exists():
                shutil.copytree(stage, target)
            out = verify(target)
            activate(data, sid)
        elif a.command == "verify":
            out = verify(data / "processed" / read(data / "active.json")["snapshot"])
        elif a.command == "rollback":
            sid = read(data / "previous.json")["snapshot"]
            out = verify(data / "processed" / sid)
            activate(data, sid)
        elif a.command == "reset":
            if (data / "active.json").exists():
                os.replace(data / "active.json", data / "previous.json")
            out = {"status": "Disconnected; snapshots retained"}
        else:
            c = config(a.config)
            if a.command == "validate":
                _, out, _ = validate(c, data, a.allow_test_fixtures)
            elif a.command == "build":
                out = build(c, data, a.allow_test_fixtures)
            else:
                last = None
                while True:
                    current = [
                        (name, hashlib.sha256(content).hexdigest())
                        for name, content in sources(c["input"])
                    ]
                    if current != last:
                        try:
                            print(
                                build(c, data, a.allow_test_fixtures)["snapshot"],
                                flush=True,
                            )
                        except Exception as e:
                            print(
                                "Import blocked; previous snapshot retained: " + str(e),
                                flush=True,
                            )
                        last = current
                    time.sleep(5)
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
        return 0
    except (ImportFailure, FileNotFoundError, ValueError, duckdb.Error) as e:
        print(
            json.dumps(
                {
                    "error": str(e),
                    "active_snapshot": "Preserved unless explicitly reset",
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
