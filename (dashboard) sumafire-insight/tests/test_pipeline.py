"""TEST_FIXTURE_NOT_RESEARCH_DATA: isolated synthetic adapter tests."""

import importlib.util, zipfile
from pathlib import Path
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "pipeline", Path(__file__).resolve().parents[1] / "pipeline/import_data.py"
)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


@pytest.fixture
def setup(tmp_path):
    raw = tmp_path / "input"
    raw.mkdir()
    data = tmp_path / "output"
    row = {
        "latitude": "-1",
        "longitude": "102",
        "acq_date": "2025-01-01",
        "acq_time": "0200",
        "version": "6.03",
        "satellite": "Terra",
        "instrument": "MODIS",
        "confidence": "80",
        "frp": "10",
        "daynight": "D",
    }
    c = {
        "input": str(raw),
        "allow_unbounded": True,
        "cutoff_utc": "2026-10-30T23:59:59+00:00",
        "mapping": {},
        "source_metadata": {},
        "version_evidence": {},
        "duplicate_policy": "error",
        "test_fixture": True,
    }

    def save(rows):
        pd.DataFrame(rows).to_csv(
            raw / "TEST_FIXTURE_NOT_RESEARCH_DATA.csv", index=False
        )

    save([row])
    return c, data, row, save


def test_fixture_blocked(setup):
    c, d, _, _ = setup
    with pytest.raises(p.ImportFailure, match="TEST_FIXTURE"):
        p.build(c, d)


def test_version(setup):
    c, d, _, _ = setup
    x, r, b = p.validate(c, d, True)
    assert x.version.iloc[0] == "6.03" and r["raw_rows"] == 1 and b is None


@pytest.mark.parametrize(
    ("col", "value", "issue"),
    [
        ("latitude", "91", "invalid_coordinates"),
        ("longitude", "text", "invalid_longitude"),
        ("confidence", "101", "invalid_confidence"),
        ("frp", "-1", "invalid_frp"),
        ("acq_date", "2025-02-30", "invalid_datetime"),
        ("acq_time", "2500", "invalid_datetime"),
        ("satellite", "NOAA", "invalid_satellite"),
        ("instrument", "VIIRS", "invalid_instrument"),
        ("daynight", "X", "invalid_daynight"),
        ("type", "7", "invalid_type"),
    ],
)
def test_invalid_record(setup, col, value, issue):
    c, d, row, save = setup
    save([row, {**row, col: value}])
    x, r, _ = p.validate(c, d, True)
    assert len(x) == 1 and r["rejected_rows"] == 1 and issue in r["issue_counts"]


def test_duplicate_policy(setup):
    c, d, row, save = setup
    save([row, row])
    with pytest.raises(p.ImportFailure, match="Duplicate"):
        p.validate(c, d, True)
    c["duplicate_policy"] = "keep_first"
    x, r, _ = p.validate(c, d, True)
    assert len(x) == 1 and r["filtered_rows"] == 1
    c["duplicate_policy"] = "retain"
    x, r, _ = p.validate(c, d, True)
    assert len(x) == 2


def test_invalid_first_not_duplicate(setup):
    c, d, row, save = setup
    save([{**row, "frp": "-1"}, row])
    x, r, _ = p.validate(c, d, True)
    assert len(x) == 1 and r["duplicate_keys"] == 0


def test_cutoff_balance(setup):
    c, d, row, save = setup
    save([row, {**row, "acq_date": "2026-10-31"}])
    x, r, _ = p.validate(c, d, True)
    assert (
        len(x) == 1
        and r["filtered_rows"] == 1
        and sum(r[k] for k in ["retained_rows", "rejected_rows", "filtered_rows"])
        == r["raw_rows"]
    )


def test_optional_missing(setup):
    c, d, row, save = setup
    save([{k: v for k, v in row.items() if k in p.REQUIRED}])
    x, r, _ = p.validate(c, d, True)
    assert len(x) == 1 and pd.isna(x.frp.iloc[0]) and x.version.iloc[0] == "Unspecified"


