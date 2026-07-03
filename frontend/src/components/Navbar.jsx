import { useState } from "react";
import { Bot, LogOut, Moon, Sun } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getTheme, toggleTheme } from "../lib/theme";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [theme, setThemeState] = useState(getTheme());

  const onToggle = () => setThemeState(toggleTheme());

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-5 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/90">
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 shadow-soft">
          <Bot className="text-white" size={20} />
        </div>
        <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
          TalentTrail
        </span>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <button
          onClick={onToggle}
          aria-label="Toggle theme"
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:border-brand-300 hover:text-brand-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-brand-500/60 dark:hover:text-white"
        >
          {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
        </button>
        <div className="hidden items-center gap-2 rounded-full bg-slate-100 py-1.5 pl-1.5 pr-3 dark:bg-slate-800 sm:flex">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
            {(user?.email?.[0] ?? "?").toUpperCase()}
          </span>
          <span className="font-medium text-slate-600 dark:text-slate-200">
            {user?.email}
          </span>
        </div>
        <button onClick={logout} className="btn-ghost py-2">
          <LogOut size={16} /> Logout
        </button>
      </div>
    </header>
  );
}
