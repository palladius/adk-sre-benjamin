import os
import sys
import argparse
from src.prompt_loader import load_prompt

def run_cli(args_list=None) -> int:
    """A piped SRE Agent CLI wrapper that accepts instruction text via stdin, 
    hydrates agent prompts with active incident state, and simulates LLM input environments.
    """
    args = args_list if args_list is not None else sys.argv[1:]
    if len(args) > 0 and args[0] == "discover":
        parser = argparse.ArgumentParser(description="GCP Resource Discovery and Asset Audit")
        parser.add_argument("--project-id", required=True, help="GCP Project ID to discover resources from")
        parsed_args = parser.parse_args(args[1:])
        from src.discovery import discover_project_resources
        try:
            results_path = discover_project_resources(parsed_args.project_id)
            print(f"Discovery complete. Results saved to: {results_path}")
            return 0
        except Exception as e:
            sys.stderr.write(f"Discovery failed: {e}\n")
            return 1

    if len(args) > 0 and args[0] == "telegram":
        import re
        from dotenv import load_dotenv
        load_dotenv() # Load local .env variables into environment context
        
        parser = argparse.ArgumentParser(description="Configure and test Telegram Alerts Integration")
        subparsers = parser.add_subparsers(dest="subcommand", required=True)
        
        set_parser = subparsers.add_parser("set", help="Set Telegram alerts configurations")
        set_parser.add_argument("chat_id", help="Telegram Chat or Channel ID")
        set_parser.add_argument("bot_token", help="Telegram Bot HTTP API Token")
        
        send_parser = subparsers.add_parser("send", help="Send a live Telegram alert message directly")
        send_parser.add_argument("message", help="Message text to send")
        
        parsed_args = parser.parse_args(args[1:])
        
        if parsed_args.subcommand == "set":
            chat_id = parsed_args.chat_id
            bot_token = parsed_args.bot_token
            
            env_path = ".env"
            env_content = ""
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_content = f.read()
            
            # Update or append TELEGRAM_CHAT_ID
            if "TELEGRAM_CHAT_ID=" in env_content:
                env_content = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID='{chat_id}'", env_content)
            else:
                env_content += f"\nTELEGRAM_CHAT_ID='{chat_id}'\n"
                
            # Update or append TELEGRAM_BOT_TOKEN
            if "TELEGRAM_BOT_TOKEN=" in env_content:
                env_content = re.sub(r"TELEGRAM_BOT_TOKEN=.*", f"TELEGRAM_BOT_TOKEN='{bot_token}'", env_content)
            else:
                env_content += f"\nTELEGRAM_BOT_TOKEN='{bot_token}'\n"
                
            with open(env_path, "w") as f:
                f.write(env_content.strip() + "\n")
                
            print(f"✅ Telegram configuration successfully saved to .env!")
            print(f"   Chat/Channel ID: {chat_id}")
            print(f"   Bot Token: {bot_token[:6]}...{bot_token[-4:] if len(bot_token) > 10 else ''}")
            return 0
            
        elif parsed_args.subcommand == "send":
            message_text = parsed_args.message
            from src.comms_telegram import send_telegram_alert
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            
            if not bot_token or not chat_id:
                sys.stderr.write("❌ Error: Telegram alerts are not configured in your .env file! Run 'telegram set' first.\n")
                return 1
                
            print(f"🚀 Dispatching live Telegram message to Chat ID {chat_id}...")
            # Bypassing local mock file feed by NOT providing feed_file_path and forcing live dispatch
            success = send_telegram_alert(message_text, "INC-CLI-DIRECT")
            if success:
                print("✅ Telegram alert successfully sent!")
                return 0
            else:
                sys.stderr.write("❌ Error: Failed to send Telegram alert. Please check your token/chat ID and internet connection.\n")
                return 1

    parser = argparse.ArgumentParser(description="Piped Agent CLI evaluation harness.")
    parser.add_argument("--agent", required=True, help="Name of the SRE Agent persona (e.g. ops_agent).")
    parser.add_argument("--incident-dir", help="Path to the active incident folder.")
    parser.add_argument("--prompt-dir", help="Path to the custom prompts directory.")
    parser.add_argument("--prompt-key", default="system_instruction", help="YAML prompt key to execute.")
    parser.add_argument("--message", "-m", help="Direct interactive message/query to send to the ADK agent.")
    
    # Parse provided args, defaulting to sys.argv if args_list is None
    parsed_args = parser.parse_args(args_list if args_list is not None else sys.argv[1:])
    
    # Load inputs from stdin
    stdin_instruction = ""
    if not sys.stdin.isatty():
        stdin_instruction = sys.stdin.read().strip()
        
    # Extract incident context variables from the active directory
    hydration_vars = {}
    if parsed_args.incident_dir and os.path.exists(parsed_args.incident_dir):
        hydration_vars["incident_id"] = os.path.basename(os.path.normpath(parsed_args.incident_dir))
        
        # Load state.md
        state_path = os.path.join(parsed_args.incident_dir, "state.md")
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                hydration_vars["state"] = f.read().strip()
                
        # Load timeline.md
        timeline_path = os.path.join(parsed_args.incident_dir, "timeline.md")
        if os.path.exists(timeline_path):
            with open(timeline_path, "r") as f:
                hydration_vars["timeline"] = f.read().strip()
                
    # Hydrate prompts via Jinja2 prompt loader
    agent_name_lower = parsed_args.agent.lower()
    # Support mapping "comms" or others to appropriate YAML file
    yaml_agent_name = agent_name_lower
    if yaml_agent_name in ["comms", "madhavi", "comms_agent"]:
        yaml_agent_name = "comms_agent"
    elif yaml_agent_name in ["ops", "opsagent"]:
        yaml_agent_name = "ops_agent"
    elif yaml_agent_name in ["planning", "planningagent"]:
        yaml_agent_name = "planning_agent"
    elif yaml_agent_name in ["logistics", "logisticsagent"]:
        yaml_agent_name = "logistics_agent"
    elif yaml_agent_name in ["commander", "benjamin", "incident_commander"]:
        yaml_agent_name = "incident_commander"
        
    try:
        system_instruction = load_prompt(
            agent_name=yaml_agent_name,
            prompt_key=parsed_args.prompt_key,
            prompt_dir=parsed_args.prompt_dir,
            **hydration_vars
        )
    except Exception as e:
        sys.stderr.write(f"Error loading agent prompts: {e}\n")
        return 1

        
    # Determine the target interactive query
    query_msg = parsed_args.message or stdin_instruction
    
    # Output structured trace logs for assert evaluation verification
    print("--- START AGENT RUN ---")
    print(f"Agent: {parsed_args.agent}")
    print(f"System Instruction:\n{system_instruction}")
    if query_msg:
        print(f"Instruction: {query_msg}")
        
        # Import and instantiate SRE agent to execute interactive ADK run
        from src.agents import (
            IncidentCommander,
            CommunicationsLead,
            OperationsLead,
            PlanningLead,
            LogisticsLead
        )
        
        agent_map = {
            "benjamin": IncidentCommander,
            "incident_commander": IncidentCommander,
            "commander": IncidentCommander,
            "comms": CommunicationsLead,
            "comms_agent": CommunicationsLead,
            "madhavi": CommunicationsLead,
            "ops": OperationsLead,
            "ops_agent": OperationsLead,
            "planning": PlanningLead,
            "planning_agent": PlanningLead,
            "logistics": LogisticsLead,
            "logistics_agent": LogisticsLead
        }
        
        if agent_name_lower in agent_map:
            agent_instance = agent_map[agent_name_lower]()
            response = agent_instance.run(query_msg)
            print(f"Response:\n{response}")
        else:
            print(f"Response (Fallback): [Agent '{parsed_args.agent}' received: '{query_msg}']")
            
    print("--- END AGENT RUN ---")
    
    return 0

if __name__ == "__main__":
    sys.exit(run_cli())
