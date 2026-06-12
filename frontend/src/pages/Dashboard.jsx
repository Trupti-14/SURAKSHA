import ActiveSessionsTable from "../components/dashboard/ActiveSessionsTable.jsx";
import RiskGauge from "../components/dashboard/RiskGauge.jsx";
import SessionStatus from "../components/dashboard/SessionStatus.jsx";
import TriggerList from "../components/dashboard/TriggerList.jsx";
import Layout from "../components/ui/Layout.jsx";
import { integrationSlots } from "../lib/mock-data.js";
import {
  getDashboardMetrics,
  getRiskProfile,
  getSelectedSession,
  useVanguard,
} from "../lib/store.js";

function MetricCard({ label, value, detail, tone = "neutral" }) {
  const toneClassName = {
    neutral: "bg-slate-800/70 text-slate-300 ring-slate-700/70",
    emerald: "bg-emerald-500/[0.12] text-emerald-300 ring-emerald-500/25",
    amber: "bg-amber-500/[0.12] text-amber-300 ring-amber-500/25",
    red: "bg-red-500/[0.12] text-red-300 ring-red-500/25",
  };

  return (
    <div className="min-h-[104px] rounded-xl border border-slate-800/80 bg-[#0f1b2d] p-4 shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-2xl font-semibold tabular-nums tracking-tight text-slate-50 xl:text-3xl">
          {value}
        </p>
        <span
          className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ring-1 ${toneClassName[tone]}`}
        >
          {detail}
        </span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { state, dispatch } = useVanguard();
  const sessions = state.activeSessions;
  const selectedSession = getSelectedSession(state);
  const metrics = getDashboardMetrics(sessions);
  const selectedRiskProfile = getRiskProfile(selectedSession.riskScore);

  return (
    <Layout selectedSession={selectedSession}>
      <section className="rounded-2xl border border-slate-800/80 bg-[#0d1a2c] p-4 shadow-[0_18px_50px_rgba(2,6,23,0.3)] xl:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">
              Session-wise Trust Command
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-50 xl:text-2xl">
              {selectedSession.name}
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Current selection: {selectedSession.customerId} -{" "}
              {selectedSession.sessionId}. The risk gauge, session decision,
              and behavioral triggers below update when an officer selects a
              different active customer session.
            </p>
          </div>

          <div
            className="rounded-xl px-4 py-3 shadow-[0_12px_30px_rgba(2,6,23,0.28)] ring-1 ring-white/10"
            style={{
              backgroundColor: `${selectedRiskProfile.color}22`,
              color: selectedRiskProfile.color,
            }}
          >
            <p className="text-[11px] font-semibold uppercase tracking-wider">
              {selectedRiskProfile.label}
            </p>
            <p className="mt-1 text-xl font-semibold text-slate-50">
              {selectedRiskProfile.decision}
            </p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3.5 xl:grid-cols-4">
        <MetricCard
          label="Active Sessions"
          value={metrics.activeSessions}
          detail="Live"
        />
        <MetricCard
          label="MFA Required"
          value={metrics.mfaRequired}
          detail="Step-up"
          tone="amber"
        />
        <MetricCard
          label="Blocked Sessions"
          value={metrics.blockedSessions}
          detail="Critical"
          tone={metrics.blockedSessions > 0 ? "red" : "emerald"}
        />
        <MetricCard
          label="Average Risk"
          value={metrics.averageRisk}
          detail="Fleet"
          tone={
            metrics.averageRisk > 70
              ? "red"
              : metrics.averageRisk > 30
              ? "amber"
              : "emerald"
          }
        />
      </section>

      <ActiveSessionsTable
        sessions={sessions}
        selectedSessionId={selectedSession.sessionId}
        onSelectSession={(sessionId) =>
          dispatch({ type: "SELECT_SESSION", payload: sessionId })
        }
      />

      <section className="grid gap-3.5 lg:grid-cols-12">
        <RiskGauge session={selectedSession} />
        <SessionStatus session={selectedSession} />
        <TriggerList session={selectedSession} />
      </section>

      <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
        <div className="border-b border-slate-800/80 px-5 py-4">
          <h2 className="text-base font-semibold tracking-wide text-slate-50">
            Integration Slots
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Placeholder contracts for teammate-owned modules. No future module
            logic is implemented in this dashboard foundation.
          </p>
        </div>

        <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
          {integrationSlots.map((slot) => (
            <div
              key={slot.title}
              className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4"
            >
              <p className="text-sm font-semibold tracking-wide text-sky-300">
                {slot.title}
              </p>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                {slot.description}
              </p>
            </div>
          ))}
        </div>
      </section>
    </Layout>
  );
}
