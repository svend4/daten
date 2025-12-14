"""
Intelligent Request Router
Dynamic routing with load balancing
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import random
from enum import Enum

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Routing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    STICKY_SESSION = "sticky_session"


class Backend:
    """Backend server"""
    
    def __init__(
        self,
        name: str,
        url: str,
        weight: int = 1,
        health_check_url: Optional[str] = None
    ):
        self.name = name
        self.url = url
        self.weight = weight
        self.health_check_url = health_check_url or f"{url}/health"
        
        # State
        self.is_healthy = True
        self.active_connections = 0
        self.total_requests = 0
        self.total_errors = 0
        self.last_health_check = None
        self.response_times = []
    
    def record_request(self, success: bool, response_time: float):
        """Record request metrics"""
        
        self.total_requests += 1
        if not success:
            self.total_errors += 1
        
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
    
    def get_avg_response_time(self) -> float:
        """Get average response time"""
        
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_error_rate(self) -> float:
        """Get error rate percentage"""
        
        if self.total_requests == 0:
            return 0.0
        return (self.total_errors / self.total_requests) * 100


class RequestRouter:
    """
    Intelligent request router with load balancing
    
    Features:
    - Multiple routing strategies
    - Health checks
    - Automatic failover
    - Connection tracking
    - Weighted distribution
    - Sticky sessions
    
    Usage:
        router = RequestRouter()
        
        # Add backends
        router.add_backend("server1", "http://localhost:8001", weight=2)
        router.add_backend("server2", "http://localhost:8002", weight=1)
        
        # Route request
        backend = router.route(
            session_id="user123",
            strategy=RoutingStrategy.WEIGHTED
        )
    """
    
    def __init__(self):
        self.backends: Dict[str, Backend] = {}
        self.round_robin_index = 0
        self.sticky_sessions: Dict[str, str] = {}  # session_id -> backend_name
    
    def add_backend(
        self,
        name: str,
        url: str,
        weight: int = 1,
        health_check_url: Optional[str] = None
    ):
        """Add backend server"""
        
        backend = Backend(
            name=name,
            url=url,
            weight=weight,
            health_check_url=health_check_url
        )
        
        self.backends[name] = backend
        logger.info(f"Added backend: {name} ({url}) weight={weight}")
    
    def remove_backend(self, name: str):
        """Remove backend server"""
        
        if name in self.backends:
            del self.backends[name]
            logger.info(f"Removed backend: {name}")
    
    def route(
        self,
        strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
        session_id: Optional[str] = None,
        exclude: Optional[List[str]] = None
    ) -> Optional[Backend]:
        """
        Route request to backend
        
        Args:
            strategy: Routing strategy
            session_id: Session ID for sticky sessions
            exclude: Backends to exclude
        
        Returns:
            Selected backend or None if all unhealthy
        """
        
        # Get healthy backends
        healthy_backends = [
            b for b in self.backends.values()
            if b.is_healthy and (not exclude or b.name not in exclude)
        ]
        
        if not healthy_backends:
            logger.error("No healthy backends available")
            return None
        
        # Route based on strategy
        if strategy == RoutingStrategy.STICKY_SESSION and session_id:
            return self._route_sticky_session(session_id, healthy_backends)
        
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            return self._route_round_robin(healthy_backends)
        
        elif strategy == RoutingStrategy.WEIGHTED:
            return self._route_weighted(healthy_backends)
        
        elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self._route_least_connections(healthy_backends)
        
        elif strategy == RoutingStrategy.RANDOM:
            return random.choice(healthy_backends)
        
        else:
            logger.warning(f"Unknown strategy: {strategy}, using random")
            return random.choice(healthy_backends)
    
    def _route_sticky_session(
        self,
        session_id: str,
        healthy_backends: List[Backend]
    ) -> Backend:
        """Route with sticky sessions"""
        
        # Check if session already mapped
        if session_id in self.sticky_sessions:
            backend_name = self.sticky_sessions[session_id]
            
            # Check if backend still healthy
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                if backend.is_healthy:
                    return backend
        
        # No existing mapping or backend unhealthy, assign new
        backend = self._route_weighted(healthy_backends)
        self.sticky_sessions[session_id] = backend.name
        
        return backend
    
    def _route_round_robin(self, healthy_backends: List[Backend]) -> Backend:
        """Round-robin routing"""
        
        backend = healthy_backends[self.round_robin_index % len(healthy_backends)]
        self.round_robin_index += 1
        
        return backend
    
    def _route_weighted(self, healthy_backends: List[Backend]) -> Backend:
        """Weighted random routing"""
        
        total_weight = sum(b.weight for b in healthy_backends)
        
        if total_weight == 0:
            return random.choice(healthy_backends)
        
        # Random selection based on weights
        rand = random.uniform(0, total_weight)
        current = 0
        
        for backend in healthy_backends:
            current += backend.weight
            if rand <= current:
                return backend
        
        return healthy_backends[-1]
    
    def _route_least_connections(self, healthy_backends: List[Backend]) -> Backend:
        """Route to backend with least active connections"""
        
        return min(healthy_backends, key=lambda b: b.active_connections)
    
    async def health_check(self, backend_name: str) -> bool:
        """
        Perform health check on backend
        
        Args:
            backend_name: Backend name
        
        Returns:
            True if healthy
        """
        
        if backend_name not in self.backends:
            return False
        
        backend = self.backends[backend_name]
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    backend.health_check_url,
                    timeout=5.0
                )
                
                is_healthy = response.status_code == 200
                backend.is_healthy = is_healthy
                backend.last_health_check = datetime.utcnow()
                
                if is_healthy:
                    logger.debug(f"Backend {backend_name} is healthy")
                else:
                    logger.warning(
                        f"Backend {backend_name} unhealthy: "
                        f"status={response.status_code}"
                    )
                
                return is_healthy
                
        except Exception as e:
            logger.error(f"Health check failed for {backend_name}: {e}")
            backend.is_healthy = False
            backend.last_health_check = datetime.utcnow()
            return False
    
    async def health_check_all(self):
        """Run health checks on all backends"""
        
        import asyncio
        
        tasks = [
            self.health_check(name)
            for name in self.backends.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = sum(1 for r in results if r is True)
        
        logger.info(
            f"Health check complete: {healthy_count}/{len(self.backends)} healthy"
        )
    
    def get_backend_stats(self) -> Dict:
        """Get statistics for all backends"""
        
        return {
            name: {
                "url": backend.url,
                "weight": backend.weight,
                "is_healthy": backend.is_healthy,
                "active_connections": backend.active_connections,
                "total_requests": backend.total_requests,
                "total_errors": backend.total_errors,
                "error_rate": round(backend.get_error_rate(), 2),
                "avg_response_time": round(backend.get_avg_response_time(), 2),
                "last_health_check": backend.last_health_check.isoformat()
                    if backend.last_health_check else None
            }
            for name, backend in self.backends.items()
        }


# Global request router
request_router = RequestRouter()