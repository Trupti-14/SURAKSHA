function severityClassName(severity) {
  if (severity === "LOW") {
    return "bg-emerald-500/[0.12] text-emerald-300 ring-emerald-500/25";
  }

  if (severity === "MEDIUM") {
    return "bg-amber-500/[0.12] text-amber-300 ring-amber-500/25";
  }

  return "bg-red-500/[0.12] text-red-300 ring-red-500/25";
}

export default function TriggerList({ session }) {
  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)] lg:col-span-3">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Behavioral Triggers
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Customer-scoped telemetry anomalies
        </p>
      </div>

      <div className="max-h-[322px] overflow-y-auto px-4 py-4">
        <ul className="space-y-2.5">
          {session.triggers.map((trigger) => (
            <li
              key={trigger.id}
              className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-3"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-[10px] font-medium tabular-nums text-slate-500">
                  {trigger.timestamp}
                </p>
                <span
                  className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ring-1 ${severityClassName(
                    trigger.severity
                  )}`}
                >
                  {trigger.severity}
                </span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {trigger.anomaly}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
