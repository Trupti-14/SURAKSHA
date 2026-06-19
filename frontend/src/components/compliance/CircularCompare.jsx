export default function CircularCompare({ circular }) {
  if (!circular) {
    return null;
  }

  const detectedGap =
    circular.detected_gap ??
    "Existing controls do not fully capture the new frequency, evidence retention, owner accountability, and regulator-ready proof requirements.";

  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Circular Delta Check
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Existing policy compared against the selected regulatory circular.
        </p>
      </div>

      <div className="grid gap-4 p-4 lg:grid-cols-3">
        <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Old Policy
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {circular.old_policy}
          </p>
        </div>

        <div className="rounded-lg border border-sky-400/25 bg-sky-500/[0.08] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-sky-300">
            New Circular Requirement
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-100">
            {circular.new_policy}
          </p>
        </div>

        <div className="rounded-lg border border-amber-400/25 bg-amber-500/[0.08] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">
            Detected Gap
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-100">
            {detectedGap}
          </p>
        </div>
      </div>
    </section>
  );
}
