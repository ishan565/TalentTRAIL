import { Link } from "react-router-dom";
import { Bot, ArrowRight, Sparkles } from "lucide-react";

const features = [
  "Resume parsing & structured extraction",
  "Multi-source job discovery",
  "Semantic matching & ranking",
  "Explainable ATS scoring",
  "Missing-keyword gap analysis",
  "Tailored resume & cover letters",
  "Kanban application tracker",
  "Personalised career roadmap",
];

export default function Landing() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      <div className="absolute left-1/2 top-0 h-96 w-[40rem] -translate-x-1/2 rounded-full bg-brand-300/20 blur-3xl dark:bg-brand-600/15" />
      <div className="relative mx-auto max-w-4xl px-6 py-24 text-center">
        <div className="mx-auto mb-6 inline-flex animate-float items-center justify-center rounded-2xl bg-brand-600 p-4 shadow-soft">
          <Bot className="text-white" size={40} />
        </div>
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-white px-4 py-1.5 text-sm font-medium text-brand-700 dark:border-brand-500/30 dark:bg-slate-900 dark:text-brand-300">
          <Sparkles size={14} /> Powered by LangGraph multi-agent AI
        </div>
        <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-slate-900 dark:text-white">
          Cursor for Job Hunting
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
          An autonomous multi-agent copilot that discovers jobs, optimises your
          resume, beats the ATS, and tracks every application.
        </p>
        <Link to="/login" className="btn mt-8 px-6 py-3 text-base">
          Get started <ArrowRight size={18} />
        </Link>
        <div className="mt-16 grid gap-3 text-left sm:grid-cols-2">
          {features.map((f, i) => (
            <div
              key={f}
              className="card card-hover animate-fade-in-up flex items-center gap-3"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                <Sparkles size={16} />
              </span>
              <span className="font-medium text-slate-700 dark:text-slate-200">{f}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
