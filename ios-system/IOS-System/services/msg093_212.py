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