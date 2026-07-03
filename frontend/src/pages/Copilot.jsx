import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  Search,
  Target,
  FileEdit,
  Send,
  CheckCircle2,
  Loader2,
  Sparkles,
  Building2,
  MapPin,
  ArrowRight,
  Download,
  RefreshCw,
} from "lucide-react";
import { api } from "../lib/api";
import ATSScoreCard from "../components/ATSScoreCard";
import KeywordGapTable from "../components/KeywordGapTable";

const STEPS = [
  { id: 0, label: "Upload Resume", icon: Upload },
  { id: 1, label: "Discover Jobs", icon: Search },
  { id: 2, label: "Fit Analysis", icon: Target },
  { id: 3, label: "Tailor & Generate", icon: FileEdit },
  { id: 4, label: "Apply", icon: Send },
];

const COMPANY_TYPES = ["startup", "faang", "enterprise", "ai"];

function StepRail({ current }) {
  return (
    <ol className="flex flex-col gap-1">
      {STEPS.map((s) => {
        const done = s.id < current;
        const active = s.id === current;
        const Icon = done ? CheckCircle2 : s.icon;
        return (
          <li
            key={s.id}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all ${
              active
                ? "bg-brand-gradient text-white shadow-glow"
                : done
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-slate-400 dark:text-slate-500"
            }`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                active
                  ? "bg-white/20"
                  : done
                  ? "bg-emerald-100 dark:bg-emerald-500/15"
                  : "bg-slate-100 dark:bg-slate-700"
              }`}
            >
              <Icon size={16} />
            </span>
            {s.label}
          </li>
        );
      })}
    </ol>
  );
}

function Spinner({ label }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-slate-500 dark:text-slate-400">
      <Loader2 className="animate-spin text-brand-500" size={20} />
      {label}
    </div>
  );
}

