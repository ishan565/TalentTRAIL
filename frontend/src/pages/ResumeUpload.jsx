import { useEffect, useState } from "react";
import { Upload, CheckCircle2 } from "lucide-react";
import { api } from "../lib/api";

export default function ResumeUpload() {
  const [resume, setResume] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.activeResume().then(setResume).catch(() => {});
  }, []);

  const handleFile = async (file) => {
    setBusy(true);
    setError("");
    try {
      const uploaded = await api.uploadResume(file);
      const analyzed = await api.analyzeResume(uploaded.id);
      setResume(analyzed);
    } catch (e) {
      setError(e?.response?.data?.detail ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="section-title">Resume Upload</h1>

      <label className="card flex cursor-pointer flex-col items-center justify-center gap-2 border-2 border-dashed py-12 text-center">
        <Upload className="text-brand-600" />
        <span className="font-medium">
          {busy ? "Analyzing…" : "Click to upload PDF, DOCX, or TXT"}
        </span>
        <span className="text-xs text-slate-400">Max 10 MB</span>
        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt,.md"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </label>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {resume?.parsed && (
        <div className="card space-y-3">
          <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 size={18} /> Parsed (v{resume.version})
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-300">{resume.summary}</p>
          <div>
            <p className="mb-1 text-sm font-medium">Skills</p>
            <div className="flex flex-wrap gap-1.5">
              {(resume.parsed.skills ?? []).map((s) => (
                <span key={s} className="badge bg-brand-50 text-brand-700">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
