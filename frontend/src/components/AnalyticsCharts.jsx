import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import { useEffect, useState } from "react";

function useDarkMode() {
  const [dark, setDark] = useState(
    () => document.documentElement.classList.contains("dark")
  );
  useEffect(() => {
    const obs = new MutationObserver(() =>
      setDark(document.documentElement.classList.contains("dark"))
    );
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);
  return dark;
}

export default function AnalyticsCharts({ data }) {
  const isDark = useDarkMode();
  const gridColor = isDark ? "#1e293b" : "#eef2f7";
  const axisColor = isDark ? "#94a3b8" : "#64748b";

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="card">
        <h3 className="mb-3 font-semibold text-slate-900 dark:text-slate-100">Applications Over Time</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data.applications_over_time}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis dataKey="date" fontSize={11} tick={{ fill: axisColor }} />
            <YAxis allowDecimals={false} fontSize={11} tick={{ fill: axisColor }} />
            <Tooltip />
            <Line type="monotone" dataKey="count" stroke="#4f46e5" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="mb-3 font-semibold text-slate-900 dark:text-slate-100">Top Matched Skills</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data.top_matched_skills}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis dataKey="skill" fontSize={11} tick={{ fill: axisColor }} />
            <YAxis allowDecimals={false} fontSize={11} tick={{ fill: axisColor }} />
            <Tooltip />
            <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="mb-3 font-semibold text-slate-900 dark:text-slate-100">Missing Skills</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data.missing_skills}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis dataKey="skill" fontSize={11} tick={{ fill: axisColor }} />
            <YAxis allowDecimals={false} fontSize={11} tick={{ fill: axisColor }} />
            <Tooltip />
            <Bar dataKey="count" fill="#f43f5e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="mb-3 font-semibold text-slate-900 dark:text-slate-100">Job Source Performance</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data.source_performance}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis dataKey="source" fontSize={11} tick={{ fill: axisColor }} />
            <YAxis domain={[0, 1]} fontSize={11} tick={{ fill: axisColor }} />
            <Tooltip />
            <Bar dataKey="avg_score" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
