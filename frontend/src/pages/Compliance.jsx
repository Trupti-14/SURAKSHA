import { useEffect, useMemo, useState } from "react";
import AgentWorkflow from "../components/compliance/AgentWorkflow.jsx";
import CircularCompare from "../components/compliance/CircularCompare.jsx";
import EvidenceUpload from "../components/compliance/EvidenceUpload.jsx";
import Layout from "../components/ui/Layout.jsx";
import {
  addComplianceReference,
  analyzeComplianceCircular,
  analyzeComplianceCircularUpload,
  deleteComplianceReference,
  fetchComplianceCirculars,
  uploadComplianceReference,
} from "../lib/compliance-api.js";

const demoCircularText = `circular_id: RBI-NEW-2026-004
title: Enhanced Digital Fraud Reporting, Customer Protection, and Evidence Preservation Circular
category: Digital Fraud / Customer Protection / Cyber Incident Reporting
issue_date: 2026-06-20
regulator: Reserve Bank of India
effective_from: 2026-07-01

Banks must report confirmed or suspected digital fraud cases involving internet banking, mobile banking, UPI, card-not-present transactions, API banking, or digital lending platforms within 4 hours of detection by the branch, fraud monitoring team, contact centre, or digital operations unit.

Banks must notify affected customers within 24 hours of confirming customer impact. The notification should include the disputed transaction reference, complaint channel, expected resolution process, escalation contact, and customer protection guidance.

Banks must retain fraud evidence, customer communication proof, investigation records, transaction logs, system alerts, and audit trails for at least 5 years. Evidence should be stored in a controlled repository with access logs and chain-of-custody records.

Banks should ensure CERT-In cyber incident escalation wherever digital fraud involves malware, unauthorized access, data leakage, credential theft, payment system compromise, suspicious infrastructure activity, or material cyber security impact.

Banks must submit monthly digital fraud monitoring reports to the Compliance Office and senior management. The report should include incident count, impacted channels, customer complaints, recovery status, unresolved cases, root cause trends, mule account linkage, and corrective action status.

Banks should maintain audit trails for suspicious mule account cases connected to digital fraud proceeds. Branch Operations, Fraud Risk, KYC/AML Compliance, Cybersecurity, and Internal Audit must coordinate evidence review and closure tracking.`;

const fallbackCirculars = [
  {
    circular_id: "RBI-SYN-2026-001",
    title: "Enhanced Monitoring of Mule Accounts",
    regulator: "Reserve Bank of India",
    issue_date: "2026-06-01",
    category: "Fraud Risk Monitoring",
    summary:
      "Banks must tighten detection of suspected mule accounts, add weekly branch-level review, and report high-risk account clusters to the fraud monitoring cell.",
    text: "All regulated entities shall enhance monitoring of mule accounts and suspected fraud conduits. Daily transaction surveillance, branch-level accountability, weekly escalation logs, and regulator-ready evidence are required. Customer impact from blocked accounts must be reviewed with documented justification.",
  },
  {
    circular_id: "RBI-SYN-2026-002",
    title: "KYC Re-verification Advisory",
    regulator: "Reserve Bank of India",
    issue_date: "2026-06-04",
    category: "KYC Operations",
    summary:
      "Banks should refresh KYC for stale or inconsistent customer records and preserve proof of customer notification, re-verification, and exception approvals.",
    text: "Regulated entities are advised to complete KYC re-verification for stale customer records. Customer communication, exception notes, overdue reporting, and branch approval evidence must be retained. Service disruption and customer impact should be minimized through documented outreach.",
  },
  {
    circular_id: "RBI-SYN-2026-003",
    title: "Digital Fraud Reporting Directive",
    regulator: "Reserve Bank of India",
    issue_date: "2026-06-07",
    category: "Digital Fraud Reporting",
    summary:
      "Banks must accelerate digital fraud reporting, preserve incident evidence, and submit structured updates for cyber-enabled payment fraud cases.",
    text: "All banks shall strengthen digital fraud reporting for cyber-enabled payment incidents. Four-hour triage, structured reporting, penalty-aware breach tracking, customer impact notes, and incident evidence retention are mandatory for compliance review.",
  },
];

const checkItems = [
  "Extracts key obligations and deadlines",
  "Compares against approved policy references",
  "Detects policy gaps and impacted departments",
  "Generates action points and evidence requirements",
];

const referenceDomainOptions = [
  "digital_fraud",
  "it_outsourcing",
  "kyc_aml",
  "cyber_incident",
  "digital_payment",
  "mobile_banking",
  "digital_lending",
  "bcp_drp",
  "audit_governance",
  "general_compliance",
];

const initialReferenceForm = {
  title: "",
  domain: "general_compliance",
  category: "",
  circularText: "",
  fileName: "",
};

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function getTextField(item, candidates, fallback) {
  if (typeof item === "string") {
    return item;
  }

  if (!item || typeof item !== "object") {
    return fallback;
  }

  const key = candidates.find(
    (candidate) =>
      typeof item[candidate] === "string" && item[candidate].trim().length > 0,
  );

  return key ? item[key] : fallback;
}

