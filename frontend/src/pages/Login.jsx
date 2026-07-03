import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, register } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("demo@talenttrail.dev");
  const [password, setPassword] = useState("demo1234");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, name);
      nav("/");
    } catch (err) {
      setError(err?.response?.data?.detail ?? "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Left brand panel */}
      <div className="relative hidden w-1/2 overflow-hidden bg-brand-gradient lg:flex lg:flex-col lg:justify-between lg:p-12 lg:text-white">
        <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-24 -left-16 h-96 w-96 rounded-full bg-fuchsia-400/20 blur-3xl" />
        <div className="relative flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur">
            <Bot size={22} />
          </div>
          <span className="text-lg font-bold">TalentTrail</span>
        </div>
        <div className="relative animate-float">
          <Sparkles className="mb-4 h-10 w-10 text-white/80" />
          <h2 className="text-4xl font-extrabold leading-tight">
            Your autonomous
            <br /> career copilot.
          </h2>
          <p className="mt-4 max-w-md text-white/80">
            Discover jobs, optimise your resume, beat the ATS, and track every
            application — all powered by a multi-agent AI pipeline.
          </p>
        </div>
        <div className="relative flex gap-6 text-sm text-white/70">
          <span>✦ Resume parsing</span>
          <span>✦ ATS scoring</span>
          <span>✦ Smart matching</span>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <div className="card glass w-full max-w-md animate-fade-in-up !p-8 shadow-card">
          <div className="mb-6 flex items-center gap-2 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 shadow-soft">
              <Bot className="text-white" size={20} />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">TalentTrail</h1>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="mb-6 mt-1 text-sm text-slate-500 dark:text-slate-300">
            {mode === "login"
              ? "Sign in to continue your job hunt."
              : "Start landing interviews faster."}
          </p>
          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <input
                className="input"
                placeholder="Full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            )}
            <input
              className="input"
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              className="input"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {error && (
              <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-300">
                {error}
              </p>
            )}
            <button className="btn w-full py-3 text-base" disabled={busy}>
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
          <p className="mt-5 text-center text-sm text-slate-500 dark:text-slate-300">
            {mode === "login" ? "No account?" : "Have an account?"}{" "}
            <button
              className="font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-300 dark:hover:text-brand-200"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
            >
              {mode === "login" ? "Register" : "Sign in"}
            </button>
          </p>
          <div className="mt-5 rounded-xl border border-dashed border-brand-200 bg-brand-50/60 px-4 py-3 text-center text-xs text-slate-500 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-slate-300">
            <span className="font-semibold text-brand-700 dark:text-brand-300">Demo account</span>
            <br />
            demo@talenttrail.dev · demo1234
          </div>
        </div>
      </div>
    </div>
  );
}
