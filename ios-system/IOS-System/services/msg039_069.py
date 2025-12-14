# ios_core/observability/tracing.py

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing():
    """Setup distributed tracing"""
    
    provider = TracerProvider()
    
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    trace.set_tracer_provider(provider)

# Использование
@trace.get_tracer(__name__).start_as_current_span("process_document")
async def process_document(self, file_path: str):
    with tracer.start_as_current_span("classify"):
        classification = await self.classifier.classify(document)
    
    with tracer.start_as_current_span("extract_entities"):
        entities = await self.graph.extract_entities(document)
    
    return result