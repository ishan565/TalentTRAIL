import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

const factors = [
  { key: "skills_match", label: "Skills", weight: "40%" },
  { key: "projects_match", label: "Projects", weight: "20%" },
  { key: "experience_match", label: "Experience", weight: "20%" },
  { key: "education_match", label: "Education", weight: "10%" },
  { key: "keyword_density", label: "Keyword Density", weight: "10%" },
];

// Map a 0–100 score to a verdict + color tokens used across the card.
function verdictFor(score) {
  if (score >= 75)
    return {
      label: "Strong match",
      tone: "emerald",
      fill: "#10b981",
      Icon: CheckCircle2,
      blurb:
        "Your resume aligns well with this role and should pass most ATS filters.",
    };
  if (score >= 50)
    return {
      label: "Moderate match",
      tone: "amber",
      fill: "#f59e0b",
      Icon: AlertTriangle,
      blurb:
        "A solid base, but tighten the weaker areas below to clear more ATS screens.",
    };
  return {
    label: "Needs work",
    tone: "rose",
    fill: "#f43f5e",
    Icon: XCircle,
    blurb:
      "Significant gaps for this role — focus on the low-scoring factors below.",
  };
}

const TONE = {
  emerald:
    "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300",
  amber:
    "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300",
  rose:
    "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300",
};

function barColor(v) {
  if (v >= 75) return "bg-emerald-500";
  if (v >= 50) return "bg-amber-500";
  return "bg-rose-500";
}

export default function ATSScoreCard({ result }) {
  const score = Math.round(result.total_score);
  const v = verdictFor(score);
  const data = [{ name: "ATS", value: score, fill: v.fill }];

  const rows = factors.map((f) => ({
    ...f,
    value: Math.round((result[f.key] ?? 0) * 100),
  }));
  const strong = rows.filter((r) => r.value >= 70);
  const weak = rows
    .filter((r) => r.value < 50)
    .sort((a, b) => a.value - b.value);
  const missing = result.breakdown?.missing_skills ?? [];

  return (
    <div className="card space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          ATS Score
        </h3>
        <span className={`badge border ${TONE[v.tone]}`}>
          <v.Icon size={13} className="mr-1" /> {v.label}
        </span>
      </div>

      {/* Brief verdict — at-a-glance summary */}
      <div className={`flex items-start gap-3 rounded-xl border p-3 ${TONE[v.tone]}`}>
        <v.Icon size={18} className="mt-0.5 shrink-0" />
        <div className="text-sm">
          <p className="font-semibold">
            {score}/100 — {v.label}
          </p>
          <p className="opacity-90">{v.blurb}</p>
        </div>
      </div>

      {/* Depth — gauge + factor breakdown */}
      <div className="flex flex-col items-center gap-6 md:flex-row">
        <div className="relative h-44 w-44 shrink-0">
          <ResponsiveContainer>
            <RadialBarChart
              innerRadius="70%"
              outerRadius="100%"
              data={data}
              startAngle={90}
              endAngle={-270}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar background dataKey="value" cornerRadius={12} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-extrabold text-slate-900 dark:text-white">
              {score}
            </span>
            <span className="text-xs font-medium text-slate-400 dark:text-slate-400">
              / 100
            </span>
          </div>
        </div>

        <div className="flex-1 space-y-3 self-stretch">
          {rows.map((f) => (
            <div key={f.key}>
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-600 dark:text-slate-300">
                  {f.label}{" "}
                  <span className="text-slate-400 dark:text-slate-500">
                    ({f.weight})
                  </span>
                </span>
                <span className="font-semibold text-slate-800 dark:text-white">
                  {f.value}%
                </span>
              </div>
              <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className={`h-2 rounded-full transition-all duration-700 ${barColor(
                    f.value
                  )}`}
                  style={{ width: `${f.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Organized takeaways */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 size={13} /> Working in your favor
          </p>
          {strong.length ? (
            <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
              {strong.map((s) => (
                <li key={s.key}>
                  {s.label} — {s.value}%
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400 dark:text-slate-500">
              No factor is above 70% yet.
            </p>
          )}
        </div>
        <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-rose-600 dark:text-rose-400">
            <AlertTriangle size={13} /> Fix these first
          </p>
          {weak.length ? (
            <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
              {weak.map((s) => (
                <li key={s.key}>
                  {s.label} — {s.value}%
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400 dark:text-slate-500">
              Nothing critical — all factors are at 50%+.
            </p>
          )}
        </div>
      </div>

      {missing.length > 0 && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 dark:border-rose-500/30 dark:bg-rose-500/10">
          <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-rose-600 dark:text-rose-300">
            Missing skills
          </p>
          <div className="flex flex-wrap gap-1.5">
            {missing.map((m) => (
              <span
                key={m}
                className="badge bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-200"
              >
                {m}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
