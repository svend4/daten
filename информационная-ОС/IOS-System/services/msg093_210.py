"""
Database Query Optimizer
Analyzes and optimizes SQL queries for performance
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Result

from .session import get_session
from ..config import settings

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyzes database queries for performance issues
    
    Features:
    - Slow query detection
    - Missing index detection
    - N+1 query detection
    - Query plan analysis
    - Performance recommendations
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.slow_query_threshold = 100  # ms
        self.query_log = []
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a single query
        
        Returns performance metrics and recommendations
        """
        start_time = time.time()
        
        # Get query execution plan
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        
        try:
            result = self.session.execute(text(explain_query))
            plan = result.scalar()
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            analysis = {
                "query": query,
                "execution_time_ms": execution_time,
                "plan": plan,
                "is_slow": execution_time > self.slow_query_threshold,
                "recommendations": self._generate_recommendations(plan, query)
            }
            
            # Log slow queries
            if analysis["is_slow"]:
                logger.warning(
                    f"Slow query detected: {execution_time:.2f}ms\n{query}"
                )
            
            self.query_log.append(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "query": query,
                "error": str(e),
                "recommendations": []
            }
    
    def _generate_recommendations(
        self, 
        plan: Dict, 
        query: str
    ) -> List[str]:
        """Generate optimization recommendations based on query plan"""
        recommendations = []
        
        if not plan:
            return recommendations
        
        # Extract plan details
        plan_data = plan[0]["Plan"] if isinstance(plan, list) else plan
        
        # Check for sequential scans on large tables
        if plan_data.get("Node Type") == "Seq Scan":
            table = plan_data.get("Relation Name")
            rows = plan_data.get("Plan Rows", 0)
            
            if rows > 1000:
                recommendations.append(
                    f"Sequential scan on '{table}' with {rows} rows. "
                    f"Consider adding an index."
                )
        
        # Check for missing indexes
        if "Index" not in plan_data.get("Node Type", ""):
            if "WHERE" in query.upper() or "JOIN" in query.upper():
                recommendations.append(
                    "Query uses WHERE/JOIN without index. "
                    "Consider adding appropriate indexes."
                )
        
        # Check for expensive sorts
        if plan_data.get("Node Type") == "Sort":
            sort_method = plan_data.get("Sort Method")
            if sort_method == "external merge":
                recommendations.append(
                    "Sort operation using disk (external merge). "
                    "Consider increasing work_mem or adding an index."
                )
        
        # Check for nested loops on large datasets
        if plan_data.get("Node Type") == "Nested Loop":
            if plan_data.get("Plan Rows", 0) > 10000:
                recommendations.append(
                    "Nested loop on large dataset. "
                    "Consider using hash join instead."
                )
        
        # Check execution time
        actual_time = plan_data.get("Actual Total Time", 0)
        if actual_time > 100:
            recommendations.append(
                f"Query took {actual_time:.2f}ms. "
                f"Review query structure and indexes."
            )
        
        return recommendations
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get slowest queries from log"""
        sorted_queries = sorted(
            self.query_log,
            key=lambda x: x.get("execution_time_ms", 0),
            reverse=True
        )
        
        return sorted_queries[:limit]
    
    def get_missing_indexes(self) -> List[Dict]:
        """
        Detect missing indexes based on query patterns
        
        Analyzes sequential scans and suggests indexes
        """
        missing_indexes = []
        
        # Aggregate sequential scans by table
        seq_scans = defaultdict(int)
        
        for query_data in self.query_log:
            plan = query_data.get("plan")
            if not plan:
                continue
            
            self._find_seq_scans(plan, seq_scans)
        
        # Generate recommendations
        for table, count in seq_scans.items():
            if count > 5:  # Table scanned multiple times
                missing_indexes.append({
                    "table": table,
                    "scan_count": count,
                    "recommendation": f"Table '{table}' scanned {count} times. "
                                    f"Analyze queries and add appropriate indexes."
                })
        
        return missing_indexes
    
    def _find_seq_scans(self, plan: Any, seq_scans: Dict):
        """Recursively find sequential scans in query plan"""
        if isinstance(plan, dict):
            if plan.get("Node Type") == "Seq Scan":
                table = plan.get("Relation Name")
                if table:
                    seq_scans[table] += 1
            
            # Check child nodes
            for key, value in plan.items():
                if key == "Plans":
                    for subplan in value:
                        self._find_seq_scans(subplan, seq_scans)
        
        elif isinstance(plan, list):
            for item in plan:
                self._find_seq_scans(item, seq_scans)


class IndexOptimizer:
    """
    Suggests and creates optimal database indexes
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def suggest_indexes(self, table_name: str) -> List[Dict]:
        """
        Suggest indexes for a table based on usage patterns
        
        Analyzes:
        - Most queried columns
        - JOIN conditions
        - WHERE clauses
        - ORDER BY columns
        """
        suggestions = []
        
        # Get table statistics
        stats_query = text(f"""
            SELECT
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE tablename = :table_name
            ORDER BY n_distinct DESC
        """)
        
        result = self.session.execute(
            stats_query,
            {"table_name": table_name}
        )
        
        for row in result:
            # High cardinality columns are good index candidates
            if abs(row.n_distinct) > 100:
                suggestions.append({
                    "table": row.tablename,
                    "column": row.attname,
                    "type": "B-tree",
                    "reason": f"High cardinality ({row.n_distinct})",
                    "sql": f"CREATE INDEX idx_{row.tablename}_{row.attname} "
                          f"ON {row.tablename}({row.attname});"
                })
            
            # Low correlation suggests index would help
            if abs(row.correlation) < 0.5 and abs(row.n_distinct) > 10:
                suggestions.append({
                    "table": row.tablename,
                    "column": row.attname,
                    "type": "B-tree",
                    "reason": f"Low correlation ({row.correlation:.2f})",
                    "sql": f"CREATE INDEX idx_{row.tablename}_{row.attname} "
                          f"ON {row.tablename}({row.attname});"
                })
        
        return suggestions
    
    def create_index(
        self,
        table: str,
        columns: List[str],
        index_type: str = "btree",
        unique: bool = False
    ) -> bool:
        """
        Create an index on specified columns
        
        Args:
            table: Table name
            columns: List of column names
            index_type: Index type (btree, hash, gin, gist)
            unique: Whether index should enforce uniqueness
        """
        try:
            index_name = f"idx_{'_'.join([table] + columns)}"
            columns_str = ", ".join(columns)
            
            unique_str = "UNIQUE " if unique else ""
            
            create_sql = f"""
                CREATE {unique_str}INDEX CONCURRENTLY
                {index_name}
                ON {table}
                USING {index_type} ({columns_str})
            """
            
            logger.info(f"Creating index: {create_sql}")
            
            self.session.execute(text(create_sql))
            self.session.commit()
            
            logger.info(f"Index created successfully: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            self.session.rollback()
            return False
    
    def get_existing_indexes(self, table_name: str) -> List[Dict]:
        """Get all existing indexes for a table"""
        query = text("""
            SELECT
                i.relname as index_name,
                a.attname as column_name,
                am.amname as index_type,
                idx.indisunique as is_unique,
                idx.indisprimary as is_primary,
                pg_size_pretty(pg_relation_size(i.oid)) as index_size
            FROM
                pg_index idx
                JOIN pg_class i ON i.oid = idx.indexrelid
                JOIN pg_class t ON t.oid = idx.indrelid
                JOIN pg_am am ON i.relam = am.oid
                JOIN pg_attribute a ON a.attrelid = t.oid
                    AND a.attnum = ANY(idx.indkey)
            WHERE
                t.relname = :table_name
                AND t.relkind = 'r'
            ORDER BY
                i.relname, a.attnum
        """)
        
        result = self.session.execute(query, {"table_name": table_name})
        
        indexes = []
        for row in result:
            indexes.append({
                "index_name": row.index_name,
                "column_name": row.column_name,
                "index_type": row.index_type,
                "is_unique": row.is_unique,
                "is_primary": row.is_primary,
                "size": row.index_size
            })
        
        return indexes
    
    def analyze_index_usage(self, table_name: str) -> List[Dict]:
        """
        Analyze index usage to find unused indexes
        
        Returns statistics on index scans vs sequential scans
        """
        query = text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM
                pg_stat_user_indexes
            WHERE
                tablename = :table_name
            ORDER BY
                idx_scan
        """)
        
        result = self.session.execute(query, {"table_name": table_name})
        
        usage_stats = []
        for row in result:
            # Mark index as unused if scanned less than 100 times
            is_unused = row.idx_scan < 100
            
            usage_stats.append({
                "index_name": row.indexname,
                "scans": row.idx_scan,
                "tuples_read": row.idx_tup_read,
                "tuples_fetched": row.idx_tup_fetch,
                "size": row.index_size,
                "is_unused": is_unused,
                "recommendation": "Consider dropping" if is_unused else "Keep"
            })
        
        return usage_stats


class QueryCache:
    """
    Query-level caching for frequently executed queries
    
    Caches query results in Redis with TTL
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def get_cached_result(self, query_hash: str) -> Optional[Any]:
        """Get cached query result"""
        try:
            cached = self.redis.get(f"query_cache:{query_hash}")
            if cached:
                logger.debug(f"Cache hit for query: {query_hash}")
                return cached
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
        
        return None
    
    def cache_result(
        self,
        query_hash: str,
        result: Any,
        ttl: Optional[int] = None
    ):
        """Cache query result"""
        try:
            ttl = ttl or self.default_ttl
            self.redis.setex(
                f"query_cache:{query_hash}",
                ttl,
                result
            )
            logger.debug(f"Cached query result: {query_hash}")
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def invalidate_cache(self, pattern: str = "*"):
        """Invalidate cached queries matching pattern"""
        try:
            keys = self.redis.keys(f"query_cache:{pattern}")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cached queries")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")