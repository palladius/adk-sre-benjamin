# PostgreSQL Database Integration for Project Benjamin
import os
import json
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db")

_pool = None

def is_db_configured() -> bool:
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    return bool(host and user)

def is_db_active() -> bool:
    return _pool is not None

def _resolve_db_env() -> str:
    """Resolves and validates the canonical environment ('production', 'development', or 'test') for DB scoping."""
    from src.incident import resolve_benjamin_env
    env = resolve_benjamin_env()
    if env not in ("production", "development", "test"):
        raise ValueError(f"Unexpected canonical environment: {env}")
    return env


def _resolve_active_state_row_id() -> int:
    """Maps BENJAMIN_ENV to a distinct active_state row ID (production=1, development=2, test=3) so environments never clobber each other."""
    env = _resolve_db_env()
    return {"production": 1, "development": 2, "test": 3}[env]


def init_db():
    global _pool
    env = _resolve_db_env()
    if not is_db_configured():
        logger.info("PostgreSQL credentials not configured. Using local filesystem storage fallback.")
        return
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    if not db_name:
        db_name = f"sredb_{env}"
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    try:
        logger.info(f"Initializing ThreadedConnectionPool to {db_user}@{db_host}:{db_port}/{db_name}...")
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1, 20,
            user=db_user,
            password=db_pass,
            database=db_name,
            host=db_host,
            port=db_port
        )
        create_schema()
        logger.info("Database connection pool and schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        _pool = None

@contextmanager
def get_db_connection():
    global _pool
    if not _pool:
        raise RuntimeError("Database connection pool is not initialized")
    
    conn = None
    try:
        conn = _pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        logger.warning(f"Database connection check failed, attempting to reinitialize pool: {e}")
        if conn:
            try:
                _pool.putconn(conn, close=True)
            except Exception:
                pass
        try:
            _pool.closeall()
        except Exception:
            pass
        _pool = None
        init_db()
        if not _pool:
            raise RuntimeError("Database connection lost and failed to reconnect")
        conn = _pool.getconn()
        
    try:
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and _pool:
            try:
                _pool.putconn(conn)
            except Exception:
                pass

def create_schema():
    ddl = """
    CREATE TABLE IF NOT EXISTS active_state (
        id INT PRIMARY KEY,
        project_id VARCHAR(255) NOT NULL,
        incident_id VARCHAR(255) NOT NULL,
        incident_status VARCHAR(50) NOT NULL,
        substatus_rca BOOLEAN DEFAULT FALSE,
        substatus_mitigated BOOLEAN DEFAULT FALSE,
        substatus_fixed BOOLEAN DEFAULT FALSE,
        substatus_verified BOOLEAN DEFAULT FALSE
    );
    
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id VARCHAR(255) PRIMARY KEY,
        env VARCHAR(32) NOT NULL DEFAULT 'production',
        status VARCHAR(50) NOT NULL DEFAULT 'NEW',
        substatus_rca BOOLEAN DEFAULT FALSE,
        substatus_mitigated BOOLEAN DEFAULT FALSE,
        substatus_fixed BOOLEAN DEFAULT FALSE,
        substatus_verified BOOLEAN DEFAULT FALSE,
        project_id VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN',
        domain_id VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN',
        trigger_event TEXT NOT NULL DEFAULT 'UNKNOWN',
        incident_uuid VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN',
        timeline JSONB DEFAULT '[]'::jsonb,
        artifacts JSONB DEFAULT '[]'::jsonb,
        archived BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ALTER TABLE incidents ADD COLUMN IF NOT EXISTS env VARCHAR(32) NOT NULL DEFAULT 'production';

    CREATE TABLE IF NOT EXISTS chats (
        id SERIAL PRIMARY KEY,
        env VARCHAR(32) NOT NULL DEFAULT 'production',
        incident_id VARCHAR(255) NOT NULL,
        sender VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    ALTER TABLE chats ADD COLUMN IF NOT EXISTS env VARCHAR(32) NOT NULL DEFAULT 'production';
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            logger.info("Database schema verified/created.")

def save_active_state(state: dict) -> bool:
    if not is_db_active():
        return False
    row_id = _resolve_active_state_row_id()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO active_state (id, project_id, incident_id, incident_status, substatus_rca, substatus_mitigated, substatus_fixed, substatus_verified)
                    VALUES ({row_id}, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        project_id = EXCLUDED.project_id,
                        incident_id = EXCLUDED.incident_id,
                        incident_status = EXCLUDED.incident_status,
                        substatus_rca = EXCLUDED.substatus_rca,
                        substatus_mitigated = EXCLUDED.substatus_mitigated,
                        substatus_fixed = EXCLUDED.substatus_fixed,
                        substatus_verified = EXCLUDED.substatus_verified;
                    """,
                    (
                        state.get("project_id", "sre-next"),
                        state.get("incident_id", "None"),
                        state.get("incident_status", "NEW"),
                        state.get("substatus_rca", False),
                        state.get("substatus_mitigated", False),
                        state.get("substatus_fixed", False),
                        state.get("substatus_verified", False)
                    )
                )
        return True
    except Exception as e:
        logger.error(f"Failed to save active state to DB: {e}")
        return False

