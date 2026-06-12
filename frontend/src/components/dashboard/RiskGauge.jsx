import { getRiskProfile } from "../../lib/store.js";

export default function RiskGauge({ session }) {
  const score = session.riskScore;
  const riskProfile = getRiskProfile(score);
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const offset = circumference - progress;

  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)] lg:col-span-4">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Session Risk Gauge
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          {session.customerId} - {session.sessionId}
        </p>
      </div>

      <div className="flex flex-col items-center px-5 py-5">
        <div className="relative flex items-center justify-center">
          <svg width="136" height="136" className="-rotate-90">
            <circle
              cx="68"
              cy="68"
              r={radius}
              fill="none"
              stroke="#1e293b"
              strokeWidth="12"
            />
            <circle
              cx="68"
              cy="68"
              r={radius}
              fill="none"
              stroke={riskProfile.color}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-500 ease-out"
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-semibold tabular-nums tracking-tight text-slate-50">
              {Math.round(score)}
            </span>
            <span
              className="mt-1 text-[11px] font-semibold uppercase tracking-widest"
              style={{ color: riskProfile.color }}
            >
              {riskProfile.label}
            </span>
          </div>
        </div>

        <div className="mt-5 w-full space-y-2">
          <div className="flex justify-between text-[11px] font-medium text-slate-500">
            <span>0</span>
            <span>Low - Medium - High</span>
            <span>100</span>
          </div>

          <div className="flex h-2 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full w-[30%] bg-emerald-400/80" />
            <div className="h-full w-[40%] bg-amber-400/80" />
            <div className="h-full w-[30%] bg-red-500/80" />
          </div>

          <div className="flex justify-between text-[10px] font-medium text-slate-500">
            <span>0-30 Normal</span>
            <span>31-70 MFA</span>
            <span>71-100 Block</span>
          </div>
        </div>
      </div>
    </section>
  );
}
