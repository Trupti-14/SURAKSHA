from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from engines.behavioral.mfa import evaluate_mfa
from engines.session_store import save_session, get_session, update_risk_score, list_active_sessions, delete_session
from api.compliance import router as compliance_router

app = FastAPI(title="Vanguard Security API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compliance_router)

@app.get("/")
def root():
    return {"status": "Vanguard API Online", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/mfa/evaluate")
def evaluate_mfa_endpoint(payload: dict):
    risk_score = payload.get("risk_score", 0)
    return evaluate_mfa(risk_score)

@app.post("/api/session/save")
def save_session_endpoint(payload: dict):
    session_id = payload.get("session_id")
    data = payload.get("data", {})
    return save_session(session_id, data)

@app.get("/api/session/{session_id}")
def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if session is None:
        return {"error": "Session not found"}
    return session

@app.post("/api/session/{session_id}/risk")
def update_risk_endpoint(session_id: str, payload: dict):
    risk_score = payload.get("risk_score", 0)
    return update_risk_score(session_id, risk_score)

@app.get("/api/sessions")
def list_sessions_endpoint():
    return list_active_sessions()

@app.delete("/api/session/{session_id}")
def delete_session_endpoint(session_id: str):
    return delete_session(session_id)