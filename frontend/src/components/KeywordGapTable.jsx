import { CheckCircle2, Target } from "lucide-react";

const CATEGORY_LABELS = {
  skills: "Skills",
  technologies: "Technologies",
  frameworks: "Frameworks",
  tools: "Tools",
};

export default function KeywordGapTable({ data }) {
  const present = data.present ?? [];
  const missingByCat = data.missing ?? {};
  const allMissing = Object.values(missingByCat).flat();
  const total = present.length + allMissing.length;
  const coverage = total ? Math.round((present.length / total) * 100) : 0;

  const tone =
    coverage >= 70 ? "emerald" : coverage >= 40 ? "amber" : "rose";
  const TONE = {
    emerald:
      "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300",
    amber:
      "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300",
    rose:
      "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300",
  };
  const barTone = {
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
  };

  // The first few missing terms per category are the highest priority.
  const topPriorities = Object.entries(missingByCat)
    .flatMap(([, terms]) => terms.slice(0, 2))
    .slice(0, 6);

  return (
    <div className="card space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Keyword Gap
        </h3>
        <span className={`badge border ${TONE[tone]}`}>{coverage}% coverage</span>
      </div>

      {/* Brief summary */}
      <div className={`rounded-xl border p-3 ${TONE[tone]}`}>
        <p className="text-sm font-semibold">
          {present.length} of {total} keywords present · {allMissing.length}{" "}
          missing
        </p>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/50 dark:bg-slate-900/40">
          <div
            className={`h-2 rounded-full transition-all duration-700 ${barTone[tone]}`}
            style={{ width: `${coverage}%` }}
          />
        </div>
      </div>

      {/* Top priorities — direct, brief callout */}
      {topPriorities.length > 0 && (
        <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-brand-600 dark:text-brand-300">
            <Target size={13} /> Add these first
          </p>
          <div className="flex flex-wrap gap-1.5">
            {topPriorities.map((t) => (
              <span
                key={t}
                className="badge bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Present */}
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 size={13} /> Present in resume ({present.length})
        </p>
        <div className="flex flex-wrap gap-1.5">
          {present.length ? (
            present.map((k) => (
              <span
                key={k}
                className="badge bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
              >
                {k}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-400 dark:text-slate-500">
              None detected
            </span>
          )}
        </div>
      </div>

      {/* Missing — organized by category */}
      <div>
        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-rose-600 dark:text-rose-400">
          Missing by category
        </p>
        <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-sm">
            <tbody>
              {Object.entries(missingByCat).map(([cat, terms], i) => (
                <tr
                  key={cat}
                  className={`align-top ${
                    i > 0 ? "border-t border-slate-100 dark:border-slate-800" : ""
                  }`}
                >
                  <td className="w-32 px-3 py-2.5 font-semibold text-slate-700 dark:text-slate-200">
                    {CATEGORY_LABELS[cat] ?? cat}
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex flex-wrap gap-1.5">
                      {terms.length ? (
                        terms.map((t) => (
                          <span
                            key={t}
                            className="badge bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"
                          >
                            {t}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500">
                          — none
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
