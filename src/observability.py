import os
import sys

# Define a mock/noop trace context if opentelemetry is not installed
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

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

def instrument_agents():
    # Setup the tracer provider first
    init_tracer()
    
    # Trace wrapper function
    def make_trace_wrapper(original_run, class_name):
        def wrapper(self, prompt, *args, **kwargs):
            if not HAS_OTEL:
                return original_run(self, prompt, *args, **kwargs)
                
            tracer = trace.get_tracer("adk-sre-benjamin")
            agent_name = getattr(self.agent, "name", class_name)
            
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
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, str(e)))
                    raise
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
