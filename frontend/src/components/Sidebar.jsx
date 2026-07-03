import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  Search,
  Target,
  ListChecks,
  FileText,
  Mail,
  Map,
  KanbanSquare,
  Sparkles,
  Zap,
} from "lucide-react";

const links = [
  { to: "/", label: "AI Assistant", icon: Sparkles, end: true },
  { to: "/auto", label: "Autopilot", icon: Zap },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/resume", label: "Resume Upload", icon: Upload },
  { to: "/jobs", label: "Job Search", icon: Search },
  { to: "/recommendations", label: "Recommendations", icon: Target },
  { to: "/ats", label: "ATS Analysis", icon: ListChecks },
  { to: "/keywords", label: "Keyword Gap", icon: FileText },
  { to: "/cover-letter", label: "Cover Letter", icon: Mail },
  { to: "/tracker", label: "Application Tracker", icon: KanbanSquare },
  { to: "/roadmap", label: "Career Roadmap", icon: Map },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 md:block">
      <nav className="flex flex-col gap-1.5 p-4">
        <p className="px-3 pb-2 pt-1 text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          Workspace
        </p>
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-200 ${
                isActive
                  ? "bg-brand-600 text-white shadow-soft"
                  : "text-slate-600 hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={18}
                  className={
                    isActive
                      ? "text-white"
                      : "text-slate-400 transition group-hover:text-brand-600 dark:text-slate-400 dark:group-hover:text-white"
                  }
                />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
