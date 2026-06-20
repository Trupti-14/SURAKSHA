const steps = ["Add Circular", "Analyze", "Review Gaps", "Assign Actions", "Verify Evidence"];

export default function AgentWorkflow({ analysisReady = false }) {
  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] px-4 py-3 shadow-[0_18px_44px_rgba(2,6,23,0.22)]">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-slate-50">
            Review Progress
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Follow the circular from intake to evidence verification.
          </p>
        </div>

        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2 lg:justify-end">
          {steps.map((step, index) => {
            const complete = analysisReady && index < 4;
            const active = (!analysisReady && index === 0) || (analysisReady && index === 4);
            const pending = !complete && !active;

            return (
              <div key={step} className="flex items-center gap-2">
                <div
                  className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${
                    complete
                      ? "border-emerald-400/30 bg-emerald-500/[0.10] text-emerald-200"
                      : active
                        ? "border-sky-400/35 bg-sky-500/[0.12] text-sky-200"
                        : "border-slate-800 bg-[#0a1627] text-slate-500"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      complete
                        ? "bg-emerald-300"
                        : active
                          ? "bg-sky-300"
                          : "bg-slate-600"
                    }`}
                  />
                  <span>{step}</span>
                  {pending && (
                    <span className="text-[10px] font-medium uppercase tracking-wider text-slate-600">
                      Pending
                    </span>
                  )}
                </div>
                {index < steps.length - 1 && (
                  <span className="hidden text-slate-700 sm:inline">/</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
