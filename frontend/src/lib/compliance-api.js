const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export async function analyzeComplianceCircular({
  circularText,
  fileName,
  mode,
}) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/compliance/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        circular_text: circularText,
        file_name: fileName,
        mode: mode || "offline",
      }),
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
          `Compliance analysis failed with status ${response.status}.`,
        data: payload,
      };
    }

    return payload ?? {};
  } catch (error) {
    return {
      ok: false,
      status: 0,
      error:
        "Compliance analysis backend is unavailable. Local fallback data remains active.",
      cause: error instanceof Error ? error.message : "Unknown network error",
    };
  }
}
