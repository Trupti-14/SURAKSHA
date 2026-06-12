import { getRiskProfile } from "../../lib/store.js";

function statusClassName(tone) {
  if (tone === "emerald") {
    return "border-emerald-500/25 bg-emerald-500/10 text-emerald-300";
  }

  if (tone === "amber") {
    return "border-amber-500/25 bg-amber-500/10 text-amber-300";
  }

  return "border-red-500/25 bg-red-500/10 text-red-300";
}

export default function SessionStatus({ session }) {
  const riskProfile = getRiskProfile(session.riskScore);

  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)] lg:col-span-5">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Session Status
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Risk decision for {session.name}
        </p>
      </div>

      <div className="space-y-3.5 px-5 py-4">
        <div
          className={`rounded-xl border px-4 py-3.5 ${statusClassName(
            riskProfile.tone
          )}`}
        >
          <p className="text-[11px] font-semibold uppercase tracking-wider">
            {riskProfile.status}
          </p>
          <p className="mt-1 text-xl font-semibold text-slate-50">
            {riskProfile.decision}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "Customer ID", value: session.customerId },
            { label: "Session ID", value: session.sessionId },
            { label: "Device", value: session.device },
            { label: "Location", value: session.location },
            { label: "Requires MFA", value: session.requiresMfa ? "Yes" : "No" },
            {
              label: "Session Blocked",
              value: session.sessionBlocked ? "Yes" : "No",
            },
          ].map((item) => (
            <div key={item.label} className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                {item.label}
              </p>
              <p className="mt-1 text-xs font-medium leading-relaxed text-slate-200">
                {item.value}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
