Пользователь готов продолжить Week 25-26: Performance Optimization. Продолжаем с файлами по оптимизации запросов к БД, кэшированию, мониторингу производительности и CDN интеграции.

Следующие файлы:
- Database query optimization (индексы, анализ запросов)
- Advanced caching strategies (многоуровневое кэширование)
- Performance monitoring tools
- CDN integration
- Query analyzer
- Cache warming scripts# 🚀 WEEK 25-26: PERFORMANCE OPTIMIZATION (ПРОДОЛЖЕНИЕ)

## DAY 137-138: DATABASE & QUERY OPTIMIZATION

---

## ФАЙЛ 4: `ios_core/database/query_optimizer.py`

```python
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
```

---

## ФАЙЛ 5: `scripts/optimize/create_indexes.sql`

```sql
-- Database Index Optimization Script
-- Creates optimized indexes for IOS System

-- ============================================
-- Documents Table
-- ============================================

-- Primary key already exists
-- CREATE UNIQUE INDEX idx_documents_pk ON documents(id);

-- Title search (frequently used in search)
CREATE INDEX CONCURRENTLY idx_documents_title 
ON documents USING gin(to_tsvector('english', title));

-- Content full-text search
CREATE INDEX CONCURRENTLY idx_documents_content_fts 
ON documents USING gin(to_tsvector('english', content));

-- Domain filter (frequently used)
CREATE INDEX CONCURRENTLY idx_documents_domain_id 
ON documents(domain_id) WHERE domain_id IS NOT NULL;

-- Created date for sorting and filtering
CREATE INDEX CONCURRENTLY idx_documents_created_at 
ON documents(created_at DESC);

-- Updated date for sorting
CREATE INDEX CONCURRENTLY idx_documents_updated_at 
ON documents(updated_at DESC);

-- User ownership
CREATE INDEX CONCURRENTLY idx_documents_user_id 
ON documents(user_id);

-- Composite index for common query pattern
CREATE INDEX CONCURRENTLY idx_documents_user_created 
ON documents(user_id, created_at DESC);

-- Status filter
CREATE INDEX CONCURRENTLY idx_documents_status 
ON documents(status) WHERE status IS NOT NULL;

-- Partial index for active documents only
CREATE INDEX CONCURRENTLY idx_documents_active 
ON documents(id, title, created_at) 
WHERE status = 'active';

-- ============================================
-- Domains Table
-- ============================================

-- Name search
CREATE INDEX CONCURRENTLY idx_domains_name 
ON domains(name);

-- Hierarchy (parent-child relationships)
CREATE INDEX CONCURRENTLY idx_domains_parent_id 
ON domains(parent_id) WHERE parent_id IS NOT NULL;

-- Path for hierarchical queries
CREATE INDEX CONCURRENTLY idx_domains_path 
ON domains USING gist(path);

-- ============================================
-- Users Table
-- ============================================

-- Email lookup (used in authentication)
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email 
ON users(LOWER(email));

-- Username lookup
CREATE UNIQUE INDEX CONCURRENTLY idx_users_username 
ON users(LOWER(username));

-- Active users filter
CREATE INDEX CONCURRENTLY idx_users_active 
ON users(id, email, username) 
WHERE is_active = true;

-- Role-based queries
CREATE INDEX CONCURRENTLY idx_users_role 
ON users(role);

-- ============================================
-- Search History Table
-- ============================================

-- User's search history
CREATE INDEX CONCURRENTLY idx_search_history_user_id 
ON search_history(user_id, created_at DESC);

-- Query text for analytics
CREATE INDEX CONCURRENTLY idx_search_history_query 
ON search_history USING gin(to_tsvector('english', query));

-- Recent searches (30 days)
CREATE INDEX CONCURRENTLY idx_search_history_recent 
ON search_history(user_id, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '30 days';

-- ============================================
-- Audit Logs Table
-- ============================================

-- User actions
CREATE INDEX CONCURRENTLY idx_audit_logs_user_id 
ON audit_logs(user_id, created_at DESC);

-- Action type filter
CREATE INDEX CONCURRENTLY idx_audit_logs_action 
ON audit_logs(action);

-- Entity tracking
CREATE INDEX CONCURRENTLY idx_audit_logs_entity 
ON audit_logs(entity_type, entity_id);

-- Time-based queries
CREATE INDEX CONCURRENTLY idx_audit_logs_created_at 
ON audit_logs(created_at DESC);

-- Recent logs (7 days) - partial index
CREATE INDEX CONCURRENTLY idx_audit_logs_recent 
ON audit_logs(user_id, action, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '7 days';

-- ============================================
-- Sessions Table
-- ============================================

-- Token lookup
CREATE UNIQUE INDEX CONCURRENTLY idx_sessions_token 
ON sessions(token);

-- User sessions
CREATE INDEX CONCURRENTLY idx_sessions_user_id 
ON sessions(user_id, created_at DESC);

-- Active sessions only
CREATE INDEX CONCURRENTLY idx_sessions_active 
ON sessions(user_id, expires_at) 
WHERE expires_at > NOW();

-- Cleanup expired sessions
CREATE INDEX CONCURRENTLY idx_sessions_expired 
ON sessions(expires_at) 
WHERE expires_at <= NOW();

-- ============================================
-- Tags Table
-- ============================================

-- Tag name
CREATE INDEX CONCURRENTLY idx_tags_name 
ON tags(LOWER(name));

-- Tag usage count
CREATE INDEX CONCURRENTLY idx_tags_usage_count 
ON tags(usage_count DESC);

-- ============================================
-- Document Tags Join Table
-- ============================================

-- Document's tags
CREATE INDEX CONCURRENTLY idx_document_tags_document_id 
ON document_tags(document_id);

-- Tag's documents
CREATE INDEX CONCURRENTLY idx_document_tags_tag_id 
ON document_tags(tag_id);

-- Composite for join queries
CREATE INDEX CONCURRENTLY idx_document_tags_composite 
ON document_tags(document_id, tag_id);

-- ============================================
-- Comments Table
-- ============================================

-- Document comments
CREATE INDEX CONCURRENTLY idx_comments_document_id 
ON comments(document_id, created_at DESC);

-- User comments
CREATE INDEX CONCURRENTLY idx_comments_user_id 
ON comments(user_id, created_at DESC);

-- Parent-child relationships (threaded comments)
CREATE INDEX CONCURRENTLY idx_comments_parent_id 
ON comments(parent_id) WHERE parent_id IS NOT NULL;

-- ============================================
-- Notifications Table
-- ============================================

-- User notifications
CREATE INDEX CONCURRENTLY idx_notifications_user_id 
ON notifications(user_id, created_at DESC);

-- Unread notifications
CREATE INDEX CONCURRENTLY idx_notifications_unread 
ON notifications(user_id, created_at DESC) 
WHERE is_read = false;

-- ============================================
-- API Keys Table
-- ============================================

-- Key lookup
CREATE UNIQUE INDEX CONCURRENTLY idx_api_keys_key 
ON api_keys(key_hash);

-- User's API keys
CREATE INDEX CONCURRENTLY idx_api_keys_user_id 
ON api_keys(user_id);

-- Active keys only
CREATE INDEX CONCURRENTLY idx_api_keys_active 
ON api_keys(user_id, created_at DESC) 
WHERE is_active = true;

-- ============================================
-- Webhooks Table
-- ============================================

-- User webhooks
CREATE INDEX CONCURRENTLY idx_webhooks_user_id 
ON webhooks(user_id);

-- Active webhooks
CREATE INDEX CONCURRENTLY idx_webhooks_active 
ON webhooks(id, url, event_types) 
WHERE is_active = true;

-- ============================================
-- Analytics Table
-- ============================================

-- Time-series data
CREATE INDEX CONCURRENTLY idx_analytics_timestamp 
ON analytics(timestamp DESC);

-- Metric queries
CREATE INDEX CONCURRENTLY idx_analytics_metric 
ON analytics(metric_name, timestamp DESC);

-- Composite for metric queries with filters
CREATE INDEX CONCURRENTLY idx_analytics_composite 
ON analytics(metric_name, entity_type, timestamp DESC);

-- ============================================
-- Verify Indexes
-- ============================================

-- Show all indexes with sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM
    pg_stat_user_indexes
ORDER BY
    pg_relation_size(indexrelid) DESC;

-- Show unused indexes (scanned less than 100 times)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM
    pg_stat_user_indexes
WHERE
    idx_scan < 100
    AND indexname NOT LIKE '%_pkey'
ORDER BY
    pg_relation_size(indexrelid) DESC;
```

