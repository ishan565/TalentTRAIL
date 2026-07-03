import { useState } from "react";
import { Search } from "lucide-react";
import { api } from "../lib/api";
import JobCard from "../components/JobCard";

export default function JobSearch() {
  const [query, setQuery] = useState("Python Engineer");
  const [location, setLocation] = useState("");
  const [jobs, setJobs] = useState([]);
  const [busy, setBusy] = useState(false);

  const search = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      setJobs(await api.searchJobs(query, location || undefined));
    } finally {
      setBusy(false);
    }
  };

  const save = async (jobId) => {
    await api.createApplication(jobId, "saved");
  };

  return (
    <div className="space-y-6">
      <h1 className="section-title">Job Search</h1>
      <form onSubmit={search} className="card flex flex-wrap gap-3">
        <div className="flex flex-1 items-center gap-2">
          <Search className="text-slate-400" size={18} />
          <input
            className="input"
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
        <button className="btn" disabled={busy}>
          {busy ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="grid gap-4 md:grid-cols-2">
        {jobs.map((j) => (
          <JobCard key={j.job.id} ranked={j} onSave={save} />
        ))}
      </div>
    </div>
  );
}
