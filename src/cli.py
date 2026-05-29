import os
import sys
import argparse
from src.prompt_loader import load_prompt

def run_cli(args_list=None) -> int:
    """A piped SRE Agent CLI wrapper that accepts instruction text via stdin, 
    hydrates agent prompts with active incident state, and simulates LLM input environments.
    """
    parser = argparse.ArgumentParser(description="Piped Agent CLI evaluation harness.")
    parser.add_argument("--agent", required=True, help="Name of the SRE Agent persona (e.g. ops_agent).")
    parser.add_argument("--incident-dir", help="Path to the active incident folder.")
    parser.add_argument("--prompt-dir", help="Path to the custom prompts directory.")
    parser.add_argument("--prompt-key", default="system_instruction", help="YAML prompt key to execute.")
    
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
    try:
        system_instruction = load_prompt(
            agent_name=parsed_args.agent,
            prompt_key=parsed_args.prompt_key,
            prompt_dir=parsed_args.prompt_dir,
            **hydration_vars
        )
    except Exception as e:
        sys.stderr.write(f"Error loading agent prompts: {e}\n")
        return 1
        
    # Output structured trace logs for assert evaluation verification
    print("--- START AGENT RUN ---")
    print(f"Agent: {parsed_args.agent}")
    print(f"System Instruction:\n{system_instruction}")
    if stdin_instruction:
        print(f"Instruction: {stdin_instruction}")
    print("--- END AGENT RUN ---")
    
    return 0

if __name__ == "__main__":
    sys.exit(run_cli())
