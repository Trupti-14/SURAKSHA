import { useEffect, useMemo, useState } from "react";
import AgentWorkflow from "../components/compliance/AgentWorkflow.jsx";
import CircularCompare from "../components/compliance/CircularCompare.jsx";
import EvidenceUpload from "../components/compliance/EvidenceUpload.jsx";
import Layout from "../components/ui/Layout.jsx";
import { analyzeComplianceCircular } from "../lib/compliance-api.js";

const fallbackCirculars = [
  {
    circular_id: "RBI-SYN-2026-001",
    title: "Enhanced Monitoring of Mule Accounts",
    regulator: "Reserve Bank of India",
    issue_date: "2026-06-01",
    deadline: "2026-06-21",
    category: "Fraud Risk Monitoring",
    summary:
      "Banks must tighten detection of suspected mule accounts, add weekly branch-level review, and report high-risk account clusters to the fraud monitoring cell.",
    old_policy:
      "Mule account checks were performed during monthly AML reviews using threshold-based alerts and manual branch escalations.",
    new_policy:
      "Mule account monitoring must run daily using transaction velocity, beneficiary churn, device overlap, and rapid cash-out indicators, with weekly evidence packs retained for audit.",
    detected_gap:
      "Monthly AML review cadence does not satisfy daily mule-account surveillance, weekly branch escalation, or regulator-ready evidence retention.",
    text: "All regulated entities shall enhance monitoring of mule accounts and suspected fraud conduits. Daily transaction surveillance, branch-level accountability, weekly escalation logs, and regulator-ready evidence are required. Customer impact from blocked accounts must be reviewed with documented justification.",
    priority_score: 10,
    priority_label: "Critical",
    priority_reason:
      "risk keywords: fraud, mule; deadline within 21 days; customer impact and reporting terms",
  },
  {
    circular_id: "RBI-SYN-2026-002",
    title: "KYC Re-verification Advisory",
    regulator: "Reserve Bank of India",
    issue_date: "2026-06-04",
    deadline: "2026-07-19",
    category: "KYC Operations",
    summary:
      "Banks should refresh KYC for stale or inconsistent customer records and preserve proof of customer notification, re-verification, and exception approvals.",
    old_policy:
      "KYC refresh was handled through periodic batch campaigns and branch-led exception handling for missing documents.",
    new_policy:
      "KYC re-verification must prioritize high-risk customers, dormant accounts, inconsistent identity fields, and accounts with recent fraud flags, with auditable notification evidence.",
    detected_gap:
      "Batch campaign controls do not show risk-first segmentation, fraud-flag routing, or complete customer notification evidence.",
    text: "Regulated entities are advised to complete KYC re-verification for stale customer records. Customer communication, exception notes, overdue reporting, and branch approval evidence must be retained. Service disruption and customer impact should be minimized through documented outreach.",
    priority_score: 7,
    priority_label: "High",
    priority_reason:
      "fraud-flagged records, reporting evidence, and customer impact controls",
  },
  {
    circular_id: "RBI-SYN-2026-003",
    title: "Digital Fraud Reporting Directive",
    regulator: "Reserve Bank of India",
    issue_date: "2026-06-07",
    deadline: "2026-06-17",
    category: "Digital Fraud Reporting",
    summary:
      "Banks must accelerate digital fraud reporting, preserve incident evidence, and submit structured updates for cyber-enabled payment fraud cases.",
    old_policy:
      "Digital fraud incidents were consolidated into daily summaries and reported after internal confirmation by operations and cyber teams.",
    new_policy:
      "Digital fraud incidents must be triaged within four hours, reported in structured format, linked to cyber telemetry, and supported by customer-impact evidence.",
    detected_gap:
      "Daily summary reporting is slower than the four-hour triage requirement and lacks structured telemetry-linked evidence.",
    text: "All banks shall strengthen digital fraud reporting for cyber-enabled payment incidents. Four-hour triage, structured reporting, penalty-aware breach tracking, customer impact notes, and incident evidence retention are mandatory for compliance review.",
    priority_score: 10,
    priority_label: "Critical",
    priority_reason:
      "fraud, cyber, payment, penalty, reporting, and short deadline terms",
  },
];

