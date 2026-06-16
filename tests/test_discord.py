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

@pytest.mark.asyncio
async def test_mention_routing_ops_agent():
    # Mock message
    mock_message = MagicMock()
    mock_message.author.bot = False
    mock_message.content = "@OpsAgent check database CPU"
    mock_message.channel.name = "war-room-inc-20260616-b7b7"
    mock_message.reply = AsyncMock()
    
    # Mock OperationsLead run method
    with patch("src.agents.OperationsLead.run") as mock_run:
        mock_run.return_value = "[OpsAgent] CPU utilization is at 45%."
        
        from src.comms_discord import handle_discord_message
        handled = await handle_discord_message(mock_message)
        
        assert handled is True
        mock_run.assert_called_once_with("check database CPU")
        mock_message.reply.assert_called_once_with("[OpsAgent] CPU utilization is at 45%.")

@pytest.mark.asyncio
async def test_mention_routing_benjamin():
    # Mock message
    mock_message = MagicMock()
    mock_message.author.bot = False
    mock_message.content = "@Benjamin what is the status?"
    mock_message.channel.name = "war-room-inc-20260616-b7b7"
    mock_message.reply = AsyncMock()
    
    # Mock IncidentCommander run method
    with patch("src.agents.IncidentCommander.run") as mock_run:
        mock_run.return_value = "[Benjamin] Standing by. I can declare SRE incidents active."
        
        from src.comms_discord import handle_discord_message
        handled = await handle_discord_message(mock_message)
        
        assert handled is True
        mock_run.assert_called_once_with("what is the status?")
        mock_message.reply.assert_called_once_with("[Benjamin] Standing by. I can declare SRE incidents active.")

@pytest.mark.asyncio
async def test_message_no_mention():
    mock_message = MagicMock()
    mock_message.author.bot = False
    mock_message.content = "Just some standard chat text without mentions"
    mock_message.channel.name = "war-room-inc-20260616-b7b7"
    mock_message.reply = AsyncMock()
    
    from src.comms_discord import handle_discord_message
    handled = await handle_discord_message(mock_message)
    
    assert handled is False
    mock_message.reply.assert_not_called()

@pytest.mark.asyncio
async def test_message_from_bot():
    mock_message = MagicMock()
    mock_message.author.bot = True
    mock_message.content = "@OpsAgent do something"
    mock_message.channel.name = "war-room-inc-20260616-b7b7"
    mock_message.reply = AsyncMock()
    
    from src.comms_discord import handle_discord_message
    handled = await handle_discord_message(mock_message)
    
    assert handled is False
    mock_message.reply.assert_not_called()

