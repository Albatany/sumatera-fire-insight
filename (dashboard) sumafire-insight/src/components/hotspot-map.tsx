"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import * as maplibre from "maplibre-gl";
import type { FeatureCollection, Geometry } from "geojson";
import { Expand, Minus, Plus, Layers, MapPin, Info } from "lucide-react";
import { useData } from "@/lib/use-data";
import type { MapData, Row } from "@/lib/types";
import { num } from "@/lib/utils";
import { Button } from "./ui/button";
maplibre.setWorkerUrl(
  new URL(
    "maplibre-gl/dist/maplibre-gl-worker.mjs",
    import.meta.url,
  ).toString(),
);
const home: [number, number] = [101.3, -0.6];
const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
function outline(g: Geometry): string {
  const project = (p: number[]) => [
    ((p[0] - 93) / 16) * 900,
    ((8 - p[1]) / 15) * 700,
  ];
  const ring = (r: number[][]) =>
    r.map((p, i) => (i ? "L" : "M") + project(p).join(",")).join(" ") + "Z";
  if (g.type === "Polygon") return g.coordinates.map(ring).join(" ");
  if (g.type === "MultiPolygon")
    return g.coordinates.flatMap((p) => p.map(ring)).join(" ");
  return "";
}
export default function HotspotMap({
  query = "",
  refresh = 0,
  connected = false,
  cluster = "",
  height = 410,
}: {
  query?: string;
  refresh?: number;
  connected?: boolean;
  cluster?: string;
  height?: number;
}) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<maplibre.Map | null>(null);
  const [fallback, setFallback] = useState(false);
  const [ready, setReady] = useState(false);
  const [viewport, setViewport] = useState("bbox=93,-7,109,8&zoom=5");
  const [mode, setMode] = useState("points");
  const [selection, setSelection] = useState<Row | null>(null);
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState([0, 0]);
  const drag = useRef<number[] | null>(null);
  const boundary = useData<FeatureCollection>("/api/boundary", refresh);
  const result = useData<MapData>(
    connected
      ? `/api/data?kind=map&${query}&${viewport}&mode=${mode === "aggregation" ? "aggregation" : "points"}${cluster ? "&cluster=" + encodeURIComponent(cluster) : ""}`
      : null,
    refresh,
  );
  const features = connected ? result.data?.features || empty : empty;
  useEffect(() => {
    if (!host.current) return;
    let instance: maplibre.Map;
    try {
      instance = new maplibre.Map({
        container: host.current,
        center: home,
        zoom: 4.6,
        style: process.env.NEXT_PUBLIC_BASEMAP_STYLE || {
          version: 8,
          sources: {},
          layers: [
            {
              id: "ocean",
              type: "background",
              paint: { "background-color": "#171c22" },
            },
          ],
        },
        attributionControl: { compact: true },
        maxZoom: 13,
        minZoom: 3,
      });
      map.current = instance;
      instance.addControl(
        new maplibre.NavigationControl({ showCompass: false }),
        "top-right",
      );
      instance.on("load", () => setReady(true));
      instance.on("moveend", () => {
        const b = instance.getBounds();
        setViewport(
          `bbox=${Math.max(-180, b.getWest())},${Math.max(-90, b.getSouth())},${Math.min(180, b.getEast())},${Math.min(90, b.getNorth())}&zoom=${instance.getZoom()}`,
        );
      });
      instance.on("click", (e) => {
        if (!instance.getLayer("observations")) return;
        const f = instance.queryRenderedFeatures(e.point, {
          layers: ["observations"],
        })[0];
        if (f) setSelection(f.properties as Row);
      });
    } catch (e) {
      console.warn(
        "MapLibre unavailable; using accessible geographic fallback",
        e,
      );
      queueMicrotask(() => setFallback(true));
    }
    return () => {
      instance?.remove();
      map.current = null;
    };
  }, []);
  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    const geo = boundary.data || empty;
    if (!m.getSource("boundary")) {
      m.addSource("boundary", {
        type: "geojson",
        data: geo,
        attribution:
          "Boundary: BIG STIG • research polygon, simplified for display",
      });
      m.addLayer({
        id: "land",
        type: "fill",
        source: "boundary",
        paint: { "fill-color": "#2b3437", "fill-opacity": 0.9 },
      });
      m.addLayer({
        id: "borders",
        type: "line",
        source: "boundary",
        paint: { "line-color": "#627071", "line-width": 0.8 },
      });
    } else (m.getSource("boundary") as maplibre.GeoJSONSource).setData(geo);
  }, [ready, boundary.data]);
  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    if (!m.getSource("observations")) {
      m.addSource("observations", { type: "geojson", data: features });
      m.addLayer({
        id: "observations",
        source: "observations",
        type: "circle",
        paint: {
          "circle-color": "#e8a264",
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["coalesce", ["get", "detections"], 1],
            1,
            3,
            50,
            6,
            500,
            12,
            5000,
            23,
          ],
          "circle-opacity": 0.7,
          "circle-stroke-color": "#ffe0bd",
          "circle-stroke-width": 0.4,
        },
      });
      m.addLayer({
        id: "density",
        source: "observations",
        type: "heatmap",
        paint: {
          "heatmap-weight": ["coalesce", ["get", "detections"], 1],
          "heatmap-radius": 24,
          "heatmap-opacity": 0.7,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(0,0,0,0)",
            0.2,
            "#625044",
            0.6,
            "#c58356",
            1,
            "#ffdab1",
          ],
        },
      });
    } else
      (m.getSource("observations") as maplibre.GeoJSONSource).setData(features);
    m.setLayoutProperty(
      "observations",
      "visibility",
      mode === "density" ? "none" : "visible",
    );
    m.setLayoutProperty(
      "density",
      "visibility",
      mode === "density" ? "visible" : "none",
    );
  }, [ready, features, mode]);
  const reset = useCallback(() => {
    map.current?.flyTo({
      center: home,
      zoom: 4.6,
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? 0
        : 600,
    });
    setScale(1);
    setPan([0, 0]);
  }, []);
  return (
    <div className="map-shell" style={{ minHeight: height }}>
      <div
        className="map-canvas"
        ref={host}
        aria-label="Interactive Sumatra hotspot map"
      />
      {fallback && (
        <svg
          viewBox="0 0 900 700"
          className="fallback-map"
          role="img"
          aria-label="Sumatra geographic map, reduced rendering mode"
          onPointerDown={(e) => {
            drag.current = [e.clientX - pan[0], e.clientY - pan[1]];
            e.currentTarget.setPointerCapture(e.pointerId);
          }}
          onPointerMove={(e) => {
            if (drag.current)
              setPan([
                e.clientX - drag.current[0],
                e.clientY - drag.current[1],
              ]);
          }}
          onPointerUp={() => (drag.current = null)}
        >
          <g
            transform={`translate(${pan[0]},${pan[1]}) translate(450,350) scale(${scale}) translate(-450,-350)`}
          >
            {boundary.data?.features.map((f, i) => (
              <path
                key={i}
                d={outline(f.geometry)}
                fill="#2b3437"
                stroke="#677474"
                strokeWidth={0.9}
              />
            ))}
            {features.features.map((f, i) => {
              if (f.geometry.type !== "Point") return null;
              const [x, y] = f.geometry.coordinates;
              const props = f.properties || {};
              return (
                <circle
                  key={i}
                  cx={((x - 93) / 16) * 900}
                  cy={((8 - y) / 15) * 700}
                  r={Math.min(
                    18,
                    2 + Math.sqrt(Number(props.detections || 1)) * 0.35,
                  )}
                  fill="#e8a264"
                  fillOpacity={mode === "density" ? 0.35 : 0.72}
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={() => setSelection(props as Row)}
                >
                  <title>
                    {props.date || "Grid aggregate"} · {props.detections || 1}{" "}
                    detections
                  </title>
                </circle>
              );
            })}
          </g>
        </svg>
      )}
      <div className="map-layer-switch" aria-label="Map display mode">
        {["points", "density", "aggregation"].map((v) => (
          <button
            key={v}
            aria-pressed={mode === v}
            disabled={fallback && v === "density"}
            title={
              fallback && v === "density"
                ? "Density requires WebGL2. Points and aggregation remain available."
                : v
            }
            onClick={() => setMode(v)}
          >
            <Layers size={12} />
            {v}
          </button>
        ))}
      </div>
      <div className="map-tools">
        {fallback && (
          <>
            <Button
              size="icon"
              variant="outline"
              aria-label="Zoom in"
              onClick={() => setScale((v) => Math.min(6, v * 1.25))}
            >
              <Plus size={16} />
            </Button>
            <Button
              size="icon"
              variant="outline"
              aria-label="Zoom out"
              onClick={() => setScale((v) => Math.max(0.7, v / 1.25))}
            >
              <Minus size={16} />
            </Button>
          </>
        )}
        <Button
          size="icon"
          variant="outline"
          aria-label="Reset map view"
          onClick={reset}
        >
          <Expand size={16} />
        </Button>
      </div>
      {!connected && (
        <div className="map-empty">
          <MapPin size={21} />
          <b>Your observations belong here.</b>
          <span>Connect a dataset to explore Sumatra.</span>
        </div>
      )}
      {selection && (
        <div className="map-popup">
          <button
            aria-label="Close observation"
            onClick={() => setSelection(null)}
          >
            ×
          </button>
          <b>
            {selection.observation_id
              ? "Hotspot observation"
              : "Display grid cell"}
          </b>
          {Object.entries(selection).map(([k, v]) => (
            <div key={k}>
              <span>
                {k === "frp"
                  ? selection.observation_id
                    ? "FRP (MW)"
                    : "Mean FRP (MW)"
                  : k.replaceAll("_", " ")}
              </span>
              <strong>{v === null ? "—" : String(v)}</strong>
            </div>
          ))}
        </div>
      )}
      <div className="map-footer">
        <span>
          <i className="legend-dot" />{" "}
          {connected
            ? `${num(result.data?.total)} detections in view`
            : "No observation layer"}
        </span>
        <span>
          {fallback ? "Reduced map mode · " : ""}
          {result.data?.mode === "aggregation"
            ? `Grid ${result.data.cell_degrees}° · `
            : ""}
          BIG boundary context
        </span>
      </div>
      {result.error && (
        <div className="map-error" role="alert">
          {result.error}
        </div>
      )}
      {result.loading && connected && (
        <div className="map-loading">Updating map…</div>
      )}
      {result.data?.capped && connected && (
        <div className="map-error">
          Display capped at 5,000 cells. Narrow the map view.
        </div>
      )}
      <span className="map-note">
        <Info size={11} /> Rendering aggregation is not a scientific cluster.
      </span>
    </div>
  );
}
