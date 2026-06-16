import os
import sys
import json
import threading
from datetime import datetime, timezone

# Define a mock/noop trace context if opentelemetry is not installed
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

# Import Google Cloud Logging if installed
try:
    from google.cloud import logging as cloud_logging
    HAS_CLOUD_LOGGING = True
except ImportError:
    HAS_CLOUD_LOGGING = False

_current_agent = threading.local()

def init_tracer():
    if not HAS_OTEL:
        print("[Observability] OpenTelemetry is not installed. Tracing is disabled.")
        return
        
    try:
        # Check if already initialized to avoid duplicate providers
        try:
            provider = trace.get_tracer_provider()
            if hasattr(provider, "add_span_processor"):
                return
        except Exception:
            pass

        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        
        # Determine which exporter to use
        exporter_set = False
        
        # 1. Check if Cloud Run or Google Cloud Project is set
        is_cloud_run = os.environ.get("K_SERVICE") is not None
        gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
        
        if is_cloud_run or (gcp_project and os.environ.get("OTEL_TRACES_EXPORTER") == "gcp"):
            try:
                from opentelemetry.exporter.gcp.trace import CloudTraceSpanExporter
                exporter = CloudTraceSpanExporter(project_id=gcp_project)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                print(f"[Observability] Configured Google Cloud Trace Exporter for project: {gcp_project or 'auto'}")
                exporter_set = True
            except Exception as e:
                print(f"[Observability] Failed to initialize Google Cloud Trace Exporter: {e}")
                
        # 2. Check if OTLP is configured
        if not exporter_set and os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(exporter))
                print("[Observability] Configured OTLP gRPC Span Exporter.")
                exporter_set = True
            except Exception as e:
                print(f"[Observability] Failed to initialize OTLP Exporter: {e}")
                
        # 3. Fallback to console or no-op
        if not exporter_set:
            if os.environ.get("OTEL_CONSOLE_EXPORTER") == "true":
                try:
                    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                    exporter = ConsoleSpanExporter()
                    provider.add_span_processor(SimpleSpanProcessor(exporter))
                    print("[Observability] Configured Console Span Exporter.")
                except Exception as e:
                    print(f"[Observability] Failed to initialize Console Exporter: {e}")
            else:
                # No active exporter configured
                print("[Observability] No-op tracer initialized (no active exporter configured).")
    except Exception as err:
        print(f"[Observability] Error during tracer setup: {err}")

def log_to_gcp_async(client, payload, severity):
    def _log():
        try:
            logger = client.logger("benjamin-audit")
            logger.log_struct(payload, severity=severity)
        except Exception as e:
            sys.stderr.write(f"[Observability] Failed to log to GCP Cloud Logging: {e}\n")
            
    threading.Thread(target=_log, daemon=True).start()

def log_audit_event(incident_context, sender_agent: str, receiver_agent: str, message: str, severity: str = "INFO", context: dict = None):
    # Determine the log path
    log_path = os.getenv("BENJAMIN_AUDIT_LOG_PATH", "logs/benjamin-audit.jsonl")
    
    # Ensure directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            # Fallback path if directory cannot be created
            fallback_dir = "/tmp" if os.name != "nt" else os.getenv("TEMP", ".")
            log_path = os.path.join(fallback_dir, os.path.basename(log_path))
            log_dir = fallback_dir
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                pass
                
    # Simple log rotation if file exceeds 10MB
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    if os.path.exists(log_path):
        try:
            if os.path.getsize(log_path) > MAX_BYTES:
                # Rotate
                for i in range(5, 0, -1):
                    old_file = f"{log_path}.{i}"
                    new_file = f"{log_path}.{i+1}"
                    if os.path.exists(old_file):
                        try:
                            os.rename(old_file, new_file)
                        except Exception:
                            pass
                try:
                    os.rename(log_path, f"{log_path}.1")
                except Exception:
                    pass
        except Exception:
            pass

    # Extract incident_uuid and incident_id
    incident_uuid = "UNKNOWN"
    incident_id = "UNKNOWN"
    if incident_context is not None:
        if hasattr(incident_context, "incident_uuid"):
            incident_uuid = incident_context.incident_uuid
        elif isinstance(incident_context, dict):
            incident_uuid = incident_context.get("incident_uuid", "UNKNOWN")
            
        if hasattr(incident_context, "incident_id"):
            incident_id = incident_context.incident_id
        elif hasattr(incident_context, "metadata") and isinstance(incident_context.metadata, dict):
            incident_id = incident_context.metadata.get("incident_id", "UNKNOWN")
            incident_uuid = incident_context.metadata.get("incident_uuid", incident_uuid)
        elif isinstance(incident_context, dict):
            incident_id = incident_context.get("incident_id", "UNKNOWN")

    timestamp = datetime.now(timezone.utc).isoformat()
    audit_entry = {
        "timestamp": timestamp,
        "incident_uuid": incident_uuid,
        "incident_id": incident_id,
        "sender agent": sender_agent,
        "sender_agent": sender_agent,
        "receiver agent": receiver_agent,
        "receiver_agent": receiver_agent,
        "message": message,
        "severity": severity,
        "context": context or {}
    }
    
    # Write to local file
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")
            text_line = f"[{timestamp}] [{severity}] [{incident_id}] [{incident_uuid}] {sender_agent} -> {receiver_agent}: {message}"
            f.write(text_line + "\n")
    except Exception as e:
        sys.stderr.write(f"[Audit Fallback] Failed to write log: {e}\n")
        sys.stderr.write(json.dumps(audit_entry) + "\n")
        
    # Write to Google Cloud Logging
    if HAS_CLOUD_LOGGING:
        try:
            project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
            client = cloud_logging.Client(project=project_id)
            log_to_gcp_async(client, audit_entry, severity)
        except Exception as e:
            # Fallback/ignore so we don't crash
            sys.stderr.write(f"[Observability] Failed to initialize/log to GCP Cloud Logging: {e}\n")

