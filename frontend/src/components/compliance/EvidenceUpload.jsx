import { useRef, useState } from "react";
import { verifyComplianceEvidence } from "../../lib/compliance-api.js";

const emptyChecks = {
  file_exists: false,
  allowed_type: false,
  metadata_consistent: false,
  tamper_indicators_found: false,
  content_matches_required_evidence: false,
};

function noFileResult() {
  return {
    status: "REJECTED",
    tampered: false,
    risk_score: 100,
    confidence: 1,
    file_type: "unknown",
    summary: "Evidence rejected: no file was selected.",
    findings: [
      {
        severity: "High",
        page: 1,
        location: "file header",
        reason: "No evidence file was selected for verification.",
        suggested_action: "Select a PDF, PNG, JPG/JPEG, or DOCX evidence file.",
      },
    ],
    checks: emptyChecks,
  };
}

function backendUnavailableResult(errorMessage) {
  return {
    status: "NEEDS_REVIEW",
    tampered: false,
    risk_score: 55,
    confidence: 0,
    file_type: "unknown",
    summary:
      errorMessage ??
      "Evidence could not be verified automatically. Manual compliance review is required.",
    findings: [
      {
        severity: "Medium",
        page: 1,
        location: "file header",
        reason: "The secure evidence verifier did not return a trusted result.",
        suggested_action:
          "Keep the evidence in manual review until verification is available.",
      },
    ],
    checks: {
      ...emptyChecks,
      file_exists: true,
    },
  };
}

function statusTone(status) {
  if (status === "APPROVED") {
    return {
      panel: "border-emerald-400/25 bg-emerald-500/[0.10]",
      text: "text-emerald-300",
      subtext: "text-emerald-200/80",
    };
  }

  if (status === "REJECTED") {
    return {
      panel: "border-red-400/25 bg-red-500/[0.10]",
      text: "text-red-300",
      subtext: "text-red-200/80",
    };
  }

  return {
    panel: "border-amber-400/25 bg-amber-500/[0.10]",
    text: "text-amber-300",
    subtext: "text-amber-200/80",
  };
}

function formatPercent(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "0%";
  }

  return `${Math.round(numericValue * 100)}%`;
}

function formatCheckName(name) {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export default function EvidenceUpload({
  selectedAction,
  locked = false,
  lockedMessage = "Evidence verification will be available after actions are generated.",
}) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [verificationState, setVerificationState] = useState("idle");

  const isVerifying = verificationState === "loading";

  async function handleFileChange(event) {
    if (locked) {
      return;
    }

    const file = event.target.files?.[0] ?? null;

    setFileName(file?.name ?? "");
    setError("");
    setResult(null);

    if (!file) {
      setResult(noFileResult());
      return;
    }

    setVerificationState("loading");

    const verification = await verifyComplianceEvidence({
      file,
      requiredEvidence: selectedAction?.evidence_required ?? "",
      actionId: selectedAction?.id ?? "",
    });

    if (verification?.ok === false) {
      setError(verification.error);
      setResult(backendUnavailableResult(verification.error));
      setVerificationState("idle");
      return;
    }

    setResult(verification);
    setVerificationState("idle");
  }

  const tone = statusTone(result?.status);
  const checks = result?.checks ?? emptyChecks;
  const findings = Array.isArray(result?.findings) ? result.findings : [];

  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Evidence Verification
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Upload proof for the selected action. Evidence is checked before compliance closure.
        </p>
      </div>

      <div className="space-y-4 p-4">
        <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Selected MAP
          </p>
          <p className="mt-2 text-sm font-medium leading-6 text-slate-100">
            {selectedAction?.action ?? "Evidence verification will be available after actions are generated."}
          </p>
          {selectedAction?.evidence_required && (
            <p className="mt-2 text-xs leading-5 text-slate-400">
              Required proof: {selectedAction.evidence_required}
            </p>
          )}
          {selectedAction?.id && (
            <p className="mt-2 text-xs font-semibold text-sky-300">
              {selectedAction.id}
            </p>
          )}
        </div>

        {locked ? (
          <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
            <p className="text-sm font-semibold text-slate-200">
              Evidence Locked
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {lockedMessage}
            </p>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
          <input
            ref={inputRef}
            className="hidden"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.docx,application/pdf,image/png,image/jpeg,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileChange}
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={isVerifying || locked}
            className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-semibold text-[#06101f] transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
          >
            {isVerifying ? "Verifying..." : "Upload Proof"}
          </button>
          <div>
            <p className="text-sm text-slate-300">
              {fileName || "No file selected"}
            </p>
            <p className="text-xs text-slate-500">
              Allowed types: PDF, PNG, JPG, DOCX
            </p>
          </div>
          </div>
        )}

        {!locked && isVerifying && (
          <div className="rounded-lg border border-sky-400/25 bg-sky-500/[0.08] px-4 py-3 text-sm font-medium text-sky-200">
            Verifying evidence...
          </div>
        )}

        {!locked && result && !isVerifying && (
          <div className={`rounded-lg border p-4 ${tone.panel}`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className={`text-sm font-semibold ${tone.text}`}>
                  Compliance verification status: {result.status}
                </p>
                <p className="mt-1 text-xs uppercase tracking-wider text-slate-400">
                  {String(result.file_type ?? "unknown").toUpperCase()} evidence
                  {" - "}Risk {result.risk_score ?? 0}/100
                </p>
              </div>
              <div className="text-right">
                <p className={`text-xs font-semibold uppercase tracking-wider ${tone.subtext}`}>
                  Confidence {formatPercent(result.confidence)}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  Tampered: {result.tampered ? "Yes" : "No"}
                </p>
              </div>
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-300">
              {result.summary}
            </p>

            {error && (
              <p className="mt-2 text-xs leading-5 text-amber-200">
                Backend message: {error}
              </p>
            )}

            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {Object.entries(checks).map(([name, passed]) => (
                <div
                  key={name}
                  className="flex items-center justify-between gap-3 rounded-md border border-slate-800/80 bg-[#0a1627] px-3 py-2"
                >
                  <span className="text-xs text-slate-400">
                    {formatCheckName(name)}
                  </span>
                  <span
                    className={`text-xs font-semibold ${
                      passed ? "text-emerald-300" : "text-red-300"
                    }`}
                  >
                    {passed ? "Pass" : "Fail"}
                  </span>
                </div>
              ))}
            </div>

            {findings.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Findings
                </p>
                {findings.map((finding, index) => (
                  <div
                    key={`${finding.reason ?? "finding"}-${index}`}
                    className="rounded-md border border-slate-800/80 bg-[#0a1627] px-3 py-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-xs font-semibold text-slate-200">
                        {finding.severity ?? "Medium"} -{" "}
                        {finding.location ?? "file"}
                      </p>
                      <p className="text-[11px] uppercase tracking-wider text-slate-500">
                        Page {finding.page ?? 1}
                      </p>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-400">
                      {finding.reason}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      {finding.suggested_action}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {!locked && !result && !isVerifying && (
          <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
            <p className="text-sm font-semibold text-slate-200">
              Compliance verification status: Waiting for evidence
            </p>
            <p className="mt-2 text-xs leading-5 text-slate-500">
              Evidence is not accepted until verification returns APPROVED or a
              compliance officer completes manual review.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
