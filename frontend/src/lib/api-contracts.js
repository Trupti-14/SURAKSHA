/*
  Vanguard frontend integration contracts.
  These shapes document the data future backend, ML, telemetry, forensics,
  compliance, and admin modules should provide to the React foundation.
*/

export const telemetryRiskPayloadContract = {
  risk_score: 68,
  triggers: [
    {
      anomaly: "High-velocity mouse vector acceleration spike",
      severity: "MEDIUM",
      timestamp: "16:42:01",
    },
  ],
  requires_mfa: true,
  session_blocked: false,
};

export const activeSessionContract = {
  customerId: "CB-CUST-00000",
  sessionId: "SES-REGION-0000",
  name: "Customer Name",
  device: "Device posture and platform",
  location: "City, State",
  riskScore: 0,
  status: "NORMAL",
  requiresMfa: false,
  sessionBlocked: false,
  lastSeen: "HH:MM:SS",
  triggers: [],
};

export const forensicsResultContract = {
  caseId: "FOR-0000",
  documentId: "DOC-0000",
  customerId: "CB-CUST-00000",
  riskFinding: "No tampering detected",
  confidence: 0.98,
  evidence: [],
};

export const complianceWorkflowContract = {
  workflowId: "CMP-0000",
  customerId: "CB-CUST-00000",
  policy: "RBI audit policy reference",
  status: "PENDING_REVIEW",
  assignedTo: "compliance.officer@canarabank.internal",
};

export const securityAdminActionContract = {
  actionId: "ADM-0000",
  sessionId: "SES-REGION-0000",
  action: "BLOCK_SESSION",
  requestedBy: "security.admin@canarabank.internal",
  reason: "High risk session escalation",
};