def get_active_state(default_state: dict = None, raise_on_error: bool = False) -> dict:
    if not is_db_active():
        if raise_on_error:
            raise RuntimeError("Database is not active")
        return default_state
    row_id = _resolve_active_state_row_id()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT project_id, incident_id, incident_status, substatus_rca, substatus_mitigated, substatus_fixed, substatus_verified
                    FROM active_state WHERE id = {row_id};
                    """,
                )
                row = cur.fetchone()
                if row:
                    return {
                        "project_id": row[0],
                        "incident_id": row[1],
                        "incident_status": row[2],
                        "substatus_rca": row[3],
                        "substatus_mitigated": row[4],
                        "substatus_fixed": row[5],
                        "substatus_verified": row[6]
                    }
    except Exception as e:
        logger.error(f"Failed to retrieve active state from DB: {e}")
        if raise_on_error:
            raise
    return default_state

def save_incident(details: dict) -> bool:
    if not is_db_active():
        return False
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO incidents (incident_id, env, status, substatus_rca, substatus_mitigated, substatus_fixed, substatus_verified, project_id, domain_id, trigger_event, incident_uuid, timeline, artifacts, archived)
                    VALUES (%s, '{env}', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (incident_id) DO UPDATE SET
                        env = EXCLUDED.env,
                        status = EXCLUDED.status,
                        substatus_rca = EXCLUDED.substatus_rca,
                        substatus_mitigated = EXCLUDED.substatus_mitigated,
                        substatus_fixed = EXCLUDED.substatus_fixed,
                        substatus_verified = EXCLUDED.substatus_verified,
                        project_id = EXCLUDED.project_id,
                        domain_id = EXCLUDED.domain_id,
                        trigger_event = EXCLUDED.trigger_event,
                        incident_uuid = EXCLUDED.incident_uuid,
                        timeline = EXCLUDED.timeline,
                        artifacts = EXCLUDED.artifacts,
                        archived = EXCLUDED.archived;
                    """,
                    (
                        details["incident_id"],
                        details.get("status", "NEW"),
                        details.get("substatus_rca", False),
                        details.get("substatus_mitigated", False),
                        details.get("substatus_fixed", False),
                        details.get("substatus_verified", False),
                        details.get("project_id", "UNKNOWN"),
                        details.get("domain_id", "UNKNOWN"),
                        details.get("trigger_event", "UNKNOWN"),
                        details.get("incident_uuid", "UNKNOWN"),
                        json.dumps(details.get("timeline", [])),
                        json.dumps(details.get("artifacts", [])),
                        details.get("archived", False)
                    )
                )
        return True
    except Exception as e:
        logger.error(f"Failed to save incident {details.get('incident_id')} to DB: {e}")
        return False

