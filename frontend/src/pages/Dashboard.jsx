import { useEffect, useState } from "react";
import { Briefcase, TrendingUp, Award, GitBranch } from "lucide-react";
import { api } from "../lib/api";
import AnalyticsCharts from "../components/AnalyticsCharts";

function Stat({ label, value, icon: Icon, gradient }) {
  return (
    <div className="card card-hover relative overflow-hidden">
      <div
        className={`absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-20 blur-xl ${gradient}`}
      />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-300">{label}</p>
          <p className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-white">{value}</p>
        </div>
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl text-white shadow-soft ${gradient}`}
        >
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.analytics().then(setData).catch(() => setData(null));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="section-title">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
          Your job hunt at a glance.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Applications"
          value={data?.total_applications ?? 0}
          icon={Briefcase}
          gradient="bg-brand-600"
        />
        <Stat
          label="Interview Rate"
          value={`${Math.round((data?.interview_rate ?? 0) * 100)}%`}
          icon={TrendingUp}
          gradient="bg-emerald-600"
        />
        <Stat
          label="Offer Rate"
          value={`${Math.round((data?.offer_rate ?? 0) * 100)}%`}
          icon={Award}
          gradient="bg-amber-600"
        />
        <Stat
          label="In Pipeline"
          value={Object.values(data?.by_status ?? {}).reduce((a, b) => a + b, 0)}
          icon={GitBranch}
          gradient="bg-violet-600"
        />
      </div>
      {data && <AnalyticsCharts data={data} />}
    </div>
  );
}
