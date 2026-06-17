const steps = [
  {
    name: "Local Circular",
    detail: "Circular record received for compliance review.",
  },
  {
    name: "Scout Parser",
    detail: "Key obligations, deadlines, owners, and evidence needs are identified.",
  },
  {
    name: "Delta Check",
    detail: "New requirements are reviewed against existing policy expectations.",
  },
  {
    name: "MAP Generator",
    detail: "Measurable action points are generated for responsible teams.",
  },
  {
    name: "Priority Score",
    detail:
      "Priority is assigned using urgency, risk, customer impact, and deadline factors.",
  },
  {
    name: "Evidence Verify",
    detail: "Evidence submission is tracked for compliance verification.",
  },
];

export default function AgentWorkflow({ activeStep = 5 }) {
  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Compliance Review Workflow
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Tracks the circular from review to action generation, priority assessment, and evidence closure.
        </p>
      </div>

      <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-6">
        {steps.map((step, index) => {
          const completed = index < activeStep;
          const ready = index === activeStep;
          const status = completed ? "Completed" : ready ? "Ready" : "Pending";

          return (
            <div
              key={step.name}
              className={`min-h-[112px] rounded-lg border p-3 ${
                completed || ready
                  ? "border-sky-400/30 bg-sky-500/[0.10]"
                  : "border-slate-800 bg-[#0a1627]"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                    completed || ready
                      ? "bg-sky-400 text-[#06101f]"
                      : "bg-slate-800 text-slate-500"
                  }`}
                >
                  {index + 1}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  {status}
                </span>
              </div>
              <p className="mt-4 text-sm font-semibold leading-snug text-slate-100">
                {step.name}
              </p>
              <p className="mt-2 text-xs leading-5 text-slate-500">
                {step.detail}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
