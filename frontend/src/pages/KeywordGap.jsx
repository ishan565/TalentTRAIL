import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import KeywordGapTable from "../components/KeywordGapTable";

export default function KeywordGap() {
  const nav = useNavigate();
  const [resumeId, setResumeId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.activeResume().then((r) => setResumeId(r.id)).catch(() => {});
    api
      .recommendations()
      .then((recs) => {
        if (recs.length) {
          setJobs(recs);
          setJobId(recs[0].job.id);
        } else {
          return api.allJobs().then((all) => {
            const shaped = all.map((j) => ({ job: j, final_score: 0 }));
            setJobs(shaped);
            if (shaped[0]) setJobId(shaped[0].job.id);
          });
        }
      })
      .catch(() => {});
  }, []);

  const run = async () => {
    if (!resumeId || !jobId) return;
    setBusy(true);
    try {
      setResult(await api.keywords(resumeId, jobId));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="section-title">Keyword Gap Analysis</h1>
      <div className="card flex flex-wrap items-end gap-3">
        <div className="flex-1">
          <label className="text-sm text-slate-500 dark:text-slate-300">Target job</label>
          {jobs.length === 0 ? (
            <p className="mt-1 text-sm text-slate-400 dark:text-slate-500">
              No jobs yet —{" "}
              <button className="font-semibold text-brand-600 underline dark:text-brand-400" onClick={() => nav("/jobs")}>
                search for jobs
              </button>{" "}
              first.
            </p>
          ) : (
            <select
              className="input mt-1"
              value={jobId ?? ""}
              onChange={(e) => { setJobId(Number(e.target.value)); setResult(null); }}
            >
              {jobs.map((j) => (
                <option key={j.job.id} value={j.job.id}>
                  {j.job.title} — {j.job.company}
                </option>
              ))}
            </select>
          )}
        </div>
        <button
          className="btn"
          onClick={run}
          disabled={busy || !resumeId || !jobId || jobs.length === 0}
        >
          {busy ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {result && <KeywordGapTable data={result} />}
    </div>
  );
}
