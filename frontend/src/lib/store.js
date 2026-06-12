import {
  createContext,
  createElement,
  useContext,
  useMemo,
  useReducer,
} from "react";
import { activeSessions } from "./mock-data.js";

const VanguardContext = createContext(null);

export function getRiskProfile(score) {
  if (score <= 30) {
    return {
      label: "Low Risk",
      shortLabel: "Low",
      level: "LOW",
      status: "NORMAL",
      decision: "Passkey Allowed",
      color: "#22c55e",
      tone: "emerald",
    };
  }

  if (score <= 70) {
    return {
      label: "Medium Risk",
      shortLabel: "Medium",
      level: "MEDIUM",
      status: "ESCALATED",
      decision: "MFA Required",
      color: "#f59e0b",
      tone: "amber",
    };
  }

  return {
    label: "High Risk",
    shortLabel: "High",
    level: "HIGH",
    status: "CRITICAL",
    decision: "Blocked",
    color: "#ef4444",
    tone: "red",
  };
}

const initialState = {
  activeSessions,
  selectedSessionId: activeSessions[0]?.sessionId ?? null,
};

function normalizeTelemetryTriggers(triggers = [], sessionId) {
  return triggers.map((trigger, index) => ({
    id:
      trigger.id ??
      `${sessionId}-${trigger.timestamp ?? "telemetry"}-${index}`,
    anomaly: trigger.anomaly,
    severity: trigger.severity,
    timestamp: trigger.timestamp,
  }));
}

function vanguardReducer(state, action) {
  switch (action.type) {
    case "SELECT_SESSION": {
      return {
        ...state,
        selectedSessionId: action.payload,
      };
    }

    case "APPLY_TELEMETRY_RISK": {
      const { sessionId, payload } = action.payload;

      return {
        ...state,
        activeSessions: state.activeSessions.map((session) => {
          if (session.sessionId !== sessionId) {
            return session;
          }

          const riskScore = Math.max(0, Math.min(100, payload.risk_score));
          const riskProfile = getRiskProfile(riskScore);

          return {
            ...session,
            riskScore,
            status: riskProfile.status,
            requiresMfa: payload.requires_mfa,
            sessionBlocked: payload.session_blocked,
            triggers: normalizeTelemetryTriggers(payload.triggers, sessionId),
          };
        }),
      };
    }

    default:
      return state;
  }
}

export function getSelectedSession(state) {
  return (
    state.activeSessions.find(
      (session) => session.sessionId === state.selectedSessionId
    ) ?? state.activeSessions[0]
  );
}

export function getDashboardMetrics(sessions) {
  const totalRisk = sessions.reduce((sum, session) => sum + session.riskScore, 0);

  return {
    activeSessions: sessions.length,
    mfaRequired: sessions.filter((session) => session.requiresMfa).length,
    blockedSessions: sessions.filter((session) => session.sessionBlocked).length,
    averageRisk: Math.round(totalRisk / Math.max(1, sessions.length)),
  };
}

export function VanguardProvider({ children }) {
  const [state, dispatch] = useReducer(vanguardReducer, initialState);
  const value = useMemo(() => ({ state, dispatch }), [state]);

  return createElement(VanguardContext.Provider, { value }, children);
}

export function useVanguard() {
  const context = useContext(VanguardContext);

  if (!context) {
    throw new Error("useVanguard must be used inside VanguardProvider");
  }

  return context;
}
