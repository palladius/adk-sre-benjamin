import os
import json
import pytest
from unittest.mock import patch, MagicMock
import psycopg2

import src.db as db
from src.server import (
    get_active_state,
    save_active_state,
    load_chat_data,
    save_chat_data,
    parse_incident_folder,
    get_incidents_list,
)

@pytest.fixture(autouse=True)
def reset_db_pool():
    # Store old pool and config
    old_pool = db._pool
    db._pool = None
    yield
    # Restore pool
    db._pool = old_pool

def test_is_db_configured_logic():
    # Case 1: Configured
    with patch.dict(os.environ, {"DB_HOST": "localhost", "DB_USER": "test_user"}):
        assert db.is_db_configured() is True

    # Case 2: Missing host
    with patch.dict(os.environ, {"DB_USER": "test_user"}):
        if "DB_HOST" in os.environ:
            del os.environ["DB_HOST"]
        assert db.is_db_configured() is False

    # Case 3: Missing user
    with patch.dict(os.environ, {"DB_HOST": "localhost"}):
        if "DB_USER" in os.environ:
            del os.environ["DB_USER"]
        assert db.is_db_configured() is False

def test_fallback_when_db_inactive(tmp_path):
    # Ensure pool is None
    assert not db.is_db_active()

    temp_active_state_file = tmp_path / "active_state.json"
    temp_chat_file = tmp_path / "chat.json"

    with patch("src.server.get_active_state_file", return_value=str(temp_active_state_file)):
        # Test default active state
        state = get_active_state()
        assert state["project_id"] == "sre-next"
        assert state["incident_status"] == "NEW"

        # Save active state to file
        state["incident_status"] = "ONGOING"
        save_active_state(state)
        assert temp_active_state_file.exists()

        # Read back
        state2 = get_active_state()
        assert state2["incident_status"] == "ONGOING"

    # Chat fallback test
    chat_path = str(temp_chat_file)
    chat_data = [{"sender": "System", "message": "Fallback test", "timestamp": "2026-06-16T12:00:00Z"}]
    
    save_chat_data("INC-123", str(tmp_path), chat_data)
    assert temp_chat_file.exists()

    loaded_chat = load_chat_data("INC-123", str(tmp_path))
    assert len(loaded_chat) == 1
    assert loaded_chat[0]["message"] == "Fallback test"

@patch("psycopg2.pool.ThreadedConnectionPool")
def test_db_active_operations(mock_pool_cls, tmp_path):
    # Setup mock pool, connection and cursor
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    mock_pool_cls.return_value = mock_pool
    mock_pool.getconn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    # Enable DB via env variables
    with patch.dict(os.environ, {
        "DB_HOST": "127.0.0.1",
        "DB_USER": "benjamin",
        "DB_PASS": "pass",
        "DB_NAME": "sredb"
    }):
        db.init_db()
        assert db.is_db_active() is True

        # 1. Test save_active_state
        state = {
            "project_id": "db-project",
            "incident_id": "INC-DB-1",
            "incident_status": "INVESTIGATING",
            "substatus_rca": True
        }
        res = db.save_active_state(state)
        assert res is True
        mock_cur.execute.assert_any_call(
            any_sql_containing("INSERT INTO active_state"),
            (
                "db-project",
                "INC-DB-1",
                "INVESTIGATING",
                True,
                False,
                False,
                False
            )
        )

        # 2. Test get_active_state
        mock_cur.fetchone.return_value = (
            "db-project",
            "INC-DB-1",
            "INVESTIGATING",
            True,
            False,
            False,
            False
        )
        state_ret = db.get_active_state({})
        assert state_ret["project_id"] == "db-project"
        assert state_ret["incident_id"] == "INC-DB-1"
        assert state_ret["incident_status"] == "INVESTIGATING"
        assert state_ret["substatus_rca"] is True

        # 3. Test save_incident
        details = {
            "incident_id": "INC-DB-1",
            "status": "INVESTIGATING",
            "substatus_rca": True,
            "project_id": "db-project",
            "trigger_event": "alert",
            "timeline": [{"agent": "IC", "message": "Start"}]
        }
        res_inc = db.save_incident(details)
        assert res_inc is True

        # 4. Test save_chat_messages / load_chat_data
        chat_data = [{"sender": "IC", "message": "Hi", "timestamp": "2026"}]
        save_chat_data("INC-DB-1", str(tmp_path), chat_data)
        
        # Verify chats are loaded from DB
        mock_cur.fetchall.return_value = [("IC", "Hi", "2026")]
        loaded = load_chat_data("INC-DB-1", str(tmp_path))
        assert len(loaded) == 1
        assert loaded[0]["sender"] == "IC"
        assert loaded[0]["message"] == "Hi"

def test_connection_resilience(tmp_path):
    # Setup mock pool, connection and cursor
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # We raise OperationalError on connection test to trigger resilience logic
    mock_cur.execute.side_effect = psycopg2.OperationalError("Lost connection")
    mock_pool.getconn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    db._pool = mock_pool
    
    # Mock init_db to NOT set _pool (simulating failed reconnection)
    with patch("src.db.init_db") as mock_init:
        def fail_pool():
            db._pool = None
        mock_init.side_effect = fail_pool
        
        # This should fail to reconnect and raise RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            with db.get_db_connection():
                pass
        assert "Database connection lost and failed to reconnect" in str(excinfo.value)

class any_sql_containing:
    def __init__(self, substring):
        self.substring = substring
    def __eq__(self, other):
        return isinstance(other, str) and self.substring in other
    def __repr__(self):
        return f"SQL containing '{self.substring}'"
