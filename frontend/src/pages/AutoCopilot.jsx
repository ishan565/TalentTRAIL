import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Zap,
  Search,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Building2,
  MapPin,
  Download,
  ArrowRight,
  Sparkles,
  Trophy,
  Rocket,
  GraduationCap,
  Wrench,
  Award,
} from "lucide-react";
import { api } from "../lib/api";
import ATSScoreCard from "../components/ATSScoreCard";
import KeywordGapTable from "../components/KeywordGapTable";

// Friendly names for the 9 LangGraph agents (in execution order).
const AGENT_LABELS = {
  resume_analysis: "Resume Analysis",
  job_discovery: "Job Discovery",
  semantic_matching: "Semantic Matching",
  ats_scoring: "ATS Scoring",
  missing_keywords: "Keyword Gap",
  resume_optimization: "Resume Optimization",
  cover_letter: "Cover Letter",
  career_strategy: "Career Strategy",
  application_tracker: "Application Tracking",
};

const PIPELINE = Object.keys(AGENT_LABELS);

export default function AutoCopilot() {
  const nav = useNavigate();
  const [query, setQuery] = useState("Software Engineer");
  const [location, setLocation] = useState("India");
  const [hasResume, setHasResume] = useState(true);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .activeResume()
      .then((r) => setHasResume(Boolean(r?.parsed)))
      .catch(() => setHasResume(false));
  }, []);

  // Animate the agent timeline while the backend runs the real pipeline.
  useEffect(() => {
    if (!running) return;
    setProgress(0);
    const t = setInterval(() => {
      setProgress((p) => (p < PIPELINE.length - 1 ? p + 1 : p));
    }, 1100);
    return () => clearInterval(t);
  }, [running]);

  const runAuto = async () => {
    setRunning(true);
    setError("");
    setResult(null);
    setSaved(false);
    try {
      const data = await api.runPipeline(query, location);
      setResult(data);
    } catch (e) {
      setError(
        e?.response?.data?.detail ??
          "The pipeline failed to run. Make sure the backend is running and try again."
      );
    } finally {
      setRunning(false);
    }
  };

  const topJob = result?.ranked_jobs?.[0]?.job;
  const ats = result?.ats_scores && Object.keys(result.ats_scores).length ? result.ats_scores : null;
  const keywords =
    result?.missing_keywords && result.missing_keywords.present ? result.missing_keywords : null;
  const optimized = result?.optimized_resume;
  const recs = result?.recommendations;
  const coverLetter =
    result?.cover_letters &&
    (result.cover_letters[String(ats?.job_id)] ||
      Object.values(result.cover_letters)[0] ||
      "");

  const completedAgents = new Set(
    (result?.execution_history ?? []).map((h) => h.agent)
  );

  const downloadLetter = () => {
    const blob = new Blob([coverLetter], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cover-letter.txt";
    a.click();
  };

  const saveTopJob = async () => {
    if (!topJob?.id) return;
    await api.createApplication(topJob.id, "applied");
    setSaved(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-fuchsia-200 bg-white/70 px-3 py-1 text-xs font-semibold text-fuchsia-700 backdrop-blur dark:border-fuchsia-500/30 dark:bg-slate-800/70 dark:text-fuchsia-300">
          <Zap size={13} /> Fully Autonomous · No human in the loop
        </div>
        <h1 className="section-title mt-2">Autopilot</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          One click runs the entire 9-agent pipeline end-to-end — discover, rank,
          score, find gaps, tailor your resume, write a cover letter, and build a
          career plan. Sit back and watch.
        </p>
      </div>

      {!hasResume && (
        <div className="card flex items-start gap-3 border-amber-200 bg-amber-50/70 dark:border-amber-500/30 dark:bg-amber-500/10">
          <AlertTriangle className="mt-0.5 shrink-0 text-amber-500" size={18} />
          <div className="text-sm">
            <p className="font-semibold text-amber-700 dark:text-amber-300">
              No resume on file
            </p>
            <p className="text-amber-600/90 dark:text-amber-200/80">
              For best results, upload your resume first in the guided{" "}
              <button
                className="font-semibold underline"
                onClick={() => nav("/")}
              >
                AI Assistant
              </button>
              . You can still run autopilot, but tailoring will be limited.
            </p>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="card">
        <div className="flex flex-wrap gap-3">
          <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 dark:border-slate-700 dark:bg-slate-900">
            <Search className="text-slate-400" size={18} />
            <input
              className="input border-0 shadow-none focus:ring-0 dark:bg-slate-900"
              placeholder="Role or keywords"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={running}
            />
          </div>
          <input
            className="input max-w-xs"
            placeholder="Location (optional)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={running}
          />
          <button className="btn" onClick={runAuto} disabled={running || !query.trim()}>
            {running ? (
              <>
                <Loader2 className="animate-spin" size={16} /> Running…
              </>
            ) : (
              <>
                <Zap size={16} /> Run Autopilot
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-300">
          {error}
        </div>
      )}

      {/* Agent timeline */}
      {(running || result) && (
        <div className="card">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-slate-100">
            <Sparkles size={18} className="text-brand-500" /> Agent pipeline
          </h2>
          <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {PIPELINE.map((agent, i) => {
              const done = result ? completedAgents.has(agent) : i < progress;
              const active = running && i === progress;
              return (
                <li
                  key={agent}
                  className={`flex items-center gap-2.5 rounded-xl border px-3 py-2.5 text-sm font-medium transition-all ${
                    done
                      ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300"
                      : active
                      ? "border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-500/40 dark:bg-brand-500/10 dark:text-brand-300"
                      : "border-slate-200 text-slate-400 dark:border-slate-700 dark:text-slate-500"
                  }`}
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center">
                    {done ? (
                      <CheckCircle2 size={18} />
                    ) : active ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <span className="text-xs font-bold">{i + 1}</span>
                    )}
                  </span>
                  {AGENT_LABELS[agent]}
                </li>
              );
            })}
          </ol>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-5 animate-fade-in-up">
          {/* Top match */}
          {topJob && (
            <div className="card border-brand-200 bg-brand-50/60 dark:border-brand-500/30 dark:bg-slate-900">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-300">
                    <Trophy size={14} /> Top match
                  </p>
                  <h2 className="mt-1 text-xl font-bold text-slate-900 dark:text-slate-100">
                    {topJob.title}
                  </h2>
                  <p className="mt-1 flex flex-wrap items-center gap-x-3 text-sm text-slate-500 dark:text-slate-400">
                    <span className="flex items-center gap-1">
                      <Building2 size={14} className="text-brand-400" />
                      {topJob.company}
                    </span>
                    {topJob.location && (
                      <span className="flex items-center gap-1">
                        <MapPin size={14} className="text-brand-400" />
                        {topJob.location}
                      </span>
                    )}
                  </p>
                </div>
                {result.ranked_jobs?.[0]?.final_score != null && (
                  <span className="badge bg-brand-600 text-white">
                    {Math.round(result.ranked_jobs[0].final_score * 100)}% fit
                  </span>
                )}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn" onClick={saveTopJob} disabled={saved}>
                  {saved ? (
                    <>
                      <CheckCircle2 size={16} /> Saved to tracker
                    </>
                  ) : (
                    <>
                      Save to tracker <ArrowRight size={16} />
                    </>
                  )}
                </button>
                <button className="btn-ghost" onClick={() => nav("/tracker")}>
                  Open tracker
                </button>
              </div>
            </div>
          )}

          {/* All ranked jobs */}
          {result.ranked_jobs?.length > 1 && (
            <div className="card">
              <h2 className="mb-3 text-lg font-bold text-slate-900 dark:text-slate-100">
                Ranked matches
              </h2>
              <div className="grid gap-3 md:grid-cols-2">
                {result.ranked_jobs.slice(0, 8).map((r, i) => (
                  <div
                    key={r.job?.id ?? i}
                    className="rounded-xl border border-slate-200 p-3 dark:border-slate-700"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                        {r.job?.title}
                      </h3>
                      <span className="badge bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                        {Math.round((r.final_score ?? 0) * 100)}%
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {r.job?.company}
                      {r.job?.location ? ` · ${r.job.location}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {ats && <ATSScoreCard result={ats} />}
          {keywords && <KeywordGapTable data={keywords} />}

          {/* Optimized resume */}
          {optimized?.optimized_bullets?.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Optimized resume
              </h2>
              {optimized.improved_summary && (
                <p className="mt-1 mb-3 text-sm text-slate-500 dark:text-slate-400">
                  {optimized.improved_summary}
                </p>
              )}
              <ul className="space-y-2">
                {optimized.optimized_bullets.map((b, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded-lg bg-slate-50 p-2.5 text-sm text-slate-700 dark:bg-slate-900/60 dark:text-slate-200"
                  >
                    <CheckCircle2
                      size={15}
                      className="mt-0.5 shrink-0 text-emerald-500"
                    />
                    {b}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Cover letter */}
          {coverLetter && (
            <div className="card">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Cover letter
                </h2>
                <button className="btn-ghost py-2" onClick={downloadLetter}>
                  <Download size={14} /> Download
                </button>
              </div>
              <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-4 font-mono text-sm leading-relaxed text-slate-700 dark:bg-slate-900/60 dark:text-slate-200">
                {coverLetter}
              </pre>
            </div>
          )}

          {/* Career plan */}
          {recs && (
            <div className="card">
              <h2 className="mb-4 text-lg font-bold text-slate-900 dark:text-slate-100">
                Career strategy
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <PlanList
                  icon={Rocket}
                  title="Target roles"
                  items={recs.target_roles}
                />
                <PlanList
                  icon={GraduationCap}
                  title="Skills to learn"
                  items={recs.skills_to_learn}
                />
                <PlanList
                  icon={Wrench}
                  title="Projects to build"
                  items={recs.projects_to_build}
                />
                <PlanList
                  icon={Award}
                  title="Certifications"
                  items={recs.certifications}
                />
              </div>
              {recs.roadmap && (
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {["30_days", "60_days", "90_days"].map((k) => (
                    <div
                      key={k}
                      className="rounded-xl border border-slate-200 p-3 dark:border-slate-700"
                    >
                      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-brand-600 dark:text-brand-300">
                        {k.replace("_", " ")}
                      </p>
                      <ul className="space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
                        {(recs.roadmap[k] ?? []).map((s, i) => (
                          <li key={i} className="flex gap-2">
                            <span className="text-brand-400">•</span>
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {result.errors?.length > 0 && (
            <div className="card border-amber-200 bg-amber-50/60 dark:border-amber-500/30 dark:bg-amber-500/10">
              <p className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                Some agents reported issues (the pipeline still completed):
              </p>
              <ul className="mt-2 space-y-1 text-sm text-amber-600/90 dark:text-amber-200/80">
                {result.errors.map((e, i) => (
                  <li key={i}>
                    {AGENT_LABELS[e.agent] ?? e.agent}: {e.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PlanList({ icon: Icon, title, items }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
        <Icon size={15} className="text-brand-500" /> {title}
      </p>
      <ul className="space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-brand-400">•</span>
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