def instrument_agents():
    # Setup the tracer provider first
    init_tracer()
    
    # Trace wrapper function
    def make_trace_wrapper(original_run, class_name):
        def wrapper(self, prompt, *args, **kwargs):
            agent_name = getattr(self.agent, "name", class_name)
            caller = getattr(_current_agent, "name", "orchestrator")
            
            # Log the incoming message (inter-agent message / prompt)
            log_audit_event(
                incident_context=self,
                sender_agent=caller,
                receiver_agent=agent_name,
                message=prompt,
                severity="INFO",
                context=getattr(self, "metadata", {})
            )
            
            # Setup thread-local for nested calls tracking
            old_agent = getattr(_current_agent, "name", None)
            _current_agent.name = agent_name
            
            if HAS_OTEL:
                from opentelemetry import trace
                tracer = trace.get_tracer("adk-sre-benjamin")
                
                with tracer.start_as_current_span(f"SRE Agent Run: {agent_name}") as span:
                    span.set_attribute("agent.class", class_name)
                    span.set_attribute("agent.name", agent_name)
                    span.set_attribute("agent.prompt", prompt)
                    
                    model = getattr(self.agent, "model", None)
                    if model:
                        span.set_attribute("agent.model", str(model))
                    
                    try:
                        result = original_run(self, prompt, *args, **kwargs)
                        span.set_attribute("agent.response_length", len(result) if result else 0)
                        
                        # Log response
                        log_audit_event(
                            incident_context=self,
                            sender_agent=agent_name,
                            receiver_agent=caller,
                            message=result,
                            severity="INFO",
                            context=getattr(self, "metadata", {})
                        )
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        from opentelemetry.trace.status import StatusCode, Status
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        
                        # Log error response
                        log_audit_event(
                            incident_context=self,
                            sender_agent=agent_name,
                            receiver_agent=caller,
                            message=f"Error: {e}",
                            severity="ERROR",
                            context=getattr(self, "metadata", {})
                        )
                        raise
                    finally:
                        _current_agent.name = old_agent
            else:
                try:
                    result = original_run(self, prompt, *args, **kwargs)
                    
                    # Log response
                    log_audit_event(
                        incident_context=self,
                        sender_agent=agent_name,
                        receiver_agent=caller,
                        message=result,
                        severity="INFO",
                        context=getattr(self, "metadata", {})
                    )
                    return result
                except Exception as e:
                    # Log error response
                    log_audit_event(
                        incident_context=self,
                        sender_agent=agent_name,
                        receiver_agent=caller,
                        message=f"Error: {e}",
                        severity="ERROR",
                        context=getattr(self, "metadata", {})
                    )
                    raise
                finally:
                    _current_agent.name = old_agent
        return wrapper

    # Apply monkeypatching to each of the SRE lead classes
    try:
        from src.agents.commander import IncidentCommander
        IncidentCommander.run = make_trace_wrapper(IncidentCommander.run, "IncidentCommander")
        print("[Observability] Instrumented IncidentCommander")
    except Exception as e:
        print(f"[Observability] Failed to instrument IncidentCommander: {e}")

    try:
        from src.agents.ops_lead import OperationsLead
        OperationsLead.run = make_trace_wrapper(OperationsLead.run, "OperationsLead")
        print("[Observability] Instrumented OperationsLead")
    except Exception as e:
        print(f"[Observability] Failed to instrument OperationsLead: {e}")

    try:
        from src.agents.planning_lead import PlanningLead
        PlanningLead.run = make_trace_wrapper(PlanningLead.run, "PlanningLead")
        print("[Observability] Instrumented PlanningLead")
    except Exception as e:
        print(f"[Observability] Failed to instrument PlanningLead: {e}")

    try:
        from src.agents.logistics_lead import LogisticsLead
        LogisticsLead.run = make_trace_wrapper(LogisticsLead.run, "LogisticsLead")
        print("[Observability] Instrumented LogisticsLead")
    except Exception as e:
        print(f"[Observability] Failed to instrument LogisticsLead: {e}")

    try:
        from src.agents.comms import CommunicationsLead
        CommunicationsLead.run = make_trace_wrapper(CommunicationsLead.run, "CommunicationsLead")
        print("[Observability] Instrumented CommunicationsLead")
    except Exception as e:
        print(f"[Observability] Failed to instrument CommunicationsLead: {e}")
