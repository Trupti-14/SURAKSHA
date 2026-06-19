import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { getRiskProfile } from "../../lib/store.js";

function formatTime(date) {
  return date.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function StatusDot({ tone = "emerald" }) {
  const tones = {
    emerald: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.45)]",
    amber: "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.4)]",
    red: "bg-red-400 shadow-[0_0_10px_rgba(248,113,113,0.42)]",
  };

  return <span className={`inline-block h-2 w-2 rounded-full ${tones[tone]}`} />;
}

function NavIcon({ label }) {
  const icons = {
    "Trust Dashboard": (
      <path d="M12 2 4 5.5v5.9c0 4.9 3.4 9.4 8 10.6 4.6-1.2 8-5.7 8-10.6V5.5L12 2Zm0 3.1 5 2.2v4.1c0 3.3-2 6.5-5 7.6-3-1.1-5-4.3-5-7.6V7.3l5-2.2Z" />
    ),
    "Document Forensics": (
      <path d="M7 3h7l4 4v14H7V3Zm7 1.8V8h3.2L14 4.8ZM9 11h6v1.5H9V11Zm0 4h6v1.5H9V15Z" />
    ),
    Compliance: (
      <path d="M6 3h12v18H6V3Zm2 3v12h8V6H8Zm1.2 3h5.6v1.4H9.2V9Zm0 3h5.6v1.4H9.2V12Zm0 3h3.8v1.4H9.2V15Z" />
    ),
    "Security/Admin": (
      <path d="M12 2a4 4 0 0 1 4 4v2h2v13H6V8h2V6a4 4 0 0 1 4-4Zm-2 6h4V6a2 2 0 0 0-4 0v2Zm2 4.5a1.6 1.6 0 0 0-.8 3v2h1.6v-2a1.6 1.6 0 0 0-.8-3Z" />
    ),
  };

  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="currentColor">
      {icons[label]}
    </svg>
  );
}

const routeHeaders = {
  "/dashboard": {
    title: "Core Trust Dashboard",
    subtitle: "Session-wise identity risk, MFA posture, and behavioral triggers",
  },
  "/forensics": {
    title: "Document Forensics",
    subtitle: "Digital document authenticity, ELA heatmap, and metadata analysis",
  },
  "/compliance": {
    title: "Regulatory Compliance Command Center",
    subtitle: "Offline RBI circular tracking, MAP generation, and evidence verification",
  },
  "/admin": {
    title: "Security & Administration",
    subtitle: "Panic PIN, quorum control, and privacy redaction operations",
  },
};

export default function Layout({ children, selectedSession }) {
  const { pathname } = useLocation();
  const [currentTime, setCurrentTime] = useState(() => new Date());
  const riskProfile = selectedSession
    ? getRiskProfile(selectedSession.riskScore)
    : getRiskProfile(0);
  const routeKey =
    Object.keys(routeHeaders).find(
      (path) => pathname === path || pathname.startsWith(`${path}/`),
    ) ?? "/dashboard";
  const header = routeHeaders[routeKey];

  const navItems = [
    { label: "Trust Dashboard", path: "/dashboard" },
    { label: "Document Forensics", path: "/forensics" },
    { label: "Compliance", path: "/compliance" },
    { label: "Security/Admin", path: "/admin" },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-[#07111f] text-slate-200">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-800/80 bg-[#091527] lg:flex">
        <div className="border-b border-slate-800/80 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/[0.15] ring-1 ring-sky-400/30">
              <svg
                viewBox="0 0 24 24"
                className="h-4 w-4 text-sky-300"
                fill="currentColor"
              >
                <path d="M12 2L3 7v10l9 5 9-5V7l-9-5zm0 2.18l6.9 3.83L12 11.84 5.1 8.01 12 4.18zM5 9.38l6 3.33v6.64l-6-3.33V9.38zm8 10.97v-6.64l6-3.33v6.64l-6 3.33z" />
              </svg>
            </div>

            <div>
              <p className="text-base font-semibold tracking-wide text-slate-50">
                Vanguard
              </p>
              <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
                Trust Command Center
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-sky-500/[0.12] text-sky-200 ring-1 ring-sky-400/20"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100"
                }`
              }
            >
              <NavIcon label={item.label} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-800/80 p-3.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Environment
          </p>
          <p className="mt-1 text-xs font-medium text-slate-300">
            Production - Canara Bank SOC
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">v2.14.0-foundation</p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 bg-[#091527]/95 px-5 py-3.5 backdrop-blur">
          <div>
            <h1 className="text-base font-semibold tracking-wide text-slate-50">
              {header.title}
            </h1>
            <p className="text-xs text-slate-500">{header.subtitle}</p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {[
              { label: "Console Online", tone: "emerald" },
              { label: "Redis Ready", tone: "emerald" },
              { label: "Behavioral Engine", tone: riskProfile.tone },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 rounded-full border border-slate-700/70 bg-slate-900/50 px-3 py-1.5 text-xs font-medium text-slate-300"
              >
                <StatusDot tone={item.tone} />
                <span>{item.label}</span>
              </div>
            ))}
            <div className="rounded-full border border-slate-700/70 bg-slate-900/50 px-3 py-1.5 text-[11px] font-medium tabular-nums text-slate-300">
              {formatTime(currentTime)} UTC
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 xl:p-5">
          <div className="mx-auto w-full max-w-[1600px] space-y-3.5">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