def get_incident(incident_id: str, raise_on_error: bool = False) -> dict:
    if not is_db_active():
        return None
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT status, substatus_rca, substatus_mitigated, substatus_fixed, substatus_verified, project_id, domain_id, trigger_event, incident_uuid, timeline, artifacts, archived
                    FROM incidents WHERE incident_id = %s AND env = '{env}';
                    """,
                    (incident_id,)
                )
                row = cur.fetchone()
                if row:
                    timeline = row[9] if isinstance(row[9], (list, dict)) else json.loads(row[9] or '[]')
                    artifacts = row[10] if isinstance(row[10], (list, dict)) else json.loads(row[10] or '[]')
                    return {
                        "incident_id": incident_id,
                        "status": row[0],
                        "substatus_rca": row[1],
                        "substatus_mitigated": row[2],
                        "substatus_fixed": row[3],
                        "substatus_verified": row[4],
                        "project_id": row[5],
                        "domain_id": row[6],
                        "trigger_event": row[7],
                        "incident_uuid": row[8],
                        "timeline": timeline,
                        "artifacts": artifacts,
                        "archived": row[11]
                    }
    except Exception as e:
        logger.error(f"Failed to get incident {incident_id} from DB: {e}")
        if raise_on_error:
            raise
    return None

def list_incidents() -> list[dict]:
    if not is_db_active():
        return []
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT incident_id, status, project_id, trigger_event, archived
                    FROM incidents
                    WHERE env = '{env}'
                    ORDER BY incident_id DESC;
                    """
                )
                rows = cur.fetchall()
                incidents = []
                for row in rows:
                    incidents.append({
                        "id": row[0],
                        "status": row[1],
                        "project_id": row[2],
                        "trigger_event": row[3],
                        "archived": row[4]
                    })
                return incidents
    except Exception as e:
        logger.error(f"Failed to list incidents from DB: {e}")
    return []

def get_top_5_incidents() -> list[dict]:
    if not is_db_active():
        return None
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT incident_id, status, substatus_rca, substatus_mitigated, substatus_fixed, substatus_verified
                    FROM incidents
                    WHERE NOT archived AND env = '{env}'
                    ORDER BY incident_id DESC
                    LIMIT 5;
                    """,
                )
                rows = cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "status": r[1].upper(),
                        "substatus_rca": bool(r[2]) if len(r) > 2 else False,
                        "substatus_mitigated": bool(r[3]) if len(r) > 3 else False,
                        "substatus_fixed": bool(r[4]) if len(r) > 4 else False,
                        "substatus_verified": bool(r[5]) if len(r) > 5 else False,
                    }
                    for r in rows
                ]
    except Exception as e:
        logger.error(f"Failed to get top 5 incidents from DB: {e}")
    return None

def add_chat_message(incident_id: str, sender: str, message: str, timestamp: str = None) -> bool:
    if not is_db_active():
        return False
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if timestamp:
                    cur.execute(
                        f"""
                        INSERT INTO chats (env, incident_id, sender, message, timestamp)
                        VALUES ('{env}', %s, %s, %s, %s);
                        """,
                        (incident_id, sender, message, timestamp)
                    )
                else:
                    cur.execute(
                        f"""
                        INSERT INTO chats (env, incident_id, sender, message)
                        VALUES ('{env}', %s, %s, %s);
                        """,
                        (incident_id, sender, message)
                    )
        return True
    except Exception as e:
        logger.error(f"Failed to add chat message to DB: {e}")
        return False

def get_chat_messages(incident_id: str) -> list[dict]:
    if not is_db_active():
        return None
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT sender, message, timestamp
                    FROM chats
                    WHERE incident_id = %s AND env = '{env}'
                    ORDER BY id ASC;
                    """,
                    (incident_id,)
                )
                rows = cur.fetchall()
                messages = []
                for row in rows:
                    ts = row[2]
                    if hasattr(ts, "isoformat"):
                        ts_str = ts.isoformat().replace("+00:00", "Z")
                    else:
                        ts_str = str(ts)
                    messages.append({
                        "sender": row[0],
                        "message": row[1],
                        "timestamp": ts_str
                    })
                return messages
    except Exception as e:
        logger.error(f"Failed to get chat messages from DB: {e}")
    return None

def save_chat_messages(incident_id: str, chat_data: list) -> bool:
    if not is_db_active():
        return False
    env = _resolve_db_env()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM chats WHERE incident_id = %s AND env = '{env}';", (incident_id,))
                for msg in chat_data:
                    ts = msg.get("timestamp")
                    if ts:
                        cur.execute(
                            f"""
                            INSERT INTO chats (env, incident_id, sender, message, timestamp)
                            VALUES ('{env}', %s, %s, %s, %s);
                            """,
                            (incident_id, msg.get("sender"), msg.get("message"), ts)
                        )
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO chats (env, incident_id, sender, message)
                            VALUES ('{env}', %s, %s, %s);
                            """,
                            (incident_id, msg.get("sender"), msg.get("message"))
                        )
        return True
    except Exception as e:
        logger.error(f"Failed to save bulk chat messages to DB: {e}")
        return False
