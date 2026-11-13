"use client";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  Legend,
} from "recharts";
import type { Row } from "@/lib/types";
import { num } from "@/lib/utils";
const tip = {
  background: "#262A31",
  border: "1px solid #353942",
  borderRadius: 7,
  color: "#f2f1ed",
  fontSize: 12,
};
export function Trend({
  data,
  annual = false,
}: {
  data: Row[];
  annual?: boolean;
}) {
  const axes = (
    <>
      <CartesianGrid vertical={false} stroke="#343943" strokeDasharray="2 5" />
      <XAxis
        dataKey="period"
        tick={{ fill: "#a2a7b0", fontSize: 10 }}
        minTickGap={28}
        axisLine={false}
        tickLine={false}
      />
      <YAxis
        tick={{ fill: "#a2a7b0", fontSize: 10 }}
        tickFormatter={(v) => num(v)}
        axisLine={false}
        tickLine={false}
      />
      <Tooltip contentStyle={tip} />
    </>
  );
  return (
    <div
      className="chart"
      role="img"
      aria-label={annual ? "Annual detections" : "Monthly detections"}
    >
      <ResponsiveContainer width="100%" height="100%">
        {annual ? (
          <BarChart data={data} margin={{ left: -17, right: 15 }}>
            {axes}
            <Bar
              dataKey="detections"
              name="Detections"
              fill="#e8a264"
              radius={[3, 3, 0, 0]}
              maxBarSize={36}
              isAnimationActive={false}
            />
          </BarChart>
        ) : (
          <AreaChart data={data} margin={{ left: -17, right: 15 }}>
            {axes}
            <Area
              dataKey="detections"
              type="linear"
              stroke="#e8a264"
              fill="#e8a264"
              fillOpacity={0.08}
              strokeWidth={2}
              isAnimationActive={false}
            />
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
export function Bars({ data }: { data: Row[] }) {
  const max = Math.max(...data.map((x) => Number(x.detections)), 1);
  return (
    <div className="bars">
      {data.map((r, i) => (
        <div className="bar-row" key={String(r.name)}>
          <div>
            <span>{String(r.name)}</span>
            <strong>
              {num(r.detections)} <small>detections</small>
            </strong>
          </div>
          <div className="bar-track">
            <span
              style={{
                width: `${(Number(r.detections) / max) * 100}%`,
                background: i % 2 ? "#8ea7ab" : "#e8a264",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
export function Heatmap({ data }: { data: Row[] }) {
  const years = [...new Set(data.map((r) => Number(r.year)))];
  const max = Math.max(...data.map((r) => Number(r.detections)), 1);
  return (
    <div className="table-scroll">
      <table className="heatmap">
        <thead>
          <tr>
            <th>Year</th>
            {[
              "Jan",
              "Feb",
              "Mar",
              "Apr",
              "May",
              "Jun",
              "Jul",
              "Aug",
              "Sep",
              "Oct",
              "Nov",
              "Dec",
            ].map((m) => (
              <th key={m}>{m}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {years.map((y) => (
            <tr key={y}>
              <th>{y}</th>
              {Array.from({ length: 12 }, (_, i) => {
                const n = data.find(
                  (r) => r.year === y && r.month === i + 1,
                )?.detections;
                return (
                  <td key={i}>
                    <button
                      title={`${y}-${i + 1}: ${n ?? "No retained records"}`}
                      aria-label={`${y}-${i + 1}: ${n ?? "No retained records"}`}
                      style={{
                        background: n
                          ? `rgba(232,162,100,${0.13 + (0.8 * Math.log1p(Number(n))) / Math.log1p(max)})`
                          : "#252a32",
                      }}
                    >
                      {num(n)}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function ComparePlot({ rows, years }: { rows: Row[]; years: number[] }) {
  const data = Array.from({ length: 12 }, (_, i) => ({
    month: i + 1,
    ...Object.fromEntries(
      years.map((y) => [
        String(y),
        rows.find((r) => r.year === y && r.month === i + 1)?.detections ?? null,
      ]),
    ),
  }));
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#353942" vertical={false} />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip contentStyle={tip} />
          <Legend />
          {[...new Set(years)].map((y, i) => (
            <Line
              key={y}
              dataKey={String(y)}
              stroke={i ? "#8ea7ab" : "#e8a264"}
              strokeDasharray={i ? "5 3" : undefined}
              connectNulls={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
