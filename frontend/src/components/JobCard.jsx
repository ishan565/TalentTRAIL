import { MapPin, Building2, ExternalLink, Sparkles } from "lucide-react";

function ringColor(score) {
  if (score >= 0.7) return "text-emerald-500";
  if (score >= 0.4) return "text-amber-500";
  return "text-rose-500";
}

export default function JobCard({ ranked, onSelect, onSave }) {
  const { job } = ranked;
  const pct = Math.round(ranked.final_score * 100);
  const circumference = 2 * Math.PI * 18;
  return (
    <div className="card card-hover flex flex-col gap-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-base font-bold text-slate-900 dark:text-slate-100">
            {job.title}
          </h3>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <Building2 size={14} className="text-brand-400" /> {job.company}
            </span>
            {job.location && (
              <span className="flex items-center gap-1.5">
                <MapPin size={14} className="text-brand-400" /> {job.location}
              </span>
            )}
          </p>
        </div>
        <div className="relative flex h-14 w-14 shrink-0 items-center justify-center">
          <svg className="h-14 w-14 -rotate-90" viewBox="0 0 44 44">
            <circle
              cx="22"
              cy="22"
              r="18"
              fill="none"
              strokeWidth="4"
              className="stroke-slate-100 dark:stroke-slate-700"
            />
            <circle
              cx="22"
              cy="22"
              r="18"
              fill="none"
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - ranked.final_score)}
              className={`${ringColor(ranked.final_score)} transition-all duration-700`}
              stroke="currentColor"
            />
          </svg>
          <span className="absolute text-center text-[11px] font-bold leading-tight text-slate-700 dark:text-slate-200">
            {pct}% match
          </span>
        </div>
      </div>

      {job.skills && (
        <div className="flex flex-wrap gap-1.5">
          {job.skills.slice(0, 6).map((s) => (
            <span
              key={s}
              className="badge bg-brand-50 text-brand-700 ring-1 ring-brand-100 dark:bg-brand-500/15 dark:text-brand-300 dark:ring-brand-500/20"
            >
              {s}
            </span>
          ))}
        </div>
      )}

      {ranked.explanation?.why && (
        <p className="flex items-start gap-1.5 rounded-lg bg-slate-50 p-2.5 text-xs text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
          <Sparkles size={13} className="mt-0.5 shrink-0 text-brand-400" />
          {ranked.explanation.why}
        </p>
      )}

      <div className="flex items-center gap-2 pt-1">
        {onSelect && (
          <button className="btn py-2" onClick={() => onSelect(job.id)}>
            Analyze
          </button>
        )}
        {onSave && (
          <button className="btn-ghost py-2" onClick={() => onSave(job.id)}>
            Save
          </button>
        )}
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost py-2"
          >
            <ExternalLink size={14} /> View
          </a>
        )}
      </div>
    </div>
  );
}