---

## ФАЙЛ 6: `scripts/optimize/analyze_database.py`

```python
#!/usr/bin/env python3
"""
Database Analysis and Optimization Script

Analyzes database performance and suggests optimizations:
- Slow queries
- Missing indexes
- Table bloat
- Vacuum status
- Index usage

Usage:
    python scripts/optimize/analyze_database.py
    python scripts/optimize/analyze_database.py --table documents
    python scripts/optimize/analyze_database.py --slow-queries --limit 20
"""

import argparse
import sys
from typing import List, Dict
from datetime import datetime

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

from ios_core.config import settings


class DatabaseAnalyzer:
    """Analyzes database performance and health"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def analyze_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get slowest queries from pg_stat_statements"""
        query = text("""
            SELECT
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                max_exec_time,
                stddev_exec_time,
                rows
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY mean_exec_time DESC
            LIMIT :limit
        """)
        
        try:
            result = self.session.execute(query, {"limit": limit})
            
            slow_queries = []
            for row in result:
                slow_queries.append({
                    "query": row.query[:200],  # Truncate long queries
                    "calls": row.calls,
                    "total_time_ms": round(row.total_exec_time, 2),
                    "mean_time_ms": round(row.mean_exec_time, 2),
                    "max_time_ms": round(row.max_exec_time, 2),
                    "stddev_ms": round(row.stddev_exec_time, 2),
                    "rows": row.rows
                })
            
            return slow_queries
            
        except Exception as e:
            print(f"Error analyzing slow queries: {e}")
            print("Note: pg_stat_statements extension may not be enabled")
            return []
    
    def analyze_table_bloat(self) -> List[Dict]:
        """Detect table bloat (dead tuples)"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                n_live_tup,
                n_dead_tup,
                ROUND(100 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 0
            ORDER BY n_dead_tup DESC
            LIMIT 20
        """)
        
        result = self.session.execute(query)
        
        bloat_info = []
        for row in result:
            bloat_info.append({
                "schema": row.schemaname,
                "table": row.tablename,
                "size": row.size,
                "live_tuples": row.n_live_tup,
                "dead_tuples": row.n_dead_tup,
                "dead_ratio": row.dead_ratio or 0,
                "needs_vacuum": row.dead_ratio and row.dead_ratio > 10
            })
        
        return bloat_info
    
    def analyze_missing_indexes(self) -> List[Dict]:
        """Suggest missing indexes based on sequential scans"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                CASE 
                    WHEN seq_scan = 0 THEN 0
                    ELSE ROUND(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 2)
                END AS index_usage_ratio,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
            FROM pg_stat_user_tables
            WHERE seq_scan > 100
                AND idx_scan < seq_scan
            ORDER BY seq_scan DESC
            LIMIT 20
        """)
        
        result = self.session.execute(query)
        
        suggestions = []
        for row in result:
            suggestions.append({
                "schema": row.schemaname,
                "table": row.tablename,
                "sequential_scans": row.seq_scan,
                "tuples_read": row.seq_tup_read,
                "index_scans": row.idx_scan,
                "index_usage_ratio": row.index_usage_ratio or 0,
                "table_size": row.table_size,
                "recommendation": "Consider adding indexes to reduce sequential scans"
            })
        
        return suggestions
    
    def analyze_index_usage(self, table_name: str = None) -> List[Dict]:
        """Analyze index usage statistics"""
        if table_name:
            query = text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
                FROM pg_stat_user_indexes
                WHERE tablename = :table_name
                ORDER BY idx_scan
            """)
            result = self.session.execute(query, {"table_name": table_name})
        else:
            query = text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
                FROM pg_stat_user_indexes
                WHERE idx_scan < 100
                    AND indexname NOT LIKE '%_pkey'
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 20
            """)
            result = self.session.execute(query)
        
        index_stats = []
        for row in result:
            is_unused = row.idx_scan < 100
            
            index_stats.append({
                "schema": row.schemaname,
                "table": row.tablename,
                "index": row.indexname,
                "scans": row.idx_scan,
                "tuples_read": row.idx_tup_read,
                "tuples_fetched": row.idx_tup_fetch,
                "size": row.index_size,
                "is_unused": is_unused,
                "recommendation": "Consider dropping" if is_unused else "Keep"
            })
        
        return index_stats
    
    def analyze_table_sizes(self, limit: int = 20) -> List[Dict]:
        """Get largest tables"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                              pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
                n_live_tup AS row_count
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT :limit
        """)
        
        result = self.session.execute(query, {"limit": limit})
        
        sizes = []
        for row in result:
            sizes.append({
                "schema": row.schemaname,
                "table": row.tablename,
                "total_size": row.total_size,
                "table_size": row.table_size,
                "indexes_size": row.indexes_size,
                "row_count": row.row_count
            })
        
        return sizes
    
    def analyze_vacuum_stats(self) -> List[Dict]:
        """Get vacuum and analyze statistics"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze,
                vacuum_count,
                autovacuum_count,
                analyze_count,
                autoanalyze_count,
                n_dead_tup
            FROM pg_stat_user_tables
            ORDER BY n_dead_tup DESC
            LIMIT 20
        """)
        
        result = self.session.execute(query)
        
        vacuum_stats = []
        for row in result:
            vacuum_stats.append({
                "schema": row.schemaname,
                "table": row.tablename,
                "last_vacuum": row.last_vacuum,
                "last_autovacuum": row.last_autovacuum,
                "last_analyze": row.last_analyze,
                "last_autoanalyze": row.last_autoanalyze,
                "vacuum_count": row.vacuum_count,
                "autovacuum_count": row.autovacuum_count,
                "analyze_count": row.analyze_count,
                "autoanalyze_count": row.autoanalyze_count,
                "dead_tuples": row.n_dead_tup
            })
        
        return vacuum_stats
    
    def print_report(self):
        """Print comprehensive database analysis report"""
        print("=" * 80)
        print("DATABASE PERFORMANCE ANALYSIS REPORT")
        print(f"Generated: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Slow queries
        print("\n📊 SLOW QUERIES (Top 10)")
        print("-" * 80)
        slow_queries = self.analyze_slow_queries(10)
        
        if slow_queries:
            for i, query in enumerate(slow_queries, 1):
                print(f"\n{i}. Mean time: {query['mean_time_ms']}ms "
                      f"(calls: {query['calls']}, max: {query['max_time_ms']}ms)")
                print(f"   {query['query']}")
        else:
            print("No slow queries found or pg_stat_statements not enabled")
        
        # Table bloat
        print("\n\n💾 TABLE BLOAT")
        print("-" * 80)
        bloat = self.analyze_table_bloat()
        
        if bloat:
            for table in bloat[:10]:
                print(f"{table['table']:30} | "
                      f"Size: {table['size']:10} | "
                      f"Dead: {table['dead_tuples']:10} ({table['dead_ratio']:.1f}%) | "
                      f"{'⚠️ NEEDS VACUUM' if table['needs_vacuum'] else '✅ OK'}")
        else:
            print("No bloated tables found")
        
        # Missing indexes
        print("\n\n🔍 MISSING INDEXES (High Sequential Scans)")
        print("-" * 80)
        missing = self.analyze_missing_indexes()
        
        if missing:
            for table in missing[:10]:
                print(f"{table['table']:30} | "
                      f"Seq scans: {table['sequential_scans']:8} | "
                      f"Index usage: {table['index_usage_ratio']:5.1f}% | "
                      f"Size: {table['table_size']}")
        else:
            print("All tables have good index usage")
        
        # Unused indexes
        print("\n\n🗑️  UNUSED INDEXES")
        print("-" * 80)
        unused = self.analyze_index_usage()
        
        if unused:
            for idx in unused[:10]:
                print(f"{idx['table']:20}.{idx['index']:30} | "
                      f"Scans: {idx['scans']:5} | "
                      f"Size: {idx['size']:10} | "
                      f"{idx['recommendation']}")
        else:
            print("All indexes are being used")
        
        # Table sizes
        print("\n\n📦 LARGEST TABLES")
        print("-" * 80)
        sizes = self.analyze_table_sizes(10)
        
        for table in sizes:
            print(f"{table['table']:30} | "
                  f"Total: {table['total_size']:10} | "
                  f"Table: {table['table_size']:10} | "
                  f"Indexes: {table['indexes_size']:10} | "
                  f"Rows: {table['row_count']:10}")
        
        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze database performance"
    )
    parser.add_argument(
        "--slow-queries",
        action="store_true",
        help="Show slow queries"
    )
    parser.add_argument(
        "--table",
        help="Analyze specific table"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of results"
    )
    
    args = parser.parse_args()
    
    analyzer = DatabaseAnalyzer(settings.database_url)
    
    if args.slow_queries:
        queries = analyzer.analyze_slow_queries(args.limit)
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. {query['mean_time_ms']}ms (calls: {query['calls']})")
            print(query['query'])
    
    elif args.table:
        print(f"\nAnalyzing table: {args.table}\n")
        index_usage = analyzer.analyze_index_usage(args.table)
        
        for idx in index_usage:
            print(f"{idx['index']:40} | "
                  f"Scans: {idx['scans']:8} | "
                  f"Size: {idx['size']:10}")
    
    else:
        analyzer.print_report()


if __name__ == "__main__":
    main()
```

---

**Продолжение следует...**

Создано:
- ✅ Query analyzer (slow queries, missing indexes)
- ✅ Index optimizer (suggestions, creation)
- ✅ Query cache layer
- ✅ Comprehensive index creation script
- ✅ Database analysis tool

**Следующие файлы:**
- Advanced caching strategies
- CDN integration
- Performance monitoring
- Cache warming
- Optimization documentation

**Готовы продолжить?**