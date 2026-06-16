import os
import json
import asyncio
from datetime import datetime, timezone
import discord

async def async_create_discord_channel(token: str, guild_id: int, name: str) -> dict:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    res = {}
    
    @client.event
    async def on_ready():
        try:
            guild = client.get_guild(guild_id)
            if not guild:
                guild = await client.fetch_guild(guild_id)
            if guild:
                # Discord channel names must be lowercase and contain no spaces
                clean_name = name.lower().replace(" ", "-")
                channel = await guild.create_text_channel(clean_name)
                res["channel_id"] = channel.id
                res["channel_name"] = channel.name
            else:
                res["error"] = f"Guild {guild_id} not found"
        except Exception as e:
            res["error"] = str(e)
        finally:
            await client.close()
            
    try:
        await client.start(token)
    except Exception as e:
        res["error"] = str(e)
    return res

def create_discord_channel(incident_id: str, token: str = None, guild_id: str = None, feed_file_path: str = None) -> dict:
    token = token or os.getenv("DISCORD_BOT_TOKEN")
    guild_id = guild_id or os.getenv("DISCORD_GUILD_ID")
    
    # Clean up incident_id for channel name
    clean_incident = incident_id.lower().replace(" ", "-")
    channel_name = f"war-room-{clean_incident}"
    
    if not token or not guild_id:
        # Mock mode fallback
        feed_file_path = feed_file_path or os.getenv("DISCORD_FEED_FILE_PATH") or "investigations/discord_feed.json"
        
        # Ensure parent directory exists
        log_dir = os.path.dirname(feed_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        mock_data = {
            "incident_id": incident_id,
            "channel_name": channel_name,
            "channel_id": 123456789012345678,
            "mock": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            feed = []
            if os.path.exists(feed_file_path):
                with open(feed_file_path, "r", encoding="utf-8") as f:
                    feed = json.load(f)
            feed.append(mock_data)
            with open(feed_file_path, "w", encoding="utf-8") as f:
                json.dump(feed, f, indent=2)
        except Exception:
            pass
            
        return mock_data

    # Live mode using discord.py client
    try:
        guild_id_int = int(guild_id)
        
        # Run async loop to handle connection and channel creation
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # If loop is already running, run it in thread or schedule it
            # But in standard script execution, get_event_loop is not running
            future = asyncio.run_coroutine_threadsafe(
                async_create_discord_channel(token, guild_id_int, channel_name), loop
            )
            result = future.result(timeout=30)
        else:
            result = loop.run_until_complete(async_create_discord_channel(token, guild_id_int, channel_name))
        return result
    except Exception as e:
        return {"error": str(e)}
