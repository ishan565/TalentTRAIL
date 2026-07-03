import { useEffect, useState } from "react";
import { api } from "../lib/api";
import JobCard from "../components/JobCard";

export default function Recommendations() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    api.recommendations().then(setJobs).catch(() => setJobs([]));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="section-title">Recommended Jobs</h1>
      {jobs.length === 0 && (
        <p className="text-slate-500">
          Run a job search first to generate ranked recommendations.
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {jobs.map((j) => (
          <JobCard key={j.job.id} ranked={j} />
        ))}
      </div>
    </div>
  );
}