def test_no_negative_rows(setup):
    c, d, row, save = setup
    save([row, {**row, "acq_date": "2025-01-03"}])
    m = p.build(c, d, True)
    con = p.duckdb.connect(
        str(d / "processed" / m["snapshot"] / "observations.duckdb"), read_only=True
    )
    assert con.execute("SELECT count(*) FROM daily").fetchone()[0] == 2
    con.close()


def test_zip_mapping(setup, tmp_path):
    c, d, row, save = setup
    row["lat"] = row.pop("latitude")
    save([row])
    z = tmp_path / "input.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.write(
            Path(c["input"]) / "TEST_FIXTURE_NOT_RESEARCH_DATA.csv", "nested/test.csv"
        )
    c.update(input=str(z), mapping={"latitude": "lat"})
    x, r, _ = p.validate(c, d, True)
    assert len(x) == 1 and "::nested/test.csv" in r["files"][0]["file"]


def test_boundary_required(setup):
    c, d, _, _ = setup
    c["allow_unbounded"] = False
    with pytest.raises(p.ImportFailure, match="WGS84"):
        p.validate(c, d, True)


def test_spatial_filter(setup, tmp_path):
    c, d, row, save = setup
    geo = tmp_path / "boundary.geojson"
    p.write(
        geo,
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Test region"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[101, -2], [103, -2], [103, 0], [101, 0], [101, -2]]
                        ],
                    },
                }
            ],
        },
    )
    c["boundary"] = str(geo)
    save([row, {**row, "longitude": "105"}])
    x, r, _ = p.validate(c, d, True)
    assert x.region.iloc[0] == "Test region" and r["filtered_rows"] == 1


def test_atomic_hash(setup):
    c, d, row, save = setup
    m = p.build(c, d, True)
    stage = d / "processed" / m["snapshot"]
    assert p.verify(stage)["status"] == "PASS"
    active = (d / "active.json").read_bytes()
    save([{**row, "latitude": "100"}])
    with pytest.raises(p.ImportFailure):
        p.build(c, d, True)
    assert (d / "active.json").read_bytes() == active
    (stage / "annual.parquet").write_bytes(b"corrupt")
    with pytest.raises(p.ImportFailure, match="Checksum"):
        p.verify(stage)


def test_count_gate(setup):
    c, d, _, _ = setup
    c["expected_rows"] = 99
    with pytest.raises(p.ImportFailure, match="count mismatch"):
        p.build(c, d, True)
    assert not (d / "active.json").exists()


def test_cluster_join(setup, tmp_path):
    c, d, _, _ = setup
    mem = tmp_path / "clusters.csv"
    pd.DataFrame(
        [{"observation_id": "unknown", "cluster_id": "c1", "point_role": "core"}]
    ).to_csv(mem, index=False)
    meta = tmp_path / "meta.json"
    p.write(
        meta,
        {
            "algorithm": "TEST",
            "parameters": {"eps": 1},
            "limitations": ["Synthetic test"],
        },
    )
    c["artifacts"] = {"clustering": {"file": str(mem), "metadata": str(meta)}}
    with pytest.raises(p.ImportFailure, match="one-to-one"):
        p.build(c, d, True)


def test_prediction_gate(setup, tmp_path):
    c, d, _, _ = setup
    mem = tmp_path / "pred.csv"
    mem.write_text("prediction_id\np1\n")
    meta = tmp_path / "meta.json"
    p.write(meta, {"limitations": ["Test"], "validated": False})
    c["artifacts"] = {"prediction": {"file": str(mem), "metadata": str(meta)}}
    with pytest.raises(p.ImportFailure, match="validation evidence"):
        p.build(c, d, True)


def test_duplicate_header(setup):
    c, d, _, _ = setup
    (Path(c["input"]) / "TEST_FIXTURE_NOT_RESEARCH_DATA.csv").write_text(
        "latitude,latitude\n1,2\n"
    )
    with pytest.raises(p.ImportFailure, match="Schema"):
        p.validate(c, d, True)


def test_timezone(tmp_path):
    cfg = tmp_path / "config.json"
    p.write(cfg, {"cutoff_utc": "2026-10-30"})
    with pytest.raises(p.ImportFailure, match="timezone"):
        p.config(cfg)
