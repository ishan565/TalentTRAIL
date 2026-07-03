import ApplicationBoard from "../components/ApplicationBoard";

export default function Tracker() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="section-title">Application Tracker</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Drag a card between columns to update its status. Everything fits on one
          page — no horizontal scrolling.
        </p>
      </div>
      <ApplicationBoard />
    </div>
  );
}
