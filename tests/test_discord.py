import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.incident import IncidentContext
from src.comms_discord import create_discord_channel
from src.agents.comms import CommunicationsLead

def test_discord_mock_mode(tmp_path, monkeypatch):
    # Ensure no actual Discord variables are set
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_GUILD_ID", raising=False)
    
    feed_path = os.path.join(tmp_path, "discord_feed.json")
    
    result = create_discord_channel(
        incident_id="INC-20260616-TEST",
        feed_file_path=feed_path
    )
    
    assert result["mock"] is True
    assert result["channel_name"] == "war-room-inc-20260616-test"
    assert result["channel_id"] == 123456789012345678
    assert os.path.exists(feed_path)
    
    with open(feed_path, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["incident_id"] == "INC-20260616-TEST"
        assert data[0]["channel_name"] == "war-room-inc-20260616-test"

@patch("src.comms_discord.async_create_discord_channel")
def test_discord_live_mode_mocked(mock_async_create):
    mock_async_create.return_value = {
        "channel_id": 987654321098765432,
        "channel_name": "war-room-inc-20260616-live"
    }
    
    result = create_discord_channel(
        incident_id="INC-20260616-LIVE",
        token="mock-token-xyz",
        guild_id="999888777"
    )
    
    assert "error" not in result
    assert result["channel_id"] == 987654321098765432
    assert result["channel_name"] == "war-room-inc-20260616-live"
    mock_async_create.assert_called_once_with("mock-token-xyz", 999888777, "war-room-inc-20260616-live")

def test_comms_lead_discord_channel_creation(tmp_path, monkeypatch):
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_GUILD_ID", raising=False)
    
    feed_path = os.path.join(tmp_path, "discord_feed.json")
    monkeypatch.setenv("DISCORD_FEED_FILE_PATH", feed_path)
    
    ctx = IncidentContext(incident_uuid="test-uuid-comms-discord", incident_id="INC-DISCORD-COMMS")
    cl = CommunicationsLead(incident_context=ctx)
    
    # We want to verify CommunicationsLead has a method to initialize the war-room
    # and that it returns the channel info.
    channel_info = cl.create_discord_war_room()
    
    assert channel_info["mock"] is True
    assert channel_info["channel_name"] == "war-room-inc-discord-comms"
    assert os.path.exists(feed_path)
