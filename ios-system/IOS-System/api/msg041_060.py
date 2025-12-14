"""
Metrics endpoint for Prometheus
"""

from fastapi import APIRouter, Response

from ios_core.observability import metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus exposition format
    """
    return Response(
        content=metrics.get_metrics(),
        media_type="text/plain"
    )