import { useEffect, useMemo, useState } from "react";
import { Building2, GripVertical, Plus, X } from "lucide-react";
import { api } from "../lib/api";

const COLUMNS = [
  { id: "saved", label: "Saved", accent: "bg-slate-400" },
  { id: "applied", label: "Applied", accent: "bg-brand-500" },
  { id: "oa", label: "OA", accent: "bg-sky-500" },
  { id: "interview", label: "Interview", accent: "bg-violet-500" },
  { id: "final_round", label: "Final Round", accent: "bg-fuchsia-500" },
  { id: "offer", label: "Offer", accent: "bg-emerald-500" },
  { id: "rejected", label: "Rejected", accent: "bg-rose-500" },
  { id: "withdrawn", label: "Withdrawn", accent: "bg-amber-500" },
];

const EMPTY_FORM = {
  title: "",
  company: "",
  location: "",
  url: "",
  status: "saved",
  notes: "",
};

export default function ApplicationBoard() {
  const [apps, setApps] = useState([]);
  const [dragId, setDragId] = useState(null);
  const [overCol, setOverCol] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.applications().then(setApps).catch(() => {});

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    const map = Object.fromEntries(COLUMNS.map((c) => [c.id, []]));
    for (const a of apps) (map[a.status] ?? map.saved).push(a);
    return map;
  }, [apps]);

  const move = async (id, status) => {
    const current = apps.find((a) => a.id === id);
    if (!current || current.status === status) return;
    // Optimistic update, then persist.
    setApps((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
    try {
      await api.updateApplication(id, status);
    } catch {
      load(); // revert from server on failure
    }
  };

  const onDrop = (status) => {
    if (dragId != null) move(dragId, status);
    setDragId(null);
    setOverCol(null);
  };

  const openAdd = () => {
    setForm(EMPTY_FORM);
    setError("");
    setShowAdd(true);
  };

  const submitAdd = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.company.trim()) {
      setError("Title and company are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const created = await api.createManualApplication({
        title: form.title.trim(),
        company: form.company.trim(),
        location: form.location.trim() || null,
        url: form.url.trim() || null,
        status: form.status,
        notes: form.notes.trim() || null,
      });
      setApps((prev) => [created, ...prev]);
      setShowAdd(false);
    } catch {
      setError("Could not add the job. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">
          Application Tracker
        </h2>
        <button
          type="button"
          onClick={openAdd}
          className="inline-flex items-center gap-1.5 rounded-xl bg-brand-500 px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-600"
        >
          <Plus size={16} />
          Add job
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {COLUMNS.map((col) => {
          const items = grouped[col.id] ?? [];
          const isOver = overCol === col.id;
          return (
            <div
              key={col.id}
              onDragOver={(e) => {
                e.preventDefault();
                setOverCol(col.id);
              }}
              onDragLeave={() => setOverCol((c) => (c === col.id ? null : c))}
              onDrop={() => onDrop(col.id)}
              className={`flex flex-col rounded-2xl border p-3 transition-colors ${
                isOver
                  ? "border-brand-300 bg-brand-50 dark:border-brand-500/50 dark:bg-brand-500/10"
                  : "border-slate-200/70 bg-slate-50 dark:border-slate-700/60 dark:bg-slate-800/50"
              }`}
            >
              <div className="mb-2.5 flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                  <span className={`h-2 w-2 rounded-full ${col.accent}`} />
                  {col.label}
                </span>
                <span className="badge bg-white text-slate-500 dark:bg-slate-700 dark:text-slate-300">
                  {items.length}
                </span>
              </div>

              <div className="flex min-h-[60px] flex-col gap-2">
                {items.map((a) => (
                  <article
                    key={a.id}
                    draggable
                    onDragStart={() => setDragId(a.id)}
                    onDragEnd={() => {
                      setDragId(null);
                      setOverCol(null);
                    }}
                    className={`group cursor-grab rounded-xl border border-slate-200/80 bg-white p-3 shadow-soft transition active:cursor-grabbing dark:border-slate-700 dark:bg-slate-900 ${
                      dragId === a.id ? "opacity-50" : "hover:shadow-card"
                    }`}
                  >
                    <div className="flex items-start gap-1.5">
                      <GripVertical
                        size={14}
                        className="mt-0.5 shrink-0 text-slate-300 group-hover:text-slate-400 dark:text-slate-600"
                      />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {a.job?.title ?? `Job #${a.job_id}`}
                        </p>
                        {a.job?.company && (
                          <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-slate-500 dark:text-slate-400">
                            <Building2 size={11} className="shrink-0 text-brand-400" />
                            {a.job.company}
                          </p>
                        )}
                      </div>
                    </div>
                  </article>
                ))}

                {items.length === 0 && (
                  <p className="rounded-lg border border-dashed border-slate-200 py-3 text-center text-xs text-slate-400 dark:border-slate-700 dark:text-slate-600">
                    Drop here
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {showAdd && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
          onClick={() => !saving && setShowAdd(false)}
        >
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={submitAdd}
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-700 dark:bg-slate-900"
          >
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                Add a job
              </h3>
              <button
                type="button"
                onClick={() => setShowAdd(false)}
                className="rounded-lg p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">
                  Job title *
                </label>
                <input
                  autoFocus
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Backend Engineer"
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">
                  Company *
                </label>
                <input
                  value={form.company}
                  onChange={(e) => setForm({ ...form, company: e.target.value })}
                  placeholder="Acme Corp"
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-brand-500/20"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">
                    Location
                  </label>
                  <input
                    value={form.location}
                    onChange={(e) => setForm({ ...form, location: e.target.value })}
                    placeholder="Remote · India"
                    className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-brand-500/20"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">
                    Status
                  </label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-brand-500/20"
                  >
                    {COLUMNS.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">
                  Job URL
                </label>
                <input
                  value={form.url}
                  onChange={(e) => setForm({ ...form, url: e.target.value })}
                  placeholder="https://…"
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">
                  Notes
                </label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                  placeholder="Referral from…, recruiter name, etc."
                  className="w-full resize-none rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-brand-500/20"
                />
              </div>
            </div>

            {error && (
              <p className="mt-3 text-xs font-medium text-rose-500">{error}</p>
            )}

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAdd(false)}
                className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-600 disabled:opacity-60"
              >
                {saving ? "Adding…" : "Add job"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
