import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";

import Login from "./pages/Login";
import Landing from "./pages/Landing";
import Copilot from "./pages/Copilot";
import AutoCopilot from "./pages/AutoCopilot";
import Dashboard from "./pages/Dashboard";
import ResumeUpload from "./pages/ResumeUpload";
import JobSearch from "./pages/JobSearch";
import Recommendations from "./pages/Recommendations";
import ATSAnalysis from "./pages/ATSAnalysis";
import KeywordGap from "./pages/KeywordGap";
import CoverLetter from "./pages/CoverLetter";
import Tracker from "./pages/Tracker";
import Roadmap from "./pages/Roadmap";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-400">Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

function Shell({ children }) {
  return (
    <div className="flex h-screen flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <div className="mx-auto max-w-7xl animate-fade-in-up">{children}</div>
        </main>
      </div>
    </div>
  );
}

const protectedRoutes = [
  ["/", <Copilot />],
  ["/auto", <AutoCopilot />],
  ["/dashboard", <Dashboard />],
  ["/resume", <ResumeUpload />],
  ["/jobs", <JobSearch />],
  ["/recommendations", <Recommendations />],
  ["/ats", <ATSAnalysis />],
  ["/keywords", <KeywordGap />],
  ["/cover-letter", <CoverLetter />],
  ["/tracker", <Tracker />],
  ["/roadmap", <Roadmap />],
];

export default function App() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
      <Route path="/welcome" element={<Landing />} />
      {protectedRoutes.map(([path, el]) => (
        <Route
          key={path}
          path={path}
          element={
            <Protected>
              <Shell>{el}</Shell>
            </Protected>
          }
        />
      ))}
    </Routes>
  );
}