const fallbackActions = [
  {
    id: "MAP-RBI-SYN-2026-001-01",
    circular_id: "RBI-SYN-2026-001",
    action: "Map mule-account alert scenarios to daily surveillance rules",
    owner: "Fraud Risk Operations",
    deadline: "2026-06-21",
    priority_score: 10,
    priority_label: "Critical",
    evidence_required: "Rule configuration screenshot and daily alert export",
    status: "In Progress",
    reason:
      "Circular requires daily mule account monitoring using transaction and device indicators.",
  },
  {
    id: "MAP-RBI-SYN-2026-001-02",
    circular_id: "RBI-SYN-2026-001",
    action: "Create weekly branch escalation pack for suspected mule clusters",
    owner: "Fraud Risk Operations",
    deadline: "2026-06-21",
    priority_score: 10,
    priority_label: "Critical",
    evidence_required: "Weekly escalation register with branch owner sign-off",
    status: "Pending Review",
    reason: "Weekly escalation logs and regulator-ready evidence are required.",
  },
  {
    id: "MAP-RBI-SYN-2026-002-01",
    circular_id: "RBI-SYN-2026-002",
    action: "Segment stale KYC records by risk and exception status",
    owner: "KYC Compliance Desk",
    deadline: "2026-07-19",
    priority_score: 7,
    priority_label: "High",
    evidence_required: "Customer segment export and exception approval sample",
    status: "Pending Review",
    reason: "Circular prioritizes stale, dormant, inconsistent, and fraud-flagged records.",
  },
  {
    id: "MAP-RBI-SYN-2026-002-02",
    circular_id: "RBI-SYN-2026-002",
    action: "Capture customer notification proof for KYC re-verification",
    owner: "KYC Compliance Desk",
    deadline: "2026-07-19",
    priority_score: 7,
    priority_label: "High",
    evidence_required: "SMS/email campaign proof and branch outreach tracker",
    status: "Pending Review",
    reason: "Auditable customer notification evidence must be retained.",
  },
  {
    id: "MAP-RBI-SYN-2026-003-01",
    circular_id: "RBI-SYN-2026-003",
    action: "Implement four-hour digital fraud triage checklist",
    owner: "Digital Fraud Response Cell",
    deadline: "2026-06-17",
    priority_score: 10,
    priority_label: "Critical",
    evidence_required: "Incident checklist sample with timestamped triage fields",
    status: "In Progress",
    reason: "Circular mandates accelerated triage for cyber-enabled payment fraud.",
  },
  {
    id: "MAP-RBI-SYN-2026-003-02",
    circular_id: "RBI-SYN-2026-003",
    action: "Prepare structured digital fraud reporting evidence pack",
    owner: "Digital Fraud Response Cell",
    deadline: "2026-06-17",
    priority_score: 10,
    priority_label: "Critical",
    evidence_required: "Structured report sample and customer impact note",
    status: "Pending Review",
    reason: "Reporting, cyber telemetry linkage, and customer impact evidence are mandatory.",
  },
];

