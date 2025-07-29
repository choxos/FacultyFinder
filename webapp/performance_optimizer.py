"""
Performance Optimization Module for FacultyFinder
Handles database optimization, caching, and performance monitoring
"""

import sqlite3
import os
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    def __init__(self, db_path, cache_instance=None):
        self.db_path = db_path
        self.cache = cache_instance
        self.optimization_applied = False
        
    def get_optimized_connection(self):
        """Get an optimized database connection"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # Apply SQLite performance optimizations
            optimizations = [
                "PRAGMA journal_mode=WAL",
                "PRAGMA synchronous=NORMAL",
                "PRAGMA cache_size=-64000",  # 64MB cache
                "PRAGMA temp_store=MEMORY",
                "PRAGMA mmap_size=268435456",  # 256MB mmap
                "PRAGMA page_size=4096"
            ]
            
            for pragma in optimizations:
                try:
                    conn.execute(pragma)
                except Exception as e:
                    logger.warning(f"Failed to apply {pragma}: {e}")
            
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create optimized connection: {e}")
            return None
    
    def create_performance_indexes(self):
        """Create database indexes for better query performance"""
        if self.optimization_applied:
            return
            
        try:
            conn = self.get_optimized_connection()
            if not conn:
                return
            
            # Check what columns actually exist before creating indexes
            cursor = conn.execute("PRAGMA table_info(professors)")
            professor_columns = [row[1] for row in cursor.fetchall()]
            
            cursor = conn.execute("PRAGMA table_info(universities)")
            university_columns = [row[1] for row in cursor.fetchall()]
            
            cursor = conn.execute("PRAGMA table_info(publications)")
            publication_columns = [row[1] for row in cursor.fetchall()]
            
            # Define indexes only for columns that exist
            indexes = []
            
            # University indexes
            if 'university_code' in university_columns:
                indexes.extend([
                    "CREATE INDEX IF NOT EXISTS idx_universities_code ON universities(university_code)",
                    "CREATE INDEX IF NOT EXISTS idx_universities_country ON universities(country)",
                    "CREATE INDEX IF NOT EXISTS idx_universities_name ON universities(name)"
                ])
            
            # Professor indexes
            if 'university_code' in professor_columns:
                indexes.append("CREATE INDEX IF NOT EXISTS idx_professors_university ON professors(university_code)")
            if 'name' in professor_columns:
                indexes.append("CREATE INDEX IF NOT EXISTS idx_professors_name ON professors(name)")
            if 'department' in professor_columns:
                indexes.append("CREATE INDEX IF NOT EXISTS idx_professors_department ON professors(department)")
            if 'position' in professor_columns:
                indexes.append("CREATE INDEX IF NOT EXISTS idx_professors_position ON professors(position)")
            if 'research_areas' in professor_columns:
                indexes.append("CREATE INDEX IF NOT EXISTS idx_professors_research ON professors(research_areas)")
            
            # Publication indexes (only if table exists and has data)
            if publication_columns:
                if 'professor_id' in publication_columns:
                    indexes.append("CREATE INDEX IF NOT EXISTS idx_publications_professor ON publications(professor_id)")
                if 'year' in publication_columns:
                    indexes.append("CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(year)")
                if 'title' in publication_columns:
                    indexes.append("CREATE INDEX IF NOT EXISTS idx_publications_title ON publications(title)")
            
            # Create indexes
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
            
            # Analyze tables for better query planning
            try:
                conn.execute("ANALYZE")
                logger.info("Database analysis completed")
            except Exception as e:
                logger.warning(f"Failed to analyze database: {e}")
            
            conn.close()
            self.optimization_applied = True
            logger.info("Performance indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating performance indexes: {e}")
    
    def optimize_database_settings(self):
        """Apply comprehensive database optimizations"""
        try:
            conn = self.get_optimized_connection()
            if not conn:
                return False
            
            # Advanced SQLite optimizations
            optimizations = [
                "PRAGMA journal_mode=WAL",
                "PRAGMA synchronous=NORMAL", 
                "PRAGMA cache_size=-128000",  # 128MB cache (increased)
                "PRAGMA temp_store=MEMORY",
                "PRAGMA mmap_size=536870912",  # 512MB mmap (increased)
                "PRAGMA page_size=4096",
                "PRAGMA wal_autocheckpoint=1000",  # Checkpoint every 1000 pages
                "PRAGMA busy_timeout=30000",  # 30 second timeout
                "PRAGMA optimize",  # Optimize query planner
            ]
            
            for pragma in optimizations:
                try:
                    conn.execute(pragma)
                except Exception as e:
                    logger.warning(f"Failed to apply {pragma}: {e}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error applying database optimizations: {e}")
            return False
    
    def analyze_query_performance(self, query, params=None):
        """Analyze query performance and suggest optimizations"""
        try:
            conn = self.get_optimized_connection()
            if not conn:
                return None
            
            # Use EXPLAIN QUERY PLAN to analyze query
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor = conn.execute(explain_query, params or [])
            plan = cursor.fetchall()
            
            conn.close()
            
            # Analyze for potential issues
            issues = []
            for row in plan:
                detail = str(row).lower()
                if 'scan' in detail and 'index' not in detail:
                    issues.append("Table scan detected - consider adding index")
                if 'temp b-tree' in detail:
                    issues.append("Temporary B-tree created - consider optimizing ORDER BY")
            
            return {
                'plan': [dict(row) for row in plan],
                'issues': issues,
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return None
    
    def optimize_cache_strategy(self):
        """Optimize caching strategy based on data access patterns"""
        if not self.cache:
            return False
            
        try:
            # Cache configuration for different data types
            cache_configs = {
                'university_filters': {'timeout': 3600, 'key_prefix': 'uni_filters'},
                'country_stats': {'timeout': 3600, 'key_prefix': 'country_stats'},
                'summary_stats': {'timeout': 600, 'key_prefix': 'summary'},
                'faculty_search': {'timeout': 1800, 'key_prefix': 'faculty'},
                'university_search': {'timeout': 1800, 'key_prefix': 'uni_search'},
                'professor_profile': {'timeout': 3600, 'key_prefix': 'prof_profile'}
            }
            
            # Store cache configuration for use by application
            for cache_type, config in cache_configs.items():
                cache_key = f"cache_config:{cache_type}"
                self.cache.set(cache_key, config, timeout=86400)  # 24 hours
            
            logger.info("Cache strategy optimization applied")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing cache strategy: {e}")
            return False

    def monitor_performance(self, func):
        """Decorator to monitor function performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log slow operations
                if duration > 1.0:
                    logger.warning(f"Slow operation: {func.__name__} took {duration:.3f}s")
                elif duration > 0.5:
                    logger.info(f"Operation: {func.__name__} took {duration:.3f}s")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {func.__name__} after {duration:.3f}s: {e}")
                raise
                
        return wrapper
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        if not self.cache:
            return False
            
        try:
            # Simple cleanup - let the cache handle its own cleanup
            initial_size = len(self.cache.cache) if hasattr(self.cache, 'cache') else 0
            
            # Force cleanup by checking each entry
            if hasattr(self.cache, 'cache') and hasattr(self.cache, 'timeouts'):
                current_time = time.time()
                expired_keys = []
                
                for key, timeout in self.cache.timeouts.items():
                    if current_time >= timeout:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    try:
                        del self.cache.cache[key]
                        del self.cache.timeouts[key]
                    except KeyError:
                        pass
                
                final_size = len(self.cache.cache)
                logger.info(f"Cache cleanup: {initial_size} -> {final_size} entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
            return False


def create_performance_optimizer(db_path, cache_instance=None):
    """Factory function to create performance optimizer"""
    return PerformanceOptimizer(db_path, cache_instance)


# Performance monitoring utilities
class QueryProfiler:
    def __init__(self):
        self.queries = []
        self.slow_threshold = 0.5  # 500ms
    
    def profile_query(self, query, duration, result_count=None):
        """Profile a database query"""
        self.queries.append({
            'query': query[:100] + '...' if len(query) > 100 else query,
            'duration': duration,
            'result_count': result_count,
            'timestamp': time.time(),
            'slow': duration > self.slow_threshold
        })
        
        # Keep only last 100 queries
        if len(self.queries) > 100:
            self.queries = self.queries[-100:]
    
    def get_slow_queries(self):
        """Get queries that exceeded the slow threshold"""
        return [q for q in self.queries if q['slow']]
    
    def get_performance_summary(self):
        """Get performance summary"""
        if not self.queries:
            return {}
        
        total_queries = len(self.queries)
        slow_queries = len(self.get_slow_queries())
        avg_duration = sum(q['duration'] for q in self.queries) / total_queries
        
        return {
            'total_queries': total_queries,
            'slow_queries': slow_queries,
            'slow_percentage': (slow_queries / total_queries) * 100,
            'average_duration': avg_duration,
            'max_duration': max(q['duration'] for q in self.queries),
            'min_duration': min(q['duration'] for q in self.queries)
        }

# Global profiler instance
query_profiler = QueryProfiler() 