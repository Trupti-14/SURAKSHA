import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone

try:
    import redis
except ModuleNotFoundError:
    redis = None


DEFAULT_TTL_SECONDS = 3600
SESSION_KEY_PREFIX = "vanguard:session:"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

_memory_sessions = {}
_redis_available = redis is not None
_RedisError = redis.RedisError if redis is not None else Exception


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


REDIS_PORT = _env_int("REDIS_PORT", 6379)
REDIS_DB = _env_int("REDIS_DB", 0)


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _session_key(session_id):
    return f"{SESSION_KEY_PREFIX}{session_id}"


def _session_id_from_key(key):
    return key.replace(SESSION_KEY_PREFIX, "", 1)


def _create_redis_client():
    if redis is None:
        return None

    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
        health_check_interval=30,
    )


_redis_client = _create_redis_client()


def _mark_redis_unavailable():
    global _redis_available
    _redis_available = False


def _redis_is_available():
    if not _redis_available or _redis_client is None:
        return False

    try:
        _redis_client.ping()
        return True
    except _RedisError:
        _mark_redis_unavailable()
        return False


def _json_dumps(data):
    try:
        return json.dumps(data, separators=(",", ":"))
    except TypeError as exc:
        raise ValueError("session data must be JSON serializable") from exc


def _json_loads(raw_value):
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("stored session data is not valid JSON") from exc


def _get_memory_record(session_id):
    record = _memory_sessions.get(session_id)

    if record is None:
        return None

    if record["expires_at"] <= time.time():
        _memory_sessions.pop(session_id, None)
        return None

    return record


def _save_memory_session(session_id, data, ttl_seconds):
    _memory_sessions[session_id] = {
        "data": deepcopy(data),
        "expires_at": time.time() + ttl_seconds,
        "ttl_seconds": ttl_seconds,
    }
    return deepcopy(data)


def _get_remaining_memory_ttl(session_id):
    record = _get_memory_record(session_id)

    if record is None:
        return DEFAULT_TTL_SECONDS

    return max(1, int(record["expires_at"] - time.time()))


def _get_remaining_redis_ttl(session_id):
    try:
        ttl_seconds = _redis_client.ttl(_session_key(session_id))
    except _RedisError:
        _mark_redis_unavailable()
        return DEFAULT_TTL_SECONDS

    if ttl_seconds is None or ttl_seconds <= 0:
        return DEFAULT_TTL_SECONDS

    return ttl_seconds


def _remaining_ttl(session_id):
    if _redis_is_available():
        return _get_remaining_redis_ttl(session_id)

    return _get_remaining_memory_ttl(session_id)


def _prepare_session_payload(existing_session, data):
    now = _utc_now()
    session = deepcopy(data)

    if existing_session and existing_session.get("created_at"):
        session["created_at"] = existing_session["created_at"]
    else:
        session.setdefault("created_at", now)

    session["updated_at"] = now
    return session


def _validate_risk_score(risk_score):
    if not isinstance(risk_score, (int, float)) or isinstance(risk_score, bool):
        raise ValueError("risk_score must be a number between 0 and 100")

    if risk_score < 0 or risk_score > 100:
        raise ValueError("risk_score must be between 0 and 100")


def _validate_dict(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a dictionary")


def save_session(session_id, data, ttl_seconds=DEFAULT_TTL_SECONDS):
    """
    Save a session object as JSON with a TTL.

    If Redis is reachable, the session is stored under
    vanguard:session:{session_id}. If Redis is unavailable, the same payload is
    stored in an in-memory fallback dictionary for local testing.
    """
    _validate_dict(data, "data")
    existing_session = get_session(session_id)
    session = _prepare_session_payload(existing_session, data)

    if _redis_is_available():
        try:
            _redis_client.setex(
                _session_key(session_id),
                ttl_seconds,
                _json_dumps(session),
            )
            return deepcopy(session)
        except _RedisError:
            _mark_redis_unavailable()

    return _save_memory_session(session_id, session, ttl_seconds)


def get_session(session_id):
    """
    Return a session dictionary by session id.

    Returns None when the session does not exist, has expired, or cannot be
    decoded from the active store.
    """
    if _redis_is_available():
        try:
            session_json = _redis_client.get(_session_key(session_id))
        except _RedisError:
            _mark_redis_unavailable()
        else:
            if session_json is None:
                return None

            try:
                return _json_loads(session_json)
            except ValueError:
                return None

    record = _get_memory_record(session_id)

    if record is None:
        return None

    return deepcopy(record["data"])


def update_session(session_id, updates):
    """
    Merge updates into an existing session and refresh updated_at.

    The original created_at timestamp is preserved. Returns the updated session
    dictionary, or None when the session does not exist.
    """
    _validate_dict(updates, "updates")
    current_session = get_session(session_id)

    if current_session is None:
        return None

    updated_session = deepcopy(current_session)
    updated_session.update(deepcopy(updates))
    updated_session["created_at"] = current_session.get("created_at", _utc_now())
    updated_session["updated_at"] = _utc_now()

    ttl_seconds = _remaining_ttl(session_id)

    if _redis_is_available():
        try:
            _redis_client.setex(
                _session_key(session_id),
                ttl_seconds,
                _json_dumps(updated_session),
            )
            return deepcopy(updated_session)
        except _RedisError:
            _mark_redis_unavailable()

    return _save_memory_session(session_id, updated_session, ttl_seconds)


def delete_session(session_id):
    """
    Delete a session from the active store.

    Returns a clean dictionary containing the session id and whether a session
    was removed.
    """
    deleted = False

    if _redis_is_available():
        try:
            deleted = bool(_redis_client.delete(_session_key(session_id)))
            return {"session_id": session_id, "deleted": deleted}
        except _RedisError:
            _mark_redis_unavailable()

    deleted = _memory_sessions.pop(session_id, None) is not None
    return {"session_id": session_id, "deleted": deleted}


def update_risk_score(session_id, risk_score):
    """
    Update the risk_score field for an existing session.

    risk_score must be numeric and between 0 and 100 inclusive. Returns the
    updated session dictionary, or None when the session does not exist.
    """
    _validate_risk_score(risk_score)
    return update_session(session_id, {"risk_score": risk_score})


def list_active_sessions():
    """
    Return all active, non-expired sessions as a list of dictionaries.

    Redis sessions are discovered with SCAN using the vanguard session
    namespace. The in-memory fallback automatically drops expired records.
    """
    if _redis_is_available():
        try:
            sessions = []
            for key in _redis_client.scan_iter(match=f"{SESSION_KEY_PREFIX}*"):
                session_json = _redis_client.get(key)

                if session_json is None:
                    continue

                try:
                    session = _json_loads(session_json)
                except ValueError:
                    continue

                session.setdefault("session_id", _session_id_from_key(key))
                sessions.append(session)

            return sessions
        except _RedisError:
            _mark_redis_unavailable()

    sessions = []

    for session_id in list(_memory_sessions):
        record = _get_memory_record(session_id)

        if record is None:
            continue

        session = deepcopy(record["data"])
        session.setdefault("session_id", session_id)
        sessions.append(session)

    return sessions