function normalizeCircularItem(item, index) {
  const previewText = item.preview_text ?? item.display_text ?? "";
  const contentText =
    item.content ?? item.full_text ?? item.circular_text ?? item.text ?? item.summary ?? "";
  const summaryText =
    item.summary ?? item.normalized_summary ?? item.content_excerpt ?? previewText;

  return {
    circular_id: item.circular_id ?? item.id ?? `REF-${index + 1}`,
    title: item.title ?? item.id ?? `Policy Reference ${index + 1}`,
    regulator: item.regulator ?? item.primary_regulator ?? "Reserve Bank of India",
    issue_date: item.issue_date ?? "Reference",
    category: item.category ?? "Regulatory Compliance",
    domain: item.domain ?? item.metadata?.domain ?? "general_compliance",
    source_type: item.source_type ?? item.source ?? "Reference",
    file_name: item.file_name ?? "",
    stored_at: item.stored_at ?? "",
    summary:
      summaryText || "Approved baseline reference available for comparison.",
    text: previewText || contentText,
    content: item.content ?? item.full_text ?? item.circular_text ?? "",
    preview_text: previewText,
    display_text: item.display_text ?? previewText,
    source_status: item.source_status ?? item.metadata?.source_status ?? "",
    withdrawn: Boolean(
      item.withdrawn || item.metadata?.withdrawn || item.source_status,
    ),
  };
}

function isUserReference(circularId) {
  return typeof circularId === "string" && circularId.startsWith("USER-REF-");
}

function normalizeActionPoint(item, index, priority) {
  const action = typeof item === "string" ? { action: item } : item ?? {};

  return {
    id: action.id ?? action.map_id ?? action.action_id ?? `ACTION-${index + 1}`,
    action:
      action.action ??
      action.action_point ??
      action.description ??
      action.title ??
      "Review generated compliance action",
    owner: action.owner ?? action.assigned_to ?? action.department ?? "Compliance Office",
    department: action.department ?? action.owner ?? "Compliance Office",
    business_vertical: action.business_vertical ?? "Compliance",
    sub_vertical: action.sub_vertical ?? "Regulatory Compliance",
    deadline: action.deadline ?? action.due_date ?? "To be assigned",
    priority_score: action.priority_score ?? priority.priority_score ?? 0,
    priority_label: action.priority_label ?? priority.priority_label ?? "Medium",
    evidence_required:
      action.evidence_required ??
      action.evidence ??
      action.proof_required ??
      "Evidence requirement to be confirmed by the owner",
    status: action.status ?? "Pending Review",
    reason:
      action.reason ??
      action.priority_reason ??
      action.assignment_basis ??
      "Generated from the circular review.",
  };
}

function normalizeGap(item, index) {
  const gap = typeof item === "string" ? { policy_gap: item } : item ?? {};
  const department =
    gap.department ??
    gap.owner_department ??
    gap.impacted_department ??
    gap.business_vertical ??
    "Compliance Office";
  const existingReference = getTextField(
    gap,
    [
      "existing_reference",
      "old_requirement",
      "old_policy",
      "existing_requirement",
      "current_policy",
    ],
    "Existing reference was not specified.",
  );

  return {
    id: gap.id ?? gap.gap_id ?? `GAP-${index + 1}`,
    new_requirement: getTextField(
      gap,
      ["new_requirement", "new_policy", "requirement", "obligation", "description"],
      "New requirement was not specified.",
    ),
    existing_reference: existingReference,
    old_requirement: existingReference,
    policy_gap: getTextField(
      gap,
      ["policy_gap", "detected_gap", "gap", "summary", "description"],
      "Gap detail was not specified.",
    ),
    severity: gap.severity ?? gap.priority_label ?? "Medium",
    department,
    business_vertical: gap.business_vertical ?? department,
  };
}

