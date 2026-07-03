import { useState } from "react";
import { api } from "../lib/api";
import { Map } from "lucide-react";

function Section({ title, items = [] }) {
  return (
    <div className="card">
      <h3 className="mb-2 font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      <ul className="list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-300">
        {items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
    </div>
  );
}

export default function Roadmap() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);

  const generate = async () => {
    setBusy(true);
    try {
      setData(await api.roadmap());
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="section-title">Career Roadmap</h1>
        <button className="btn" onClick={generate} disabled={busy}>
          <Map size={16} /> {busy ? "Generating…" : "Generate"}
        </button>
      </div>

      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Section title="Target Roles" items={data.target_roles} />
            <Section title="Skills to Learn" items={data.skills_to_learn} />
            <Section title="Projects to Build" items={data.projects_to_build} />
            <Section title="Certifications" items={data.certifications} />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {Object.entries(data.roadmap ?? {}).map(([phase, items]) => (
              <Section
                key={phase}
                title={phase.replace("_", " ").toUpperCase()}
                items={items}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
