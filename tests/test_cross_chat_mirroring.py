import os
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.server import SREHttpRequestHandler

class MockHTTPHandler(SREHttpRequestHandler):
    def __init__(self, *args, **kwargs):
        # Prevent parent HTTP init logic from running in unit tests
        pass

@patch("src.server.send_raw_telegram_message")
@patch("src.server.parse_incident_folder")
@patch("os.path.exists")
def test_web_to_telegram_push_mirroring(mock_exists, mock_parse, mock_send_tg):
    # Set up mocks
    mock_exists.side_effect = lambda p: not p.endswith("chat.json")
    mock_parse.return_value = {
        "status": "OPEN",
        "project_id": "sre-next",
        "trigger_event": "frontend_latency_slo_violated"
    }

    # Set Telegram credentials in mocked environment
    with patch.dict(os.environ, {
        "TELEGRAM_BOT_TOKEN": "123456:mock-token",
        "TELEGRAM_CHAT_ID": "987654321"
    }):
        # Mock request context
        handler = MockHTTPHandler()
        handler.path = "/api/incidents/INC-MOCK-123/chat"
        handler.headers = {"Content-Length": "27"}
        
        # Mock rfile.read to return JSON payload
        mock_rfile = MagicMock()
        mock_rfile.read.return_value = b'{"message": "Hello from Web"}'
        handler.rfile = mock_rfile
        
        # Mock response methods
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        
        mock_wfile = MagicMock()
        handler.wfile = mock_wfile

        # Mock Incident Commander run call to bypass external LLM API query
        with patch("src.agents.IncidentCommander") as mock_commander:
            instance = MagicMock()
            instance.run.return_value = "Incident under control."
            mock_commander.return_value = instance

            # Mock file open for writing central chat.json log using builtins mock_open
            with patch("builtins.open", mock_open()):
                handler.do_POST()

        # Verify that send_raw_telegram_message was triggered for BOTH:
        # 1. The Operator Message
        # 2. Benjamin's IC response
        assert mock_send_tg.call_count == 2
        
        # First call is the Operator's message
        args1, kwargs1 = mock_send_tg.call_args_list[0]
        assert args1[0] == "123456:mock-token"
        assert args1[1] == "987654321"
        assert "💬 *[Web Operator]:* Hello from Web" in args1[2]

        # Second call is Benjamin's response
        args2, kwargs2 = mock_send_tg.call_args_list[1]
        assert args2[0] == "123456:mock-token"
        assert args2[1] == "987654321"
        commander_name = os.getenv("COMMANDER_NAME") or os.getenv("INCIDENT_COMMANDER_NAME") or "Benjamin"
        assert f"🏰 *{commander_name} (IC):*" in args2[2]
        assert "Incident under control." in args2[2]
