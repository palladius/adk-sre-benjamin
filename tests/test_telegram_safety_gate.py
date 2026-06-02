import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.server import send_telegram_safety_gate_menu

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_send_telegram_safety_gate_menu(mock_request, mock_urlopen):
    # Mock return values for urlopen
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    bot_token = "mock-bot-token"
    chat_id = "123456789"
    message = "⚠️ Safety Gate Hold! Proceed?"

    send_telegram_safety_gate_menu(bot_token, chat_id, message)

    # Verify that urllib.request.Request was called with correct parameters
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    url = args[0]
    
    assert f"https://api.telegram.org/bot{bot_token}/sendMessage" in url
    assert kwargs.get("method") == "POST"

    # Verify data encoded format contains safety gate buttons
    data = kwargs.get("data")
    if not data and len(args) > 1:
        data = args[1]
        
    import urllib.parse
    decoded_params = urllib.parse.parse_qs(data.decode("utf-8"))
    
    assert decoded_params["chat_id"][0] == chat_id
    assert decoded_params["text"][0] == message
    assert "reply_markup" in decoded_params
    
    reply_markup = json.loads(decoded_params["reply_markup"][0])
    assert "keyboard" in reply_markup
    buttons = reply_markup["keyboard"][0]
    assert buttons[0]["text"] == "✅ Yes, I am sure"
    assert buttons[1]["text"] == "❌ No, abort mutation"
