#!/usr/bin/env python3
"""
Automated Database Performance Testing.

Runs EXPLAIN ANALYZE on key queries and validates index usage.

Usage:
    python scripts/performance_test/database_performance.py \
        --output database_performance.json
"""
import argparse
import sys
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_dir)

load_dotenv(os.path.join(backend_dir, '.env'))


def explain_analyze(db_session, query: str, query_name: str) -> dict:
    """Run EXPLAIN ANALYZE on a query."""
    try:
        result = db_session.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"))
        row = result.fetchone()
        
        if row and row[0]:
            plan = row[0][0] if isinstance(row[0], list) else row[0]
            return {
                'query_name': query_name,
                'query': query,
                'execution_time_ms': plan.get('Execution Time', 0),
                'planning_time_ms': plan.get('Planning Time', 0),
                'total_time_ms': plan.get('Execution Time', 0) + plan.get('Planning Time', 0),
                'plan': plan.get('Plan', {}),
                'indexes_used': extract_indexes(plan.get('Plan', {})),
                'success': True,
            }
        else:
            return {
                'query_name': query_name,
                'query': query,
                'success': False,
                'error': 'No plan returned',
            }
    except Exception as e:
        return {
            'query_name': query_name,
            'query': query,
            'success': False,
            'error': str(e),
        }


def extract_indexes(plan: dict, indexes: list = None) -> list:
    """Recursively extract index usage from query plan."""
    if indexes is None:
        indexes = []
    
    # Check if this node uses an index
    if 'Index Scan' in plan.get('Node Type', '') or 'Index Only Scan' in plan.get('Node Type', ''):
        index_name = plan.get('Index Name')
        if index_name:
            indexes.append(index_name)
    
    # Check for bitmap index scans
    if 'Bitmap Index Scan' in plan.get('Node Type', ''):
        index_name = plan.get('Index Name')
        if index_name:
            indexes.append(index_name)
    
    # Recursively check child plans
    if 'Plans' in plan:
        for child_plan in plan['Plans']:
            extract_indexes(child_plan, indexes)
    
    return list(set(indexes))  # Remove duplicates


def check_sequential_scans(plan: dict) -> bool:
    """Check if query uses sequential scans."""
    node_type = plan.get('Node Type', '')
    if 'Seq Scan' in node_type:
        return True
    
    if 'Plans' in plan:
        for child_plan in plan['Plans']:
            if check_sequential_scans(child_plan):
                return True
    
    return False


def get_indexes(db_session) -> list:
    """Get all indexes from database."""
    query = text("""
        SELECT 
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)
    
    result = db_session.execute(query)
    indexes = []
    for row in result:
        indexes.append({
            'table': row.tablename,
            'name': row.indexname,
            'definition': row.indexdef,
        })
    
    return indexes


def test_key_queries(db_session) -> list:
    """Test key queries used by the application."""
    results = []
    
    # Get a sample tutor ID
    tutor_id_result = db_session.execute(text("SELECT id FROM tutors LIMIT 1"))
    tutor_id_row = tutor_id_result.fetchone()
    tutor_id = str(tutor_id_row.id) if tutor_id_row else None
    
    queries = [
        {
            'name': 'tutor_list',
            'query': """
                SELECT t.*, ts.*
                FROM tutors t
                LEFT JOIN tutor_scores ts ON t.id = ts.tutor_id
                WHERE t.is_active = true
                ORDER BY ts.reschedule_rate_30d DESC
                LIMIT 100
            """,
            'target_ms': 100,
        },
        {
            'name': 'tutor_detail',
            'query': f"""
                SELECT t.*, ts.*
                FROM tutors t
                LEFT JOIN tutor_scores ts ON t.id = ts.tutor_id
                WHERE t.id = '{tutor_id}'
            """ if tutor_id else None,
            'target_ms': 50,
        },
        {
            'name': 'session_history',
            'query': f"""
                SELECT s.*, r.*
                FROM sessions s
                LEFT JOIN reschedules r ON s.id = r.session_id
                WHERE s.tutor_id = '{tutor_id}'
                ORDER BY s.scheduled_time DESC
                LIMIT 50
            """ if tutor_id else None,
            'target_ms': 200,
        },
    ]
    
    for query_info in queries:
        if not query_info['query']:
            continue
        
        print(f"Testing {query_info['name']} query...")
        result = explain_analyze(db_session, query_info['query'], query_info['name'])
        result['target_ms'] = query_info['target_ms']
        results.append(result)
    
    return results


def print_results(results: list, indexes: list):
    """Print performance results."""
    print("\n" + "=" * 80)
    print("DATABASE PERFORMANCE RESULTS")
    print("=" * 80)
    
    print(f"\nTotal Indexes: {len(indexes)}")
    print("\nIndex Coverage:")
    tables = {}
    for idx in indexes:
        table = idx['table']
        if table not in tables:
            tables[table] = []
        tables[table].append(idx['name'])
    
    for table, idx_names in tables.items():
        print(f"  {table}: {len(idx_names)} indexes")
    
    print("\nQuery Performance:")
    for result in results:
        if not result['success']:
            print(f"\n❌ {result['query_name']}: {result.get('error', 'Unknown error')}")
            continue
        
        exec_time = result['execution_time_ms']
        target = result['target_ms']
        status = "✅" if exec_time < target else "❌"
        
        print(f"\n{status} {result['query_name']}:")
        print(f"  Execution Time: {exec_time:.2f}ms (target: <{target}ms)")
        print(f"  Planning Time: {result['planning_time_ms']:.2f}ms")
        print(f"  Total Time: {result['total_time_ms']:.2f}ms")
        
        # Check for sequential scans
        has_seq_scan = check_sequential_scans(result['plan'])
        if has_seq_scan:
            print(f"  ⚠️  Uses sequential scan (not optimal)")
        else:
            print(f"  ✅ No sequential scans")
        
        # Index usage
        indexes_used = result['indexes_used']
        if indexes_used:
            print(f"  ✅ Indexes used: {', '.join(indexes_used)}")
        else:
            print(f"  ⚠️  No indexes used")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Test database performance')
    parser.add_argument(
        '--output',
        type=str,
        default='database_performance.json',
        help='Output JSON file (default: database_performance.json)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='Database URL (default: from DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Connect to database
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    try:
        # Get indexes
        print("Fetching database indexes...")
        indexes = get_indexes(db_session)
        
        # Test key queries
        print("Testing key queries...")
        results = test_key_queries(db_session)
        
        # Print results
        print_results(results, indexes)
        
        # Save results
        output_data = {
            'indexes': indexes,
            'query_results': results,
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\n✅ Results saved to {args.output}")
        
        # Check if all targets met
        all_met = all(
            r['success'] and r['execution_time_ms'] < r['target_ms']
            for r in results
        )
        
        if all_met:
            print("\n✅ All performance targets met!")
            sys.exit(0)
        else:
            print("\n⚠️  Some performance targets not met")
            sys.exit(1)
            
    finally:
        db_session.close()


if __name__ == '__main__':
    main()