export default function Copilot() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("");
  const [error, setError] = useState("");

  // step 0
  const [resume, setResume] = useState(null);
  // step 1
  const [query, setQuery] = useState("Software Engineer");
  const [location, setLocation] = useState("India");
  const [internships, setInternships] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  // step 2
  const [ats, setAts] = useState(null);
  const [keywords, setKeywords] = useState(null);
  // step 3
  const [companyType, setCompanyType] = useState("startup");
  const [optimized, setOptimized] = useState(null);
  const [coverLetter, setCoverLetter] = useState("");
  // step 4
  const [applied, setApplied] = useState(false);

  // Resume the flow if a resume already exists
  useEffect(() => {
    api
      .activeResume()
      .then((r) => {
        if (r?.parsed) setResume(r);
      })
      .catch(() => {});
  }, []);

  const run = async (label, fn) => {
    setBusy(true);
    setBusyLabel(label);
    setError("");
    try {
      return await fn();
    } catch (e) {
      setError(e?.response?.data?.detail ?? "Something went wrong. Try again.");
      throw e;
    } finally {
      setBusy(false);
      setBusyLabel("");
    }
  };

  // ---- Step 0: upload + parse + analyze ----
  const handleFile = async (file) => {
    await run("Parsing your resume…", async () => {
      const uploaded = await api.uploadResume(file);
      const analyzed = await api.analyzeResume(uploaded.id);
      setResume(analyzed);
    });
  };

  // ---- Step 1: discover jobs ----
  const discover = async () => {
    await run("Discovering & ranking jobs…", async () => {
      const results = await api.searchJobs(
        query,
        location || undefined,
        internships
      );
      setJobs(results);
      setStep(1);
    });
  };

  const pickJob = async (ranked) => {
    setSelectedJob(ranked);
    // reset downstream
    setAts(null);
    setKeywords(null);
    setOptimized(null);
    setCoverLetter("");
    setApplied(false);
    await run("Scoring fit & finding keyword gaps…", async () => {
      const [a, k] = await Promise.all([
        api.atsScore(resume.id, ranked.job.id),
        api.keywords(resume.id, ranked.job.id),
      ]);
      setAts(a);
      setKeywords(k);
      setStep(2);
    });
  };

  // ---- Step 3: optimize + cover letter ----
  const generate = async () => {
    await run("Tailoring resume & writing cover letter…", async () => {
      const [opt, cl] = await Promise.all([
        api.optimize(resume.id, selectedJob.job.id),
        api.coverLetter(resume.id, selectedJob.job.id, companyType),
      ]);
      setOptimized(opt);
      setCoverLetter(cl.content);
      setStep(3);
    });
  };

  const regenerateLetter = async () => {
    await run("Rewriting cover letter…", async () => {
      const cl = await api.coverLetter(resume.id, selectedJob.job.id, companyType);
      setCoverLetter(cl.content);
    });
  };

  // ---- Step 4: apply ----
  const apply = async () => {
    await run("Saving your application…", async () => {
      await api.createApplication(selectedJob.job.id, "applied");
      setApplied(true);
      setStep(4);
    });
  };

  const downloadLetter = () => {
    const blob = new Blob([coverLetter], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cover-letter.txt";
    a.click();
  };

  const restart = () => {
    setStep(resume ? 1 : 0);
    setJobs([]);
    setSelectedJob(null);
    setAts(null);
    setKeywords(null);
    setOptimized(null);
    setCoverLetter("");
    setApplied(false);
    setError("");
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-white/70 px-3 py-1 text-xs font-semibold text-brand-700 backdrop-blur dark:border-brand-500/30 dark:bg-slate-800/70 dark:text-brand-300">
          <Sparkles size={13} /> Autonomous · Human-in-the-loop
        </div>
        <h1 className="section-title mt-2">AI Assistant</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          One guided flow: upload → discover → analyze → tailor → apply. You stay
          in control at every step.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        {/* Progress rail */}
        <div className="card h-fit lg:sticky lg:top-20">
          <StepRail current={step} />
        </div>

        {/* Content */}
        <div className="min-w-0 space-y-5">
          {error && (
            <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-300">
              {error}
            </div>
          )}

          {busy && (
            <div className="card">
              <Spinner label={busyLabel} />
            </div>
          )}

          {/* STEP 0 — Upload */}
          {!busy && step === 0 && (
            <div className="card animate-fade-in-up">
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Step 1 · Upload your resume
              </h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                We parse it into structured data and extract your skills.
              </p>
              <label className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-brand-200 bg-brand-50/40 py-12 text-center transition hover:border-brand-400 hover:bg-brand-50 dark:border-brand-500/30 dark:bg-brand-500/5 dark:hover:border-brand-400 dark:hover:bg-brand-500/10">
                <Upload className="text-brand-600 dark:text-brand-400" />
                <span className="font-semibold text-slate-700 dark:text-slate-200">
                  Click to upload PDF, DOCX, or TXT
                </span>
                <span className="text-xs text-slate-400">Max 10 MB</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.md"
                  className="hidden"
                  onChange={(e) =>
                    e.target.files?.[0] && handleFile(e.target.files[0])
                  }
                />
              </label>

              {resume?.parsed && (
                <div className="mt-5 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4">
                  <div className="flex items-center gap-2 font-semibold text-emerald-700">
                    <CheckCircle2 size={18} /> Resume parsed (v{resume.version})
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{resume.summary}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {(resume.parsed.skills ?? []).slice(0, 14).map((s) => (
                      <span
                        key={s}
                        className="badge bg-white text-brand-700 ring-1 ring-brand-100"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <button className="btn mt-4" onClick={discover}>
                    Continue to job discovery <ArrowRight size={16} />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* STEP 1 — Discover & select */}
          {!busy && step === 1 && (
            <div className="animate-fade-in-up space-y-4">
              <div className="card">
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Step 2 · Discover jobs
                </h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Search, then pick the role you want to target.
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 dark:border-slate-700 dark:bg-slate-900">
                    <Search className="text-slate-400" size={18} />
                    <input
                      className="input border-0 shadow-none focus:ring-0"
                      placeholder="Role or keywords"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>
                  <input
                    className="input max-w-xs"
                    placeholder="Location (optional)"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                  <button className="btn" onClick={discover}>
                    Search
                  </button>
                </div>
                <label className="mt-3 inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-400"
                    checked={internships}
                    onChange={(e) => setInternships(e.target.checked)}
                  />
                  Internships only
                  <span className="text-xs text-slate-400">
                    (live from Google Jobs · Remotive · Jobicy · Arbeitnow)
                  </span>
                </label>
              </div>

              {jobs.length === 0 && (
                <div className="card text-center text-sm text-slate-500 dark:text-slate-400">
                  No live results for this search. Try a broader keyword
                  {internships ? " or uncheck “Internships only”." : "."}
                </div>
              )}

              <div className="grid gap-3 md:grid-cols-2">
                {jobs.map((r) => {
                  const active = selectedJob?.job.id === r.job.id;
                  const pct = Math.round(r.final_score * 100);
                  return (
                    <button
                      key={r.job.id}
                      onClick={() => pickJob(r)}
                      className={`card card-hover text-left ${
                        active ? "border-brand-400 ring-2 ring-brand-200 dark:ring-brand-500/30" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-bold text-slate-900 dark:text-slate-100">{r.job.title}</h3>
                        <span className="badge bg-brand-50 text-brand-700 ring-1 ring-brand-100 dark:bg-brand-500/15 dark:text-brand-300 dark:ring-brand-500/20">
                          {pct}%
                        </span>
                      </div>
                      <p className="mt-1 flex flex-wrap items-center gap-x-3 text-sm text-slate-500 dark:text-slate-400">
                        <span className="flex items-center gap-1">
                          <Building2 size={14} className="text-brand-400" />
                          {r.job.company}
                        </span>
                        {r.job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin size={14} className="text-brand-400" />
                            {r.job.location}
                          </span>
                        )}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {r.job.is_internship && (
                          <span className="badge bg-emerald-100 text-emerald-700">
                            Internship
                          </span>
                        )}
                        {r.job.salary && (
                          <span className="badge bg-amber-100 text-amber-700">
                            {r.job.salary}
                          </span>
                        )}
                        {r.job.source && (
                          <span className="badge bg-slate-100 text-slate-500 capitalize">
                            {r.job.source}
                          </span>
                        )}
                      </div>
                      <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-600">
                        Select & analyze <ArrowRight size={14} />
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 2 — Fit analysis */}
          {!busy && step === 2 && selectedJob && (
            <div className="animate-fade-in-up space-y-4">
              <div className="card flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-300">
                    Target role
                  </p>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {selectedJob.job.title}
                  </h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {selectedJob.job.company}
                  </p>
                </div>
                <button className="btn-ghost" onClick={() => setStep(1)}>
                  Change job
                </button>
              </div>

              {ats && <ATSScoreCard result={ats} />}
              {keywords && <KeywordGapTable data={keywords} />}

              <div className="card flex items-center justify-between border-brand-200 bg-brand-50/60 dark:border-brand-500/30 dark:bg-slate-900">
                <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                  Happy with the fit? Let the copilot tailor your resume and write
                  a cover letter.
                </p>
                <button className="btn" onClick={generate}>
                  Tailor & generate <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3 — Tailor & generate */}
          {!busy && step === 3 && (
            <div className="animate-fade-in-up space-y-4">
              {optimized && (
                <div className="card">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    Optimized resume
                  </h2>
                  <p className="mt-1 mb-3 text-sm text-slate-500 dark:text-slate-400">
                    {optimized.improved_summary}
                  </p>
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
                  {optimized.notes?.length > 0 && (
                    <p className="mt-3 text-xs text-slate-400">
                      {optimized.notes.join(" · ")}
                    </p>
                  )}
                </div>
              )}

              <div className="card">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Cover letter</h2>
                  <div className="flex items-center gap-2">
                    <select
                      className="input max-w-[140px] py-1.5"
                      value={companyType}
                      onChange={(e) => setCompanyType(e.target.value)}
                    >
                      {COMPANY_TYPES.map((c) => (
                        <option key={c} value={c}>
                          {c.toUpperCase()}
                        </option>
                      ))}
                    </select>
                    <button className="btn-ghost py-2" onClick={regenerateLetter}>
                      <RefreshCw size={14} /> Regenerate
                    </button>
                  </div>
                </div>
                <textarea
                  className="input mt-3 h-72 font-mono text-sm leading-relaxed"
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                />
                <div className="mt-3 flex items-center justify-between">
                  <button className="btn-ghost py-2" onClick={downloadLetter}>
                    <Download size={14} /> Download
                  </button>
                  <button className="btn" onClick={apply}>
                    Approve & apply <Send size={15} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4 — Done */}
          {!busy && step === 4 && applied && (
            <div className="card animate-fade-in-up text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600">
                <CheckCircle2 size={32} />
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                Application tracked!
              </h2>
              <p className="mx-auto mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">
                {selectedJob?.job.title} at {selectedJob?.job.company} was added to
                your tracker as <span className="font-semibold">Applied</span>.
              </p>
              <div className="mt-6 flex justify-center gap-3">
                <button className="btn-ghost" onClick={restart}>
                  <RefreshCw size={15} /> Find another job
                </button>
                <button className="btn" onClick={() => nav("/tracker")}>
                  Open tracker <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
