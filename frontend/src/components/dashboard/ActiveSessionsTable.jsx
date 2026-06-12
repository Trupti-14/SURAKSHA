import { getRiskProfile } from "../../lib/store.js";

function riskClassName(score) {
  if (score <= 30) {
    return "bg-emerald-500/[0.12] text-emerald-300 ring-emerald-500/25";
  }

  if (score <= 70) {
    return "bg-amber-500/[0.12] text-amber-300 ring-amber-500/25";
  }

  return "bg-red-500/[0.12] text-red-300 ring-red-500/25";
}

function statusClassName(tone) {
  if (tone === "emerald") {
    return "bg-emerald-500/10 text-emerald-300 ring-emerald-500/20";
  }

  if (tone === "amber") {
    return "bg-amber-500/10 text-amber-300 ring-amber-500/20";
  }

  return "bg-red-500/10 text-red-300 ring-red-500/20";
}

export default function ActiveSessionsTable({
  sessions,
  selectedSessionId,
  onSelectSession,
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 px-5 py-4">
        <div>
          <h2 className="text-base font-semibold tracking-wide text-slate-50">
            Active Sessions
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Select a customer session to inspect trust, MFA, and trigger state.
          </p>
        </div>
        <span className="rounded-full bg-sky-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-sky-300 ring-1 ring-sky-500/20">
          Mock session feed
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-left">
          <thead className="bg-[#0a1627] text-slate-400">
            <tr>
              {[
                "Customer",
                "Session",
                "Device",
                "Location",
                "Risk",
                "Status",
                "MFA",
                "Blocked",
                "Last Seen",
              ].map((heading) => (
                <th
                  key={heading}
                  className="border-b border-slate-800/80 px-4 py-3 text-[11px] font-semibold uppercase tracking-wider"
                >
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => {
              const selected = session.sessionId === selectedSessionId;
              const riskProfile = getRiskProfile(session.riskScore);

              return (
                <tr
                  key={session.sessionId}
                  onClick={() => onSelectSession(session.sessionId)}
                  className={`cursor-pointer border-b border-slate-800/60 transition-colors ${
                    selected
                      ? "bg-sky-500/10 shadow-[inset_3px_0_0_#38bdf8]"
                      : "bg-[#0f1b2d] hover:bg-slate-800/45"
                  }`}
                >
                  <td className="px-4 py-2.5">
                    <p className="text-sm font-semibold text-slate-100">
                      {session.name}
                    </p>
                    <p className="mt-0.5 text-[11px] text-slate-500">
                      {session.customerId}
                    </p>
                  </td>
                  <td className="px-4 py-2.5 text-xs font-medium text-slate-300">
                    {session.sessionId}
                  </td>
                  <td className="max-w-[190px] px-4 py-2.5 text-xs leading-5 text-slate-400">
                    {session.device}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-slate-400">
                    {session.location}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex min-w-12 justify-center rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums ring-1 ${riskClassName(
                        session.riskScore
                      )}`}
                    >
                      {session.riskScore}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ring-1 ${statusClassName(
                        riskProfile.tone
                      )}`}
                    >
                      {riskProfile.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs font-medium">
                    <span
                      className={
                        session.requiresMfa
                          ? "text-amber-300"
                          : "text-emerald-300"
                      }
                    >
                      {session.requiresMfa ? "Required" : "Clear"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs font-medium">
                    <span
                      className={
                        session.sessionBlocked
                          ? "text-red-300"
                          : "text-slate-400"
                      }
                    >
                      {session.sessionBlocked ? "Blocked" : "Open"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs tabular-nums text-slate-400">
                    {session.lastSeen}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
