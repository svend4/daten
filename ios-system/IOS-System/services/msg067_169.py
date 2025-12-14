"""
API Analytics and Monitoring
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

from ..database import async_session
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


class APIAnalytics:
    """
    API usage analytics
    
    Features:
    - Request tracking
    - Response time metrics
    - Error rate monitoring
    - Endpoint popularity
    - User behavior analysis
    - Rate limit monitoring
    
    Usage:
        analytics = APIAnalytics()
        
        # Track request
        await analytics.track_request(
            endpoint="/api/search",
            method="POST",
            user_id="user123",
            response_time=0.15,
            status_code=200
        )
    """
    
    def __init__(self):
        self.memory_stats = {
            "requests_by_endpoint": defaultdict(int),
            "requests_by_user": defaultdict(int),
            "response_times": defaultdict(list),
            "status_codes": defaultdict(int),
            "errors": [],
        }
        self.retention_days = 30
    
    async def track_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        response_time: float = 0.0,
        status_code: int = 200,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Track API request
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            user_id: User ID
            response_time: Response time in seconds
            status_code: HTTP status code
            error: Error message if any
            metadata: Additional metadata
        """
        
        # Update memory stats
        self.memory_stats["requests_by_endpoint"][endpoint] += 1
        
        if user_id:
            self.memory_stats["requests_by_user"][user_id] += 1
        
        self.memory_stats["response_times"][endpoint].append(response_time)
        self.memory_stats["status_codes"][status_code] += 1
        
        if error:
            self.memory_stats["errors"].append({
                "endpoint": endpoint,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only recent errors
            if len(self.memory_stats["errors"]) > 1000:
                self.memory_stats["errors"] = self.memory_stats["errors"][-1000:]
        
        # Trim response times lists
        for ep in self.memory_stats["response_times"]:
            times = self.memory_stats["response_times"][ep]
            if len(times) > 1000:
                self.memory_stats["response_times"][ep] = times[-1000:]
    
    def get_endpoint_stats(
        self,
        endpoint: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """
        Get endpoint statistics
        
        Args:
            endpoint: Specific endpoint (None for all)
            limit: Max endpoints to return
        
        Returns:
            Endpoint statistics
        """
        
        if endpoint:
            # Specific endpoint
            times = self.memory_stats["response_times"].get(endpoint, [])
            count = self.memory_stats["requests_by_endpoint"].get(endpoint, 0)
            
            return {
                "endpoint": endpoint,
                "total_requests": count,
                "avg_response_time": round(sum(times) / len(times), 3) if times else 0,
                "min_response_time": round(min(times), 3) if times else 0,
                "max_response_time": round(max(times), 3) if times else 0,
                "p95_response_time": round(
                    self._percentile(times, 95), 3
                ) if times else 0,
                "p99_response_time": round(
                    self._percentile(times, 99), 3
                ) if times else 0
            }
        
        else:
            # Top endpoints
            top_endpoints = sorted(
                self.memory_stats["requests_by_endpoint"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "endpoints": [
                    {
                        "endpoint": ep,
                        "requests": count,
                        "avg_response_time": round(
                            sum(self.memory_stats["response_times"].get(ep, [])) /
                            len(self.memory_stats["response_times"].get(ep, [1])),
                            3
                        )
                    }
                    for ep, count in top_endpoints
                ]
            }
    
    def get_user_stats(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """Get user statistics"""
        
        if user_id:
            # Specific user
            return {
                "user_id": user_id,
                "total_requests": self.memory_stats["requests_by_user"].get(
                    user_id, 0
                )
            }
        
        else:
            # Top users
            top_users = sorted(
                self.memory_stats["requests_by_user"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "users": [
                    {"user_id": uid, "requests": count}
                    for uid, count in top_users
                ]
            }
    
    def get_error_stats(self, limit: int = 100) -> Dict:
        """Get error statistics"""
        
        recent_errors = self.memory_stats["errors"][-limit:]
        
        # Group by endpoint
        errors_by_endpoint = defaultdict(int)
        for error in recent_errors:
            errors_by_endpoint[error["endpoint"]] += 1
        
        return {
            "total_errors": len(self.memory_stats["errors"]),
            "recent_errors": recent_errors,
            "by_endpoint": dict(errors_by_endpoint)
        }
    
    def get_status_code_stats(self) -> Dict:
        """Get HTTP status code distribution"""
        
        total = sum(self.memory_stats["status_codes"].values())
        
        return {
            "distribution": dict(self.memory_stats["status_codes"]),
            "total_requests": total,
            "success_rate": round(
                sum(
                    count for code, count in self.memory_stats["status_codes"].items()
                    if 200 <= code < 300
                ) / total * 100, 2
            ) if total > 0 else 0
        }
    
    def get_summary(self) -> Dict:
        """Get overall summary"""
        
        total_requests = sum(self.memory_stats["requests_by_endpoint"].values())
        
        # Calculate overall avg response time
        all_times = []
        for times in self.memory_stats["response_times"].values():
            all_times.extend(times)
        
        avg_response_time = sum(all_times) / len(all_times) if all_times else 0
        
        return {
            "total_requests": total_requests,
            "unique_endpoints": len(self.memory_stats["requests_by_endpoint"]),
            "unique_users": len(self.memory_stats["requests_by_user"]),
            "avg_response_time": round(avg_response_time, 3),
            "total_errors": len(self.memory_stats["errors"]),
            "status_codes": dict(self.memory_stats["status_codes"])
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset all statistics"""
        
        self.memory_stats = {
            "requests_by_endpoint": defaultdict(int),
            "requests_by_user": defaultdict(int),
            "response_times": defaultdict(list),
            "status_codes": defaultdict(int),
            "errors": [],
        }
        
        logger.info("API analytics reset")


# Global API analytics
api_analytics = APIAnalytics()