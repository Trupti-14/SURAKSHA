export default function TelemetryPanel({ telemetry }) {
  const metrics = [
    {
      label: "Total Keystrokes",
      value: telemetry.totalKeystrokes,
    },
    {
      label: "Keydown Events",
      value: telemetry.keydownCount,
    },
    {
      label: "Keyup Events",
      value: telemetry.keyupCount,
    },
    {
      label: "Mouse Movements",
      value: telemetry.mouseMoveCount,
    },
    {
      label: "Mouse Clicks",
      value: telemetry.clickCount,
    },
    {
      label: "Idle Time",
      value: `${telemetry.idleSeconds}s`,
    },
  ];

  return (
    <section className="rounded-lg border border-slate-800/80 bg-[#0f141c]">
      <div className="border-b border-slate-800/80 px-5 py-3.5">
        <h2 className="text-sm font-medium text-slate-100">
          Behavioral Analytics Engine
        </h2>
        <p className="mt-0.5 text-xs text-slate-500">
          Continuous behavioral signal collection for adaptive identity verification
        </p>
      </div>

      <div className="grid grid-cols-2 divide-x divide-y divide-slate-800/80 text-center sm:grid-cols-3 lg:grid-cols-6">
        {metrics.map((metric) => (
          <div key={metric.label} className="px-4 py-4">
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              {metric.label}
            </p>
            <p className="mt-1 text-sm font-medium tabular-nums text-slate-200">
              {metric.value}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