function SummaryCard({ label, value, detail, tone = "sky" }) {
  const toneClassName = {
    sky: "bg-sky-500/[0.12] text-sky-300 ring-sky-500/25",
    emerald: "bg-emerald-500/[0.12] text-emerald-300 ring-emerald-500/25",
    amber: "bg-amber-500/[0.12] text-amber-300 ring-amber-500/25",
    red: "bg-red-500/[0.12] text-red-300 ring-red-500/25",
  };

  return (
    <div className="min-h-[96px] rounded-xl border border-slate-800/80 bg-[#0f1b2d] p-4 shadow-[0_16px_36px_rgba(2,6,23,0.22)]">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-xl font-semibold tabular-nums tracking-tight text-slate-50 xl:text-2xl">
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

function priorityTone(label) {
  if (label === "Critical") {
    return "bg-red-500/[0.12] text-red-300 ring-red-500/25";
  }

  if (label === "High") {
    return "bg-amber-500/[0.12] text-amber-300 ring-amber-500/25";
  }

  if (label === "Low") {
    return "bg-emerald-500/[0.12] text-emerald-300 ring-emerald-500/25";
  }

  return "bg-sky-500/[0.12] text-sky-300 ring-sky-500/25";
}

function RequirementList({ title, items, emptyText }) {
  return (
    <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </p>
      {items.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {items.map((item, index) => (
            <li
              key={`${title}-${index}`}
              className="rounded-md border border-slate-800/80 bg-[#0f1b2d] px-3 py-2 text-sm leading-6 text-slate-300"
            >
              {getTextField(item, ["obligation", "requirement", "description", "summary"], String(item))}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm leading-6 text-slate-500">{emptyText}</p>
      )}
    </div>
  );
}

export default function Compliance() {
  const [circulars, setCirculars] = useState(fallbackCirculars);
  const [selectedReferenceId, setSelectedReferenceId] = useState(
    fallbackCirculars[0].circular_id,
  );
  const [referencesOpen, setReferencesOpen] = useState(false);
  const [referenceFormOpen, setReferenceFormOpen] = useState(false);
  const [referenceForm, setReferenceForm] = useState(initialReferenceForm);
  const [referenceSaveState, setReferenceSaveState] = useState({
    status: "idle",
    message: "",
  });
  const [referenceDeleteState, setReferenceDeleteState] = useState({
    status: "idle",
    message: "",
    circularId: "",
  });
  const [referenceUploadFile, setReferenceUploadFile] = useState(null);
  const [referenceFileInputKey, setReferenceFileInputKey] = useState(0);
  const [circularUploadFile, setCircularUploadFile] = useState(null);
  const [circularFileInputKey, setCircularFileInputKey] = useState(0);
  const [circularText, setCircularText] = useState("");
  const [fileName, setFileName] = useState("new-rbi-circular.txt");
  const [analysis, setAnalysis] = useState(null);
  const [selectedActionId, setSelectedActionId] = useState("");
  const [analysisState, setAnalysisState] = useState({
    status: "idle",
    error: "",
  });

  async function loadPolicyReferences() {
    try {
      const circularPayload = await fetchComplianceCirculars();

      if (circularPayload?.ok === false) {
        return;
      }

      const normalizedCirculars = asArray(
        circularPayload.items ?? circularPayload.circulars ?? circularPayload,
      ).map(normalizeCircularItem);

      if (normalizedCirculars.length > 0) {
        setCirculars(normalizedCirculars);
        setSelectedReferenceId((currentId) =>
          normalizedCirculars.some((item) => item.circular_id === currentId)
            ? currentId
            : normalizedCirculars[0].circular_id,
        );
      }
    } catch {
      // Keep the built-in policy references for the prototype if the service is unavailable.
    }
  }

  useEffect(() => {
    let alive = true;

    async function loadInitialPolicyReferences() {
      try {
        const circularPayload = await fetchComplianceCirculars();

        if (circularPayload?.ok === false) {
          return;
        }

        const normalizedCirculars = asArray(
          circularPayload.items ?? circularPayload.circulars ?? circularPayload,
        ).map(normalizeCircularItem);

        if (alive && normalizedCirculars.length > 0) {
          setCirculars(normalizedCirculars);
          setSelectedReferenceId((currentId) =>
            normalizedCirculars.some((item) => item.circular_id === currentId)
              ? currentId
              : normalizedCirculars[0].circular_id,
          );
        }
      } catch {
        // Keep the built-in policy references for the prototype if the service is unavailable.
      }
    }

    loadInitialPolicyReferences();

    return () => {
      alive = false;
    };
  }, []);

  const isAnalyzing = analysisState.status === "loading";
  const hasAnalysis = analysisState.status === "success" && Boolean(analysis);
  const priority = useMemo(() => analysis?.priority ?? {}, [analysis]);
  const policyGaps = useMemo(
    () => asArray(analysis?.policy_gaps).map(normalizeGap),
    [analysis],
  );
  const actionPoints = useMemo(
    () =>
      asArray(analysis?.measurable_action_points).map((item, index) =>
        normalizeActionPoint(item, index, priority),
      ),
    [analysis, priority],
  );
  const obligations = asArray(analysis?.obligations);
  const similarReferences = asArray(analysis?.similar_circulars);
  const priorityLabel = hasAnalysis ? priority.priority_label ?? "Medium" : "Pending";
  const priorityScore = hasAnalysis ? priority.priority_score ?? 0 : null;
  const selectedReference =
    circulars.find((circular) => circular.circular_id === selectedReferenceId) ??
    circulars[0];
  const selectedReferencePreview =
    selectedReference?.preview_text ||
    selectedReference?.display_text ||
    selectedReference?.text ||
    "";
  const selectedAction =
    actionPoints.find((action) => action.id === selectedActionId) ??
    actionPoints[0] ??
    null;

  function clearAnalysis() {
    setAnalysis(null);
    setSelectedActionId("");
    setAnalysisState({ status: "idle", error: "" });
  }

  function handleCircularTextChange(event) {
    setCircularText(event.target.value);
    if (analysis || analysisState.status !== "idle") {
      clearAnalysis();
    }
  }

  function handleFileNameChange(event) {
    setFileName(event.target.value);
    if (analysis || analysisState.status !== "idle") {
      clearAnalysis();
    }
  }

  function handleLoadDemoCircular() {
    setCircularText(demoCircularText);
    setFileName("rbi-new-2026-004-demo.txt");
    setCircularUploadFile(null);
    setCircularFileInputKey((key) => key + 1);
    clearAnalysis();
  }

  function handleCircularUploadFileChange(event) {
    const file = event.target.files?.[0];

    if (!file) {
      setCircularUploadFile(null);
      return;
    }

    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith(".txt") && !lowerName.endsWith(".pdf")) {
      setCircularUploadFile(null);
      event.target.value = "";
      setAnalysisState({
        status: "error",
        error: "Only TXT or PDF upload is supported here.",
      });
      return;
    }

    setCircularUploadFile(file);
    setFileName(file.name);
    clearAnalysis();
  }

  function handleClearCircularUpload() {
    setCircularUploadFile(null);
    setCircularFileInputKey((key) => key + 1);
    if (analysis || analysisState.status !== "idle") {
      clearAnalysis();
    }
  }

  function handleReferenceFieldChange(field, value) {
    setReferenceForm((current) => ({
      ...current,
      fileName:
        field === "circularText" && referenceUploadFile ? "" : current.fileName,
      [field]: value,
    }));
    if (field === "circularText" && referenceUploadFile) {
      setReferenceUploadFile(null);
      setReferenceFileInputKey((key) => key + 1);
    }
    setReferenceSaveState({ status: "idle", message: "" });
  }

  async function handleReferenceFileChange(event) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const lowerName = file.name.toLowerCase();

    if (!lowerName.endsWith(".txt") && !lowerName.endsWith(".pdf")) {
      setReferenceSaveState({
        status: "error",
        message:
          "Only TXT or PDF upload is supported here. Paste DOCX text manually for this prototype.",
      });
      setReferenceUploadFile(null);
      event.target.value = "";
      return;
    }

    if (lowerName.endsWith(".pdf")) {
      setReferenceUploadFile(file);
      setReferenceForm((current) => ({
        ...current,
        fileName: file.name,
      }));
      setReferenceSaveState({ status: "idle", message: "" });
      return;
    }

    try {
      const text = await file.text();
      setReferenceUploadFile(null);
      setReferenceForm((current) => ({
        ...current,
        circularText: text,
        fileName: file.name,
      }));
      setReferenceSaveState({ status: "idle", message: "" });
    } catch {
      setReferenceUploadFile(null);
      setReferenceSaveState({
        status: "error",
        message: "TXT file could not be read. Paste the reference text manually.",
      });
    }
  }

  async function handleSaveReference() {
    const title = referenceForm.title.trim();
    const domain = referenceForm.domain.trim();
    const category = referenceForm.category.trim();
    const referenceText = referenceForm.circularText.trim();
    const isPdfUpload = referenceUploadFile?.name?.toLowerCase().endsWith(".pdf");

    if (!domain || (!referenceText && !isPdfUpload)) {
      setReferenceSaveState({
        status: "error",
        message: "Reference domain and circular text or PDF file are required.",
      });
      return;
    }

    if (!isPdfUpload && referenceText.length < 100) {
      setReferenceSaveState({
        status: "error",
        message: "Circular text must be at least 100 characters.",
      });
      return;
    }

    setReferenceSaveState({ status: "loading", message: "" });

    const result = isPdfUpload
      ? await uploadComplianceReference({
          title,
          domain,
          category,
          file: referenceUploadFile,
        })
      : await addComplianceReference({
          title,
          domain,
          category,
          circular_text: referenceText,
          file_name: referenceForm.fileName.trim(),
        });

    if (result?.ok === false) {
      setReferenceSaveState({
        status: "error",
        message:
          result.error ||
          "Reference circular could not be added. Please review the form and try again.",
      });
      return;
    }

    setReferenceForm(initialReferenceForm);
    setReferenceUploadFile(null);
    setReferenceFileInputKey((key) => key + 1);
    setReferenceSaveState({
      status: "success",
      message: isPdfUpload
        ? "PDF extracted and reference circular added to Policy Reference Library."
        : "Reference circular added to Policy Reference Library.",
    });
    await loadPolicyReferences();
  }

  async function handleDeleteReference(circular) {
    if (!isUserReference(circular?.circular_id)) {
      return;
    }

    const confirmed = window.confirm(
      "Delete this uploaded reference? This will remove it from future comparisons.",
    );
    if (!confirmed) {
      return;
    }

    setReferenceDeleteState({
      status: "loading",
      message: "",
      circularId: circular.circular_id,
    });

    const result = await deleteComplianceReference(circular.circular_id);

    if (result?.ok === false) {
      setReferenceDeleteState({
        status: "error",
        message:
          result.error ||
          "Reference circular could not be deleted. Please try again.",
        circularId: circular.circular_id,
      });
      return;
    }

    setReferenceDeleteState({
      status: "success",
      message: "Reference circular deleted from Policy Reference Library.",
      circularId: "",
    });
    await loadPolicyReferences();
  }

  async function handleAnalyzeCircular() {
    if (!circularUploadFile && !circularText.trim()) {
      setAnalysisState({
        status: "error",
        error: "Paste a new RBI circular or choose a TXT/PDF file before running analysis.",
      });
      return;
    }

    setAnalysis(null);
    setSelectedActionId("");
    setAnalysisState({ status: "loading", error: "" });

    const result = circularUploadFile
      ? await analyzeComplianceCircularUpload({
          file: circularUploadFile,
          fileName: fileName || circularUploadFile.name,
        })
      : await analyzeComplianceCircular({
          circularText,
          fileName: fileName || "new-rbi-circular.txt",
          mode: "offline",
        });

    if (result?.ok === false) {
      setAnalysisState({
        status: "error",
        error:
          result.error ||
          "Analysis could not be completed. Please confirm the backend is running and try again.",
      });
      return;
    }

    const generatedActions = asArray(result?.measurable_action_points).map(
      (item, index) => normalizeActionPoint(item, index, result?.priority ?? {}),
    );

    setAnalysis(result);
    setSelectedActionId(generatedActions[0]?.id ?? "");
    setAnalysisState({ status: "success", error: "" });
  }

  return (
    <Layout>
      <section className="rounded-2xl border border-slate-800/80 bg-[#0d1a2c] p-4 shadow-[0_18px_50px_rgba(2,6,23,0.26)] xl:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">
              Member D Compliance Desk
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-50">
              Agentic Compliance System
            </h2>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
              Paste a new RBI circular, compare it with approved policy references,
              generate gaps, assign actions, and verify evidence.
            </p>
          </div>

          <div className="max-w-sm space-y-2 text-left lg:text-right">
            <div className="inline-flex rounded-full border border-emerald-400/25 bg-emerald-500/[0.12] px-4 py-2 text-xs font-semibold uppercase tracking-wider text-emerald-300">
              Secure Offline Review
            </div>
            <p className="text-xs leading-5 text-slate-500">
              Runs in a bank-controlled environment. Circular analysis and evidence
              checks are performed without sending documents outside the system.
            </p>
          </div>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-3">
          {["Compliance Desk Ready", "Policy Library Ready", "Evidence Verifier Ready"].map(
            (label) => (
              <div
                key={label}
                className="rounded-lg border border-slate-800/80 bg-[#0a1627] px-3 py-2 text-xs font-semibold text-slate-300"
              >
                <span className="mr-2 inline-block h-2 w-2 rounded-full bg-emerald-300" />
                {label}
              </div>
            ),
          )}
        </div>
      </section>

      <section className="rounded-xl border border-sky-400/20 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.24)]">
        <div className="grid gap-5 p-4 xl:grid-cols-[minmax(0,1fr)_340px] xl:p-5">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">
              Start Here
            </p>
            <h2 className="mt-1 text-lg font-semibold tracking-wide text-slate-50">
              1. Add New RBI Circular
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Paste the new circular or advisory received by the bank. Vanguard
              will compare it with approved reference policies and generate
              compliance actions.
            </p>

            <div className="mt-4">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                New circular text
              </label>
              <textarea
                value={circularText}
                onChange={handleCircularTextChange}
                rows={9}
                placeholder="Paste circular text here... Example: Banks must report digital fraud cases within 4 hours..."
                className="mt-2 min-h-[220px] w-full resize-y rounded-lg border border-slate-800/80 bg-[#0a1627] px-4 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
              />
            </div>

            <div className="mt-3 grid gap-3 rounded-lg border border-slate-800/80 bg-[#0a1627] p-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Optional TXT/PDF upload
                </label>
                <input
                  key={circularFileInputKey}
                  type="file"
                  accept=".txt,.pdf,text/plain,application/pdf"
                  onChange={handleCircularUploadFileChange}
                  className="mt-2 w-full rounded-lg border border-slate-800/80 bg-[#0f1b2d] px-3 py-2 text-xs text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-slate-800 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-200 hover:file:bg-slate-700"
                />
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {circularUploadFile
                    ? `Selected ${circularUploadFile.name}`
                    : "Manual paste remains available when no file is selected."}
                </p>
              </div>

              {circularUploadFile && (
                <button
                  type="button"
                  onClick={handleClearCircularUpload}
                  disabled={isAnalyzing}
                  className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-sky-400/60 hover:text-sky-200 disabled:cursor-not-allowed disabled:text-slate-500"
                >
                  Clear file
                </button>
              )}
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-[1fr_auto_auto] md:items-end">
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Document name
                </label>
                <input
                  value={fileName}
                  onChange={handleFileNameChange}
                  className="mt-2 w-full rounded-lg border border-slate-800/80 bg-[#0a1627] px-4 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
                  placeholder="new-rbi-circular.txt"
                />
              </div>

              <button
                type="button"
                onClick={handleAnalyzeCircular}
                disabled={isAnalyzing}
                className="rounded-lg bg-sky-400 px-5 py-2.5 text-sm font-semibold text-[#06101f] transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              >
                {isAnalyzing
                  ? circularUploadFile
                    ? "Extracting and analyzing circular..."
                    : "Analyzing circular..."
                  : "Analyze Circular"}
              </button>

              <button
                type="button"
                onClick={handleLoadDemoCircular}
                disabled={isAnalyzing}
                className="rounded-lg border border-slate-700 bg-slate-900/60 px-5 py-2.5 text-sm font-semibold text-slate-200 transition hover:border-sky-400/50 hover:text-sky-200 disabled:cursor-not-allowed disabled:text-slate-500"
              >
                Load Demo Circular
              </button>
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Demo text is synthetic and used only for prototype testing.
            </p>

            {analysisState.status === "error" && (
              <div className="mt-4 rounded-lg border border-amber-400/25 bg-amber-500/[0.08] px-4 py-3 text-sm leading-6 text-amber-100">
                {analysisState.error}
              </div>
            )}
          </div>

          <aside className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
            <h3 className="text-base font-semibold text-slate-50">
              What Vanguard checks
            </h3>
            <div className="mt-4 space-y-3">
              {checkItems.map((item, index) => (
                <div
                  key={item}
                  className="rounded-lg border border-slate-800/80 bg-[#0f1b2d] p-3"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Check {index + 1}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-slate-200">{item}</p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>

      <AgentWorkflow analysisReady={hasAnalysis} />

      <section className="grid grid-cols-2 gap-3.5 lg:grid-cols-3 xl:grid-cols-5">
        <SummaryCard
          label="Policy Library"
          value="Ready"
          detail="Available"
          tone="emerald"
        />
        <SummaryCard
          label="Generated Actions"
          value={hasAnalysis ? actionPoints.length : "Pending"}
          detail={hasAnalysis ? "Created" : "Analyze"}
          tone={hasAnalysis ? "emerald" : "sky"}
        />
        <SummaryCard
          label="Priority"
          value={
            hasAnalysis && priorityScore !== null
              ? `${priorityLabel} ${priorityScore}/10`
              : "Pending"
          }
          detail={hasAnalysis ? "Assigned" : "Pending"}
          tone={priorityLabel === "Critical" ? "red" : hasAnalysis ? "amber" : "sky"}
        />
        <SummaryCard
          label="Policy Gaps"
          value={hasAnalysis ? policyGaps.length : "Pending"}
          detail={hasAnalysis ? "Review" : "Pending"}
          tone={hasAnalysis && policyGaps.length > 0 ? "amber" : "sky"}
        />
        <SummaryCard
          label="Evidence Status"
          value={hasAnalysis && actionPoints.length > 0 ? "Ready" : "Locked"}
          detail="Verifier"
          tone={hasAnalysis && actionPoints.length > 0 ? "emerald" : "sky"}
        />
      </section>

      {!hasAnalysis ? (
        <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] p-5 shadow-[0_18px_44px_rgba(2,6,23,0.22)]">
          <p className="text-base font-semibold text-slate-100">
            No analysis yet. Paste a new RBI circular and click Analyze Circular.
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Evidence upload will be available after actions are generated.
          </p>
        </section>
      ) : (
        <>
          <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.24)]">
            <div className="border-b border-slate-800/80 px-5 py-4">
              <h2 className="text-base font-semibold tracking-wide text-slate-50">
                Analysis Summary
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Summary, obligations, and matching approved references.
              </p>
            </div>

            <div className="grid gap-4 p-4 xl:grid-cols-[minmax(0,1fr)_360px]">
              <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Summary
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-300">
                  {analysis.summary ?? "Summary was not returned for this circular."}
                </p>
              </div>

              <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Similar References
                </p>
                <p className="mt-3 text-lg font-semibold text-slate-50">
                  Policy references available
                </p>
                <div className="mt-3 space-y-2">
                  {similarReferences.length > 0 ? (
                    similarReferences.slice(0, 3).map((item, index) => (
                      <p
                        key={`${item.id ?? "reference"}-${index}`}
                        className="rounded-md border border-slate-800/80 bg-[#0f1b2d] px-3 py-2 text-xs leading-5 text-slate-400"
                      >
                        {item.id ?? item.title ?? `Reference ${index + 1}`}
                      </p>
                    ))
                  ) : (
                    <p className="text-sm leading-6 text-slate-500">
                      No similar references were returned.
                    </p>
                  )}
                </div>
              </div>

              <div className="xl:col-span-2">
                <RequirementList
                  title="Key Obligations"
                  items={obligations}
                  emptyText="No obligations were returned."
                />
              </div>
            </div>
          </section>

          {policyGaps.length > 0 && <CircularCompare gap={policyGaps[0]} />}

          <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.24)]">
            <div className="border-b border-slate-800/80 px-5 py-4">
              <h2 className="text-base font-semibold tracking-wide text-slate-50">
                Policy Gaps
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Review the gaps found between the new circular and approved references.
              </p>
            </div>

            {policyGaps.length > 0 ? (
              <div className="grid gap-3 p-4 lg:grid-cols-2">
                {policyGaps.map((gap) => (
                  <article
                    key={gap.id}
                    className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold text-sky-300">{gap.id}</p>
                        <h3 className="mt-1 text-sm font-semibold text-slate-100">
                          {gap.department}
                        </h3>
                      </div>
                      <span
                        className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ring-1 ${priorityTone(
                          gap.severity,
                        )}`}
                      >
                        {gap.severity}
                      </span>
                    </div>

                    <dl className="mt-4 space-y-3 text-sm leading-6">
                      <div>
                        <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                          New requirement
                        </dt>
                        <dd className="mt-1 text-slate-300">{gap.new_requirement}</dd>
                      </div>
                      <div>
                        <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                          Existing reference
                        </dt>
                        <dd className="mt-1 text-slate-400">{gap.existing_reference}</dd>
                      </div>
                      <div>
                        <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                          Gap detected
                        </dt>
                        <dd className="mt-1 text-amber-100">{gap.policy_gap}</dd>
                      </div>
                      <div>
                        <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                          Department/business vertical
                        </dt>
                        <dd className="mt-1 text-slate-300">{gap.business_vertical}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
              </div>
            ) : (
              <div className="p-4">
                <p className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4 text-sm leading-6 text-slate-500">
                  No policy gaps were returned for this circular.
                </p>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.24)]">
            <div className="border-b border-slate-800/80 px-5 py-4">
              <h2 className="text-base font-semibold tracking-wide text-slate-50">
                Department-wise Actions
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Assign actions to the responsible team and collect required evidence.
              </p>
            </div>

            {actionPoints.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1280px] table-fixed text-left">
                  <colgroup>
                    <col className="w-[90px]" />
                    <col className="w-[280px]" />
                    <col className="w-[230px]" />
                    <col className="w-[140px]" />
                    <col className="w-[150px]" />
                    <col className="w-[280px]" />
                    <col className="w-[150px]" />
                  </colgroup>
                  <thead className="border-b border-slate-800/80 bg-[#0a1627] text-[11px] uppercase tracking-wider text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-semibold">MAP ID</th>
                      <th className="px-4 py-3 font-semibold">Action</th>
                      <th className="px-4 py-3 font-semibold">Owner/Department</th>
                      <th className="px-4 py-3 font-semibold">Deadline</th>
                      <th className="px-4 py-3 font-semibold">Priority</th>
                      <th className="px-4 py-3 font-semibold">Evidence Required</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {actionPoints.map((action) => (
                      <tr
                        key={action.id}
                        onClick={() => setSelectedActionId(action.id)}
                        className={`cursor-pointer transition ${
                          selectedAction?.id === action.id
                            ? "bg-sky-500/[0.08]"
                            : "hover:bg-slate-800/30"
                        }`}
                      >
                        <td className="px-4 py-4 align-top text-xs font-semibold text-sky-300">
                          {action.id}
                        </td>
                        <td className="break-words px-4 py-4 align-top text-sm leading-6 text-slate-100">
                          {action.action}
                        </td>
                        <td className="break-words px-4 py-4 align-top text-sm leading-5 text-slate-300">
                          <span className="block font-medium text-slate-200">
                            {action.owner}
                          </span>
                          <span className="mt-1 block text-xs leading-5 text-slate-500">
                            {action.department}
                          </span>
                        </td>
                        <td className="px-4 py-4 align-top text-sm tabular-nums text-slate-300">
                          {action.deadline}
                        </td>
                        <td className="px-4 py-4 align-top">
                          <span
                            className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ring-1 ${priorityTone(
                              action.priority_label,
                            )}`}
                          >
                            {action.priority_label} {action.priority_score}/10
                          </span>
                        </td>
                        <td className="break-words px-4 py-4 align-top text-xs leading-5 text-slate-400">
                          {action.evidence_required}
                        </td>
                        <td className="px-4 py-4 align-top">
                          <span className="inline-flex whitespace-nowrap rounded-full bg-slate-800 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-300 ring-1 ring-slate-700">
                            {action.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4">
                <p className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4 text-sm leading-6 text-slate-500">
                  No actions were generated for this circular.
                </p>
              </div>
            )}
          </section>

          {actionPoints.length > 0 ? (
            <EvidenceUpload selectedAction={selectedAction} />
          ) : (
            <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] p-5 shadow-[0_18px_44px_rgba(2,6,23,0.22)]">
              <p className="text-sm font-semibold text-slate-100">
                Evidence upload will be available after actions are generated.
              </p>
            </section>
          )}
        </>
      )}

      <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.22)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 px-5 py-4">
          <div>
            <h2 className="text-base font-semibold tracking-wide text-slate-50">
              Policy Reference Library
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Selected approved circulars and policy references used for comparison in this prototype.
            </p>
            <p className="mt-1 text-[11px] font-medium uppercase tracking-wider text-slate-600">
              Selected references loaded
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setReferenceFormOpen((open) => !open)}
              className="rounded-lg border border-sky-400/40 bg-sky-500/[0.10] px-4 py-2 text-xs font-semibold text-sky-100 transition hover:border-sky-300/70 hover:bg-sky-500/[0.16]"
            >
              Add Reference Circular
            </button>
            <button
              type="button"
              onClick={() => setReferencesOpen((open) => !open)}
              className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-sky-400/60 hover:text-sky-200"
            >
              {referencesOpen ? "Hide References" : "Show References"}
            </button>
          </div>
        </div>

        {referenceFormOpen && (
          <div className="border-b border-slate-800/80 px-5 py-4">
            <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-sky-300">
                    Add Reference Circular
                  </p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Add an approved old circular or policy reference used for comparison.
                  </p>
                </div>
                <span className="rounded-full border border-slate-700 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                  Reference only
                </span>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px_minmax(0,1fr)]">
                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    Reference Title
                  </label>
                  <input
                    value={referenceForm.title}
                    onChange={(event) =>
                      handleReferenceFieldChange("title", event.target.value)
                    }
                    className="mt-2 w-full rounded-lg border border-slate-800/80 bg-[#0f1b2d] px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
                    placeholder="Digital Payment Security Controls Reference"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    Domain
                  </label>
                  <select
                    value={referenceForm.domain}
                    onChange={(event) =>
                      handleReferenceFieldChange("domain", event.target.value)
                    }
                    className="mt-2 w-full rounded-lg border border-slate-800/80 bg-[#0f1b2d] px-3 py-2.5 text-sm text-slate-100 outline-none transition focus:border-sky-400/60"
                  >
                    {referenceDomainOptions.map((domain) => (
                      <option key={domain} value={domain}>
                        {domain}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    Category
                  </label>
                  <input
                    value={referenceForm.category}
                    onChange={(event) =>
                      handleReferenceFieldChange("category", event.target.value)
                    }
                    className="mt-2 w-full rounded-lg border border-slate-800/80 bg-[#0f1b2d] px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
                    placeholder="Digital Payment Security / Fraud Monitoring"
                  />
                </div>
              </div>

              <div className="mt-3">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Circular Text
                </label>
                <textarea
                  value={referenceForm.circularText}
                  onChange={(event) =>
                    handleReferenceFieldChange("circularText", event.target.value)
                  }
                  rows={5}
                  className="mt-2 min-h-[140px] w-full resize-y rounded-lg border border-slate-800/80 bg-[#0f1b2d] px-3 py-2.5 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
                  placeholder="Paste the approved old circular or policy reference text..."
                />
              </div>

              <div className="mt-3 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    Optional TXT/PDF upload
                  </label>
                  <input
                    key={referenceFileInputKey}
                    type="file"
                    accept=".txt,.pdf,text/plain,application/pdf"
                    onChange={handleReferenceFileChange}
                    className="mt-2 w-full rounded-lg border border-slate-800/80 bg-[#0f1b2d] px-3 py-2 text-xs text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-slate-800 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-200 hover:file:bg-slate-700"
                  />
                  {referenceForm.fileName && (
                    <p className="mt-1 text-xs text-slate-500">
                      Loaded {referenceForm.fileName}
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleSaveReference}
                  disabled={referenceSaveState.status === "loading"}
                  className="rounded-lg bg-sky-400 px-5 py-2.5 text-sm font-semibold text-[#06101f] transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
                  {referenceSaveState.status === "loading"
                    ? referenceUploadFile
                      ? "Extracting PDF..."
                      : "Saving reference..."
                    : "Save Reference"}
                </button>
              </div>

              {referenceSaveState.message && (
                <div
                  className={`mt-3 rounded-lg border px-4 py-3 text-sm leading-6 ${
                    referenceSaveState.status === "success"
                      ? "border-emerald-400/25 bg-emerald-500/[0.08] text-emerald-100"
                      : "border-amber-400/25 bg-amber-500/[0.08] text-amber-100"
                  }`}
                >
                  {referenceSaveState.message}
                </div>
              )}
            </div>
          </div>
        )}

        {referenceDeleteState.message && (
          <div className="border-b border-slate-800/80 px-5 py-3">
            <div
              className={`rounded-lg border px-4 py-3 text-sm leading-6 ${
                referenceDeleteState.status === "success"
                  ? "border-emerald-400/25 bg-emerald-500/[0.08] text-emerald-100"
                  : "border-amber-400/25 bg-amber-500/[0.08] text-amber-100"
              }`}
            >
              {referenceDeleteState.message}
            </div>
          </div>
        )}

        {referencesOpen && (
          <div className="grid gap-4 p-4 xl:grid-cols-[420px_minmax(0,1fr)]">
            <div className="space-y-3">
              {circulars.map((circular) => (
                <article
                  key={circular.circular_id}
                  className={`rounded-lg border p-4 ${
                    selectedReference?.circular_id === circular.circular_id
                      ? "border-sky-400/40 bg-sky-500/[0.10]"
                      : "border-slate-800/80 bg-[#0a1627]"
                  }`}
                >
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-sky-300">
                    Baseline Reference
                  </p>
                  <h3 className="mt-1 text-sm font-semibold leading-5 text-slate-50">
                    {circular.title}
                  </h3>
                  <p className="mt-2 text-xs leading-5 text-slate-500">
                    {circular.domain} / {circular.category} - {circular.regulator}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedReferenceId(circular.circular_id)}
                      className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-sky-400/60 hover:text-sky-200"
                    >
                      View Reference
                    </button>
                    {isUserReference(circular.circular_id) ? (
                      <button
                        type="button"
                        onClick={() => handleDeleteReference(circular)}
                        disabled={
                          referenceDeleteState.status === "loading" &&
                          referenceDeleteState.circularId === circular.circular_id
                        }
                        className="rounded-lg border border-rose-500/30 bg-rose-500/[0.06] px-3 py-1.5 text-xs font-semibold text-rose-200 transition hover:border-rose-400/60 hover:bg-rose-500/[0.10] disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-900/40 disabled:text-slate-500"
                      >
                        {referenceDeleteState.status === "loading" &&
                        referenceDeleteState.circularId === circular.circular_id
                          ? "Deleting..."
                          : "Delete"}
                      </button>
                    ) : (
                      <span className="rounded-full border border-slate-700 bg-slate-900/50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                        Locked
                      </span>
                    )}
                  </div>
                </article>
              ))}
            </div>

            <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Reference Preview
              </p>
              <h3 className="mt-2 text-base font-semibold text-slate-50">
                {selectedReference?.title ?? "No reference selected"}
              </h3>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {selectedReference?.regulator ?? "Reserve Bank of India"} -{" "}
                {selectedReference?.issue_date ?? "Reference"}
              </p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                {selectedReference?.domain ?? "general_compliance"}
                {(selectedReference?.withdrawn ||
                  selectedReference?.source_status) && (
                  <span className="ml-2 rounded-full border border-amber-400/25 bg-amber-500/[0.08] px-2 py-0.5 text-[10px] text-amber-200">
                    {selectedReference?.source_status || "Withdrawn / archived"}
                  </span>
                )}
              </p>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                {selectedReference?.summary ??
                  "Select a baseline reference to preview it."}
              </p>
              <p className="mt-4 max-h-48 overflow-auto rounded-md border border-slate-800/80 bg-[#0f1b2d] p-3 text-sm leading-6 text-slate-500">
                {selectedReferencePreview ||
                  "Reference text will appear here when available."}
              </p>
            </div>
          </div>
        )}
      </section>
    </Layout>
  );
}
