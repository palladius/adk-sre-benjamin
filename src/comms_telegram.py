import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

def send_telegram_alert(message: str, incident_id: str, feed_file_path: str = None) -> bool:
    """Dispatches a formatted incident notification to Telegram bot or mock feed file."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # 1. Real Telegram HTTP API Dispatch
    if bot_token and chat_id and not feed_file_path:
        try:
            formatted_message = f"🏰 *[PROJECT BENJAMIN]*\n🚨 *Incident:* {incident_id}\n📢 *Alert:* {message}"
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception as e:
            print(f"[Telegram Comms Error] Failed to send live message: {e}")
            # Fallback to local logging on failure
            
    # 2. Fallback Mock Mode (writes to local JSON file for testing and Web UI consumption)
    if not feed_file_path:
        # Save to incident folder if running inside dynamic simulation
        feed_file_path = os.path.join("investigations", incident_id, "artifacts", "telegram_feed.json")
        
    try:
        os.makedirs(os.path.dirname(feed_file_path), exist_ok=True)
        
        feed_data = []
        if os.path.exists(feed_file_path):
            with open(feed_file_path, "r") as f:
                try:
                    feed_data = json.load(f)
                except Exception:
                    pass
                    
        feed_data.append({
            "timestamp": timestamp,
            "incident_id": incident_id,
            "message": message
        })
        
        with open(feed_file_path, "w") as f:
            json.dump(feed_data, f, indent=2)
        return True
    except Exception as e:
        print(f"[Telegram Comms Error] Failed to write mock payload: {e}")
        return False
