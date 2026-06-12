import { useState } from "react";
import { useNavigate } from "react-router-dom";

const operatorRoles = [
  "Fraud Analyst",
  "Security Operations",
  "Compliance Officer",
  "Underwriter",
  "Security Administrator",
];

const securityIndicators = [
  "Behavioral Engine Online",
  "MFA Gateway Active",
  "Compliance Fabric Synced",
  "Redis Session Layer Ready",
];

function VanguardLogo() {
  return (
    <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[#0078d4]/20 ring-1 ring-[#0078d4]/40">
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5 text-[#4da3ff]"
        fill="currentColor"
      >
        <path d="M12 2L3 7v10l9 5 9-5V7l-9-5zm0 2.18l6.9 3.83L12 11.84 5.1 8.01 12 4.18zM5 9.38l6 3.33v6.64l-6-3.33V9.38zm8 10.97v-6.64l6-3.33v6.64l-6 3.33z" />
      </svg>
    </div>
  );
}

function StatusDot() {
  return (
    <span className="mt-1 inline-block h-2 w-2 shrink-0 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
  );
}

export default function Login() {
  const navigate = useNavigate();
  const [employeeId, setEmployeeId] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const nextErrors = {};

    if (!employeeId.trim()) {
      nextErrors.employeeId = "Employee ID is required.";
    }

    if (!password) {
      nextErrors.password = "Secure Password is required.";
    }

    if (!role) {
      nextErrors.role = "Operator role is required.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleLogin = (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    navigate("/dashboard");
  };

  const clearFieldError = (field) => {
    setErrors((currentErrors) => {
      const nextErrors = { ...currentErrors };
      delete nextErrors[field];
      return nextErrors;
    });
  };

  return (
    <div className="min-h-screen bg-[#080b10] text-slate-200">
      <div className="grid min-h-screen lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,0.7fr)]">
        <section className="hidden border-r border-slate-800/80 bg-[#0a0e14] lg:flex lg:flex-col">
          <div className="flex items-center justify-between border-b border-slate-800/80 px-10 py-6">
            <div className="flex items-center gap-3">
              <VanguardLogo />
              <div>
                <h1 className="text-lg font-semibold tracking-wide text-slate-100">
                  Vanguard
                </h1>
                <p className="text-xs text-slate-500">
                  Canara Bank Security Operations Console
                </p>
              </div>
            </div>

            <div className="rounded-md border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider text-emerald-300">
              Restricted Console
            </div>
          </div>

          <div className="flex flex-1 flex-col justify-between px-10 py-10">
            <div className="max-w-2xl">
              <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.2em] text-[#4da3ff]">
                Authorized Operator Access
              </p>
              <h2 className="max-w-xl text-3xl font-semibold leading-tight text-slate-100">
                Unified Security, Integrity & Agentic Compliance Fabric
              </h2>
              <p className="mt-5 max-w-xl text-sm leading-relaxed text-slate-400">
                Internal command access for fraud operations, security
                monitoring, compliance review, underwriting integrity, and
                privileged security administration.
              </p>

              <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-2">
                {securityIndicators.map((indicator) => (
                  <div
                    key={indicator}
                    className="rounded-md border border-slate-800 bg-slate-900/40 px-3.5 py-3"
                  >
                    <div className="flex items-start gap-2.5">
                      <StatusDot />
                      <p className="text-xs font-medium text-slate-300">
                        {indicator}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid max-w-2xl grid-cols-3 divide-x divide-slate-800/80 border-y border-slate-800/80 text-center">
              {[
                { label: "Access Model", value: "Zero Trust" },
                { label: "Audit Mode", value: "Continuous" },
                { label: "Session Risk", value: "Adaptive" },
              ].map((item) => (
                <div key={item.label} className="px-4 py-4">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
                    {item.label}
                  </p>
                  <p className="mt-1 text-xs font-medium text-slate-200">
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <main className="flex items-center justify-center px-5 py-8 sm:px-8">
          <div className="w-full max-w-md">
            <div className="mb-7 flex items-center gap-3 lg:hidden">
              <VanguardLogo />
              <div>
                <h1 className="text-lg font-semibold tracking-wide text-slate-100">
                  Vanguard
                </h1>
                <p className="text-xs text-slate-500">
                  Unified Security, Integrity & Agentic Compliance Fabric
                </p>
              </div>
            </div>

            <section className="rounded-lg border border-slate-800/80 bg-[#0f141c] shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
              <div className="border-b border-slate-800/80 px-6 py-5">
                <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-[#4da3ff]">
                  Authorized Operator Access
                </p>
                <h2 className="mt-2 text-xl font-semibold text-slate-100">
                  Vanguard
                </h2>
                <p className="mt-1 text-sm leading-relaxed text-slate-500">
                  Unified Security, Integrity & Agentic Compliance Fabric
                </p>
              </div>

              <form onSubmit={handleLogin} className="space-y-5 px-6 py-6">
                <div>
                  <label
                    htmlFor="employeeId"
                    className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-slate-500"
                  >
                    Employee ID
                  </label>
                  <input
                    id="employeeId"
                    type="text"
                    autoComplete="username"
                    value={employeeId}
                    onChange={(event) => {
                      setEmployeeId(event.target.value);
                      clearFieldError("employeeId");
                    }}
                    placeholder="CB-SEC-1024"
                    aria-invalid={Boolean(errors.employeeId)}
                    aria-describedby={
                      errors.employeeId ? "employeeId-error" : undefined
                    }
                    className={`w-full rounded-md border bg-[#0a0e14] px-3.5 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 outline-none transition-colors focus:border-[#0078d4]/60 focus:ring-1 focus:ring-[#0078d4]/30 ${
                      errors.employeeId
                        ? "border-red-500/60"
                        : "border-slate-700/80"
                    }`}
                  />
                  {errors.employeeId && (
                    <p
                      id="employeeId-error"
                      className="mt-1.5 text-xs text-red-300"
                    >
                      {errors.employeeId}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-slate-500"
                  >
                    Secure Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => {
                      setPassword(event.target.value);
                      clearFieldError("password");
                    }}
                    placeholder="Enter secure password"
                    aria-invalid={Boolean(errors.password)}
                    aria-describedby={
                      errors.password ? "password-error" : undefined
                    }
                    className={`w-full rounded-md border bg-[#0a0e14] px-3.5 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 outline-none transition-colors focus:border-[#0078d4]/60 focus:ring-1 focus:ring-[#0078d4]/30 ${
                      errors.password
                        ? "border-red-500/60"
                        : "border-slate-700/80"
                    }`}
                  />
                  {errors.password && (
                    <p
                      id="password-error"
                      className="mt-1.5 text-xs text-red-300"
                    >
                      {errors.password}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="role"
                    className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-slate-500"
                  >
                    Operator Role
                  </label>
                  <select
                    id="role"
                    value={role}
                    onChange={(event) => {
                      setRole(event.target.value);
                      clearFieldError("role");
                    }}
                    aria-invalid={Boolean(errors.role)}
                    aria-describedby={errors.role ? "role-error" : undefined}
                    className={`w-full rounded-md border bg-[#0a0e14] px-3.5 py-2.5 text-sm text-slate-100 outline-none transition-colors focus:border-[#0078d4]/60 focus:ring-1 focus:ring-[#0078d4]/30 ${
                      errors.role ? "border-red-500/60" : "border-slate-700/80"
                    }`}
                  >
                    <option value="">Select authorized role</option>
                    {operatorRoles.map((operatorRole) => (
                      <option key={operatorRole} value={operatorRole}>
                        {operatorRole}
                      </option>
                    ))}
                  </select>
                  {errors.role && (
                    <p id="role-error" className="mt-1.5 text-xs text-red-300">
                      {errors.role}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  className="w-full rounded-md bg-[#0078d4] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#106ebe] focus:outline-none focus:ring-2 focus:ring-[#0078d4]/40"
                >
                  Enter Security Console
                </button>
              </form>

              <div className="border-t border-slate-800/80 px-6 py-5">
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {securityIndicators.map((indicator) => (
                    <div
                      key={indicator}
                      className="flex items-start gap-2.5 rounded-md border border-slate-800 bg-slate-900/30 px-3 py-2.5"
                    >
                      <StatusDot />
                      <p className="text-[11px] font-medium text-slate-400">
                        {indicator}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="mt-4 rounded-md border border-amber-500/20 bg-amber-500/5 px-4 py-3.5">
              <div className="flex items-start gap-2.5">
                <svg
                  viewBox="0 0 24 24"
                  className="mt-0.5 h-4 w-4 shrink-0 text-amber-300"
                  fill="currentColor"
                >
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 4.5a2 2 0 0 1 2 2v1h-4V7.5a2 2 0 0 1 2-2zm0 7a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z" />
                </svg>
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-wider text-amber-200">
                    Operator Session Notice
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-amber-100/70">
                    Access is restricted to authorized Canara Bank personnel.
                    All operator actions are logged, risk-scored, and subject
                    to audit review.
                  </p>
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