function SummaryCard({ label, value, detail, tone = "sky" }) {
  const toneClassName = {
    sky: "bg-sky-500/[0.12] text-sky-300 ring-sky-500/25",
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

function priorityTone(label) {
  if (label === "Critical") {
    return "bg-red-500/[0.12] text-red-300 ring-red-500/25";
  }
  if (label === "High") {
    return "bg-amber-500/[0.12] text-amber-300 ring-amber-500/25";
  }
  return "bg-sky-500/[0.12] text-sky-300 ring-sky-500/25";
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function getReadableItem(item, candidates = []) {
  if (typeof item === "string") {
    return item;
  }

  if (!item || typeof item !== "object") {
    return "No detail provided.";
  }

  const readableKey = candidates.find(
    (key) => typeof item[key] === "string" && item[key].trim().length > 0,
  );

  if (readableKey) {
    return item[readableKey];
  }

  return Object.entries(item)
    .filter(([, value]) => typeof value === "string" || typeof value === "number")
    .map(([key, value]) => `${key}: ${value}`)
    .join("; ");
}

function normalizeActionPoint(item, index, circular, priority) {
  if (typeof item === "string") {
    return {
      id: `API-MAP-${circular.circular_id}-${index + 1}`,
      circular_id: circular.circular_id,
      action: item,
      owner: "Compliance Operations",
      deadline: circular.deadline ?? "To be assigned",
      priority_score: priority.priority_score ?? circular.priority_score,
      priority_label: priority.priority_label ?? circular.priority_label,
      evidence_required: "Compliance evidence pack to be defined by owner",
      status: "Backend Draft",
      reason: "Generated from backend compliance analysis.",
    };
  }

  const action = item ?? {};

  return {
    id:
      action.id ??
      action.map_id ??
      action.action_id ??
      `API-MAP-${circular.circular_id}-${index + 1}`,
    circular_id: circular.circular_id,
    action:
      action.action ??
      action.action_point ??
      action.description ??
      action.title ??
      "Review generated compliance action point",
    owner: action.owner ?? action.assigned_to ?? action.department ?? "Compliance Operations",
    deadline: action.deadline ?? action.due_date ?? circular.deadline ?? "To be assigned",
    priority_score:
      action.priority_score ?? priority.priority_score ?? circular.priority_score,
    priority_label:
      action.priority_label ?? priority.priority_label ?? circular.priority_label,
    evidence_required:
      action.evidence_required ??
      action.evidence ??
      action.proof_required ??
      "Compliance evidence pack to be defined by owner",
    status: action.status ?? "Backend Draft",
    reason:
      action.reason ??
      action.priority_reason ??
      "Generated from backend compliance analysis.",
  };
}

function AnalysisList({ title, items, candidates, emptyText }) {
  const safeItems = asArray(items);

  return (
    <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </p>
      {safeItems.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {safeItems.map((item, index) => (
            <li
              key={`${title}-${index}`}
              className="rounded-md border border-slate-800/80 bg-[#0f1b2d] px-3 py-2 text-sm leading-6 text-slate-300"
            >
              {getReadableItem(item, candidates)}
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
  const [actions, setActions] = useState(fallbackActions);
  const [selectedCircularId, setSelectedCircularId] = useState(
    fallbackCirculars[0].circular_id,
  );
  const [selectedActionId, setSelectedActionId] = useState(fallbackActions[0].id);
  const [analysisResultsByCircularId, setAnalysisResultsByCircularId] = useState({});
  const [analysisState, setAnalysisState] = useState({
    status: "idle",
    circularId: "",
    error: "",
  });

  useEffect(() => {
    let alive = true;

    async function loadComplianceData() {
      try {
        const [circularResponse, actionResponse] = await Promise.all([
          fetch("/api/compliance/circulars"),
          fetch("/api/compliance/actions"),
        ]);

        if (!circularResponse.ok || !actionResponse.ok) {
          return;
        }

        const circularPayload = await circularResponse.json();
        const actionPayload = await actionResponse.json();

        if (alive) {
          setCirculars(circularPayload.circulars ?? fallbackCirculars);
          setActions(actionPayload.actions ?? fallbackActions);
        }
      } catch {
        // Offline-first demo path: keep local synthetic data when no backend is running.
      }
    }

    loadComplianceData();

    return () => {
      alive = false;
    };
  }, []);

  const selectedCircular =
    circulars.find((circular) => circular.circular_id === selectedCircularId) ??
    circulars[0];

  const selectedAnalysis = selectedCircular
    ? analysisResultsByCircularId[selectedCircular.circular_id]
    : null;

  const displayedCircular = useMemo(() => {
    if (!selectedCircular) {
      return null;
    }

    const priority = selectedAnalysis?.priority ?? {};
    const policyGaps = asArray(selectedAnalysis?.policy_gaps);
    const detectedGap =
      policyGaps.length > 0
        ? getReadableItem(policyGaps[0], [
            "detected_gap",
            "gap",
            "description",
            "summary",
            "requirement",
          ])
        : selectedCircular.detected_gap;

    return {
      ...selectedCircular,
      summary: selectedAnalysis?.summary ?? selectedCircular.summary,
      detected_gap: detectedGap,
      priority_score: priority.priority_score ?? selectedCircular.priority_score,
      priority_label: priority.priority_label ?? selectedCircular.priority_label,
      priority_reason:
        priority.priority_reason ?? selectedCircular.priority_reason,
    };
  }, [selectedAnalysis, selectedCircular]);

  const localCircularActions = useMemo(
    () =>
      actions.filter(
        (action) => action.circular_id === selectedCircular?.circular_id,
      ),
    [actions, selectedCircular],
  );

  const backendActions = useMemo(
    () =>
      asArray(selectedAnalysis?.measurable_action_points).map((action, index) =>
        normalizeActionPoint(
          action,
          index,
          displayedCircular ?? selectedCircular,
          selectedAnalysis?.priority ?? {},
        ),
      ),
    [displayedCircular, selectedAnalysis, selectedCircular],
  );

  const circularActions =
    backendActions.length > 0 ? backendActions : localCircularActions;

  const selectedAction =
    circularActions.find((action) => action.id === selectedActionId) ??
    circularActions[0] ??
    actions[0];

  const criticalCount = circulars.filter(
    (circular) => circular.priority_label === "Critical",
  ).length;
  const dueSoonCount = actions.filter((action) => action.status === "In Progress").length;
  const verifiedCount = actions.filter((action) => action.status === "Verified").length;

  const selectedAnalysisState =
    analysisState.circularId === selectedCircular?.circular_id
      ? analysisState
      : {
          status: selectedAnalysis ? "success" : "idle",
          circularId: selectedCircular?.circular_id ?? "",
          error: "",
        };

  const isAnalyzing = selectedAnalysisState.status === "loading";

  async function handleAnalyzeCircular() {
    if (!selectedCircular) {
      return;
    }

    const circularId = selectedCircular.circular_id;
    setAnalysisState({ status: "loading", circularId, error: "" });

    const result = await analyzeComplianceCircular({
      circularText: selectedCircular.text ?? selectedCircular.summary ?? "",
      fileName: `${circularId}.txt`,
      mode: "offline",
    });

    if (result?.ok === false) {
      setAnalysisState({
        status: "error",
        circularId,
        error:
          result.error ??
          "Compliance analysis backend is unavailable. Local fallback data remains active.",
      });
      return;
    }

    setAnalysisResultsByCircularId((currentResults) => ({
      ...currentResults,
      [circularId]: result,
    }));

    const nextBackendActions = asArray(result?.measurable_action_points).map(
      (action, index) =>
        normalizeActionPoint(action, index, selectedCircular, result?.priority ?? {}),
    );

    if (nextBackendActions.length > 0) {
      setSelectedActionId(nextBackendActions[0].id);
    }

    setAnalysisState({ status: "success", circularId, error: "" });
  }

  return (
    <Layout>
      <section className="rounded-2xl border border-slate-800/80 bg-[#0d1a2c] p-4 shadow-[0_18px_50px_rgba(2,6,23,0.3)] xl:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">
              Regulatory Compliance Desk
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-50 xl:text-2xl">
              Regulatory Compliance Command Center
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Review regulatory circulars, track policy gaps, generate measurable
              action points, assign priority, and manage evidence-based compliance
              closure.
            </p>
          </div>

          <div className="space-y-2 text-right">
            <div className="rounded-full border border-emerald-400/25 bg-emerald-500/[0.12] px-4 py-2 text-xs font-semibold uppercase tracking-wider text-emerald-300">
              Offline Mode Active
            </div>
            <p className="max-w-xs text-xs leading-5 text-slate-500">
              Runs as an offline-first compliance engine using local circular data,
              rule-based MAP generation, and rule-based priority scoring. No
              Gemini, OpenAI, or cloud API dependency is used.
            </p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3.5 lg:grid-cols-3 xl:grid-cols-5">
        <SummaryCard
          label="Local Circulars"
          value={circulars.length}
          detail="LOCAL RECORDS"
        />
        <SummaryCard
          label="Generated MAPs"
          value={actions.length}
          detail="AUTOMATED"
          tone="emerald"
        />
        <SummaryCard
          label="Critical Priority"
          value={criticalCount}
          detail="Focus"
          tone={criticalCount > 0 ? "red" : "emerald"}
        />
        <SummaryCard
          label="Active Reviews"
          value={dueSoonCount}
          detail="Evidence"
          tone="amber"
        />
        <SummaryCard
          label="Verified Evidence"
          value={verifiedCount}
          detail="REVIEW"
          tone="emerald"
        />
      </section>

      <section className="grid gap-3.5 xl:grid-cols-12">
        <div className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)] xl:col-span-4">
          <div className="border-b border-slate-800/80 px-5 py-4">
            <h2 className="text-base font-semibold tracking-wide text-slate-50">
              Local Circulars
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Local RBI-style circular records available for compliance review.
            </p>
          </div>
          <div className="space-y-3 p-4">
            {circulars.map((circular) => (
              <button
                key={circular.circular_id}
                type="button"
                onClick={() => {
                  setSelectedCircularId(circular.circular_id);
                  const nextAction = actions.find(
                    (action) => action.circular_id === circular.circular_id,
                  );
                  if (nextAction) {
                    setSelectedActionId(nextAction.id);
                  }
                }}
                className={`w-full rounded-lg border p-4 text-left transition ${
                  selectedCircular?.circular_id === circular.circular_id
                    ? "border-sky-400/40 bg-sky-500/[0.10]"
                    : "border-slate-800/80 bg-[#0a1627] hover:border-slate-700"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-semibold leading-5 text-slate-50">
                    {circular.title}
                  </p>
                  <span
                    className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ring-1 ${priorityTone(
                      circular.priority_label,
                    )}`}
                  >
                    {circular.priority_label} {circular.priority_score}/10
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">
                  {circular.category} - Due {circular.deadline}
                </p>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)] xl:col-span-8">
          <div className="border-b border-slate-800/80 px-5 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold tracking-wide text-slate-50">
                  {selectedCircular.title}
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  {selectedCircular.regulator} - Issued {selectedCircular.issue_date}
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={handleAnalyzeCircular}
                  disabled={isAnalyzing}
                  className="rounded-lg border border-sky-400/30 bg-sky-500/[0.12] px-4 py-2 text-xs font-semibold uppercase tracking-wider text-sky-200 transition hover:border-sky-300/60 disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-800 disabled:text-slate-500"
                >
                  {isAnalyzing
                    ? "Analyzing..."
                    : selectedAnalysis
                      ? "Re-analyze Circular"
                      : "Analyze Circular"}
                </button>
                <span
                  className={`rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide ring-1 ${priorityTone(
                    displayedCircular.priority_label,
                  )}`}
                >
                  {displayedCircular.priority_label} Priority
                </span>
              </div>
            </div>
          </div>

          <div className="grid gap-4 p-4 lg:grid-cols-3">
            {selectedAnalysisState.status !== "idle" && (
              <div className="lg:col-span-3">
                {selectedAnalysisState.status === "loading" && (
                  <div className="rounded-lg border border-sky-400/25 bg-sky-500/[0.08] px-4 py-3 text-sm font-medium text-sky-200">
                    Analyzing selected circular through the offline compliance backend...
                  </div>
                )}
                {selectedAnalysisState.status === "error" && (
                  <div className="rounded-lg border border-amber-400/25 bg-amber-500/[0.08] px-4 py-3">
                    <p className="text-sm font-semibold text-amber-200">
                      Backend analysis unavailable
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">
                      {selectedAnalysisState.error} Existing local fallback data remains visible.
                    </p>
                  </div>
                )}
                {selectedAnalysisState.status === "success" && selectedAnalysis && (
                  <div className="rounded-lg border border-emerald-400/25 bg-emerald-500/[0.08] px-4 py-3 text-sm font-medium text-emerald-200">
                    Backend compliance analysis loaded for this circular.
                  </div>
                )}
              </div>
            )}
            <div className="lg:col-span-2">
              <p className="text-sm leading-6 text-slate-300">
                {displayedCircular.summary}
              </p>
              <p className="mt-3 text-xs leading-5 text-slate-500">
                Priority reason: {displayedCircular.priority_reason}
              </p>
            </div>
            <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Deadline
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-50">
                {selectedCircular.deadline}
              </p>
              <p className="mt-2 text-xs leading-5 text-slate-400">
                Priority is based on regulatory urgency, customer impact,
                reporting obligations, and implementation deadline.
              </p>
            </div>
            <div className="rounded-lg border border-amber-400/20 bg-amber-500/[0.08] p-4 lg:col-span-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">
                Detected Gap
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-200">
                {displayedCircular.detected_gap}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
        <div className="border-b border-slate-800/80 px-5 py-4">
          <h2 className="text-base font-semibold tracking-wide text-slate-50">
            Measurable Action Points
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Action points generated from circular obligations for responsible teams.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1180px] text-left">
            <thead className="border-b border-slate-800/80 bg-[#0a1627] text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3 font-semibold">MAP ID</th>
                <th className="px-5 py-3 font-semibold">Action</th>
                <th className="px-5 py-3 font-semibold">Owner</th>
                <th className="px-5 py-3 font-semibold">Deadline</th>
                <th className="px-5 py-3 font-semibold">Priority</th>
                <th className="px-5 py-3 font-semibold">Evidence Required</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {circularActions.map((action) => (
                <tr
                  key={action.id}
                  onClick={() => setSelectedActionId(action.id)}
                  className={`cursor-pointer transition ${
                    selectedAction?.id === action.id
                      ? "bg-sky-500/[0.08]"
                      : "hover:bg-slate-800/30"
                  }`}
                >
                  <td className="px-5 py-4 text-xs font-semibold text-sky-300">
                    {action.id}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-100">
                    {action.action}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-300">
                    {action.owner}
                  </td>
                  <td className="px-5 py-4 text-sm tabular-nums text-slate-300">
                    {action.deadline}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ring-1 ${priorityTone(
                        action.priority_label ?? displayedCircular.priority_label,
                      )}`}
                    >
                      {action.priority_label ?? displayedCircular.priority_label}{" "}
                      {action.priority_score ?? displayedCircular.priority_score}/10
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs leading-5 text-slate-400">
                    {action.evidence_required}
                  </td>
                  <td className="px-5 py-4">
                    <span className="rounded-full bg-slate-800 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-300 ring-1 ring-slate-700">
                      {action.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs leading-5 text-slate-400">
                    {action.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <AgentWorkflow activeStep={selectedAnalysis ? 5 : 4} />

      {selectedAnalysis && (
        <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.28)]">
          <div className="border-b border-slate-800/80 px-5 py-4">
            <h2 className="text-base font-semibold tracking-wide text-slate-50">
              Backend Analysis Output
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Response fields returned by the local compliance analysis endpoint.
            </p>
          </div>

          <div className="grid gap-4 p-4 lg:grid-cols-2">
            <AnalysisList
              title="Obligations"
              items={selectedAnalysis.obligations}
              candidates={["obligation", "requirement", "description", "summary"]}
              emptyText="No obligations returned by backend."
            />
            <AnalysisList
              title="Policy Gaps"
              items={selectedAnalysis.policy_gaps}
              candidates={["gap", "detected_gap", "description", "summary"]}
              emptyText="No policy gaps returned by backend."
            />
            <AnalysisList
              title="Workflow"
              items={selectedAnalysis.workflow}
              candidates={["step", "name", "task", "description", "status"]}
              emptyText="No workflow steps returned by backend."
            />
            <AnalysisList
              title="Engine Notes"
              items={selectedAnalysis.engine_notes}
              candidates={["note", "message", "description", "summary"]}
              emptyText="No engine notes returned by backend."
            />
          </div>
        </section>
      )}

      <section className="grid gap-3.5 xl:grid-cols-2">
        <CircularCompare circular={displayedCircular} />
        <EvidenceUpload selectedAction={selectedAction} />
      </section>
    </Layout>
  );
}
