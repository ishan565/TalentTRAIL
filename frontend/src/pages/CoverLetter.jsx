import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

const COMPANY_TYPES = ["startup", "faang", "enterprise", "ai"];

export default function CoverLetter() {
  const nav = useNavigate();
  const [resumeId, setResumeId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [companyType, setCompanyType] = useState("startup");
  const [content, setContent] = useState("");
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

  const generate = async () => {
    if (!resumeId || !jobId) return;
    setBusy(true);
    try {
      const res = await api.coverLetter(resumeId, jobId, companyType);
      setContent(res.content);
    } finally {
      setBusy(false);
    }
  };

  const download = () => {
    const blob = new Blob([content], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cover-letter.txt";
    a.click();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="section-title">Cover Letter Generator</h1>
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
              onChange={(e) => setJobId(Number(e.target.value))}
            >
              {jobs.map((j) => (
                <option key={j.job.id} value={j.job.id}>
                  {j.job.title} — {j.job.company}
                </option>
              ))}
            </select>
          )}
        </div>
        <div>
          <label className="text-sm text-slate-500 dark:text-slate-300">Company type</label>
          <select
            className="input mt-1"
            value={companyType}
            onChange={(e) => setCompanyType(e.target.value)}
          >
            {COMPANY_TYPES.map((c) => (
              <option key={c} value={c}>
                {c.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        <button
          className="btn"
          onClick={generate}
          disabled={busy || !resumeId || !jobId || jobs.length === 0}
        >
          {busy ? "Generating…" : "Generate"}
        </button>
      </div>

      {content && (
        <div className="card space-y-3">
          <textarea
            className="input h-80 font-mono text-sm"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <button className="btn-ghost" onClick={download}>
            Download
          </button>
        </div>
      )}
    </div>
  );
}
