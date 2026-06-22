const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function requestComplianceJson(path, options = {}, fallbackError) {
  try {
    const { headers, ...requestOptions } = options;
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      headers: {
        Accept: "application/json",
        ...(headers ?? {}),
      },
    });

    let payload = null;

    try {
      payload = await response.json();
    } catch {
      payload = null;
    }

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        error:
          payload?.detail ??
          payload?.error ??
          fallbackError ??
          `Compliance request failed with status ${response.status}.`,
        data: payload,
      };
    }

    return payload ?? {};
  } catch (error) {
    return {
      ok: false,
      status: 0,
      error:
        fallbackError ??
        "Compliance backend is unavailable. Local fallback data remains active.",
      cause: error instanceof Error ? error.message : "Unknown network error",
    };
  }
}

export async function analyzeComplianceCircular({
  circularText,
  fileName,
  mode,
}) {
  return requestComplianceJson(
    "/api/compliance/analyze",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        circular_text: circularText,
        file_name: fileName,
        mode: mode || "offline",
      }),
    },
    "Compliance analysis backend is unavailable. Local fallback data remains active.",
  );
}

export async function analyzeComplianceCircularUpload({ file, fileName }) {
  const formData = new FormData();
  formData.append("file", file);

  if (fileName) {
    formData.append("file_name", fileName);
  }

  return requestComplianceJson(
    "/api/compliance/analyze/upload",
    {
      method: "POST",
      body: formData,
    },
    "Compliance circular upload analysis could not be completed. Please confirm the backend is running and try again.",
  );
}

export async function verifyComplianceEvidence({
  file,
  requiredEvidence,
  actionId,
}) {
  const formData = new FormData();

  if (file) {
    formData.append("file", file);
  }

  if (requiredEvidence) {
    formData.append("required_evidence", requiredEvidence);
  }

  if (actionId) {
    formData.append("action_id", actionId);
  }

  return requestComplianceJson(
    "/api/compliance/evidence/verify",
    {
      method: "POST",
      body: formData,
    },
    "Evidence verification backend is unavailable. Manual review is required.",
  );
}

export async function fetchComplianceCirculars() {
  return requestComplianceJson(
    "/api/compliance/circulars",
    { method: "GET" },
    "Compliance circulars backend is unavailable. Local circulars remain active.",
  );
}

export async function addComplianceReference(payload) {
  return requestComplianceJson(
    "/api/compliance/references",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Reference circular could not be added. Please confirm the backend is running and try again.",
  );
}

export async function uploadComplianceReference({ title, domain, category, file }) {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("domain", domain);
  formData.append("category", category || "");
  formData.append("file", file);

  return requestComplianceJson(
    "/api/compliance/references/upload",
    {
      method: "POST",
      body: formData,
    },
    "Reference circular upload could not be completed. Please confirm the backend is running and try again.",
  );
}

export async function deleteComplianceReference(circularId) {
  return requestComplianceJson(
    `/api/compliance/references/${encodeURIComponent(circularId)}`,
    { method: "DELETE" },
    "Reference circular could not be deleted. Please confirm the backend is running and try again.",
  );
}

export async function fetchComplianceActions() {
  return requestComplianceJson(
    "/api/compliance/actions",
    { method: "GET" },
    "Compliance actions backend is unavailable. Local action templates remain active.",
  );
}

export async function fetchComplianceHealth() {
  return requestComplianceJson(
    "/api/compliance/health",
    { method: "GET" },
    "Compliance health endpoint is unavailable.",
  );
}
