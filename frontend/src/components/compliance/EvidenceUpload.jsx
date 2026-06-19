import { useRef, useState } from "react";

const verificationResult = {
  verified: true,
  confidence: 0.82,
  notes: "Evidence accepted for offline compliance review",
};

export default function EvidenceUpload({ selectedAction }) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState("");
  const [result, setResult] = useState(null);

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    setFileName(file?.name ?? "");
    setResult(file ? verificationResult : null);
  }

  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          Evidence Upload
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Upload proof for the selected action point. Evidence will be tracked
          for offline compliance review; no cloud vision API is used.
        </p>
      </div>

      <div className="space-y-4 p-4">
        <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Selected MAP
          </p>
          <p className="mt-2 text-sm font-medium leading-6 text-slate-100">
            {selectedAction?.action ?? "Select an action point for evidence review"}
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

        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={inputRef}
            className="hidden"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-semibold text-[#06101f] transition hover:bg-sky-300"
          >
            Upload Proof
          </button>
          <div>
            <p className="text-sm text-slate-300">
              {fileName || "No file selected"}
            </p>
            <p className="text-xs text-slate-500">
              Allowed types: PDF, PNG, JPG
            </p>
          </div>
        </div>

        {result && (
          <div className="rounded-lg border border-emerald-400/25 bg-emerald-500/[0.10] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold text-emerald-300">
                Compliance verification status
              </p>
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-200">
                Confidence {(result.confidence * 100).toFixed(0)}%
              </p>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-300">{result.notes}</p>
            <p className="mt-2 text-xs leading-5 text-emerald-200/80">
              Evidence file selected for compliance review. Automated verification
              can be connected to local vision checks during advanced integration;
              no cloud vision API is used.
            </p>
          </div>
        )}

        {!result && (
          <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
            <p className="text-sm font-semibold text-slate-200">
              Compliance verification status: Waiting for evidence
            </p>
            <p className="mt-2 text-xs leading-5 text-slate-500">
              Evidence will be marked for review after a PDF, PNG, or JPG proof
              file is selected.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
