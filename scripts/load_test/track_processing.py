#!/usr/bin/env python3
"""
Track session processing performance and validate 1-hour SLA.

This script queries the database to track how long sessions take to process
and validates that all sessions are processed within the 1-hour SLA.

Usage:
    python scripts/load_test/track_processing.py \
        --start-time "2024-01-01 00:00:00" \
        --database-url postgresql://user@localhost:5432/tutor_scoring
"""
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))


def get_processing_times(db_session, start_time: datetime) -> List[Dict]:
    """
    Query database for session processing times.
    
    Returns list of sessions with processing time information.
    """
    query = text("""
        SELECT 
            s.id AS session_id,
            s.created_at,
            s.status,
            ts.last_calculated_at AS processing_completed_at,
            EXTRACT(EPOCH FROM (ts.last_calculated_at - s.created_at)) AS processing_seconds
        FROM sessions s
        JOIN tutor_scores ts ON s.tutor_id = ts.tutor_id
        WHERE s.created_at >= :start_time
        ORDER BY processing_seconds DESC
    """)
    
    result = db_session.execute(query, {"start_time": start_time})
    rows = result.fetchall()
    
    sessions = []
    for row in rows:
        sessions.append({
            'session_id': str(row.session_id),
            'created_at': row.created_at,
            'status': row.status,
            'processing_completed_at': row.processing_completed_at,
            'processing_seconds': float(row.processing_seconds) if row.processing_seconds else None,
        })
    
    return sessions


def get_unprocessed_sessions(db_session, start_time: datetime) -> List[Dict]:
    """
    Find sessions that haven't been processed yet (no tutor_score update).
    """
    query = text("""
        SELECT 
            s.id AS session_id,
            s.created_at,
            s.status,
            s.tutor_id
        FROM sessions s
        LEFT JOIN tutor_scores ts ON s.tutor_id = ts.tutor_id
        WHERE s.created_at >= :start_time
        AND (ts.last_calculated_at IS NULL OR ts.last_calculated_at < s.created_at)
        ORDER BY s.created_at DESC
    """)
    
    result = db_session.execute(query, {"start_time": start_time})
    rows = result.fetchall()
    
    sessions = []
    for row in rows:
        sessions.append({
            'session_id': str(row.session_id),
            'created_at': row.created_at,
            'status': row.status,
            'tutor_id': str(row.tutor_id),
        })
    
    return sessions


def calculate_statistics(sessions: List[Dict]) -> Dict:
    """Calculate processing statistics."""
    if not sessions:
        return {
            'total': 0,
            'avg': 0,
            'min': 0,
            'max': 0,
            'p50': 0,
            'p95': 0,
            'p99': 0,
            'within_sla': 0,
            'exceeding_sla': 0,
            'compliance_rate': 0.0,
        }
    
    processing_times = [s['processing_seconds'] for s in sessions if s['processing_seconds'] is not None]
    
    if not processing_times:
        return {
            'total': len(sessions),
            'avg': 0,
            'min': 0,
            'max': 0,
            'p50': 0,
            'p95': 0,
            'p99': 0,
            'within_sla': 0,
            'exceeding_sla': len(sessions),
            'compliance_rate': 0.0,
        }
    
    processing_times.sort()
    
    sla_threshold = 3600  # 1 hour in seconds
    within_sla = sum(1 for t in processing_times if t <= sla_threshold)
    
    return {
        'total': len(sessions),
        'avg': sum(processing_times) / len(processing_times),
        'min': min(processing_times),
        'max': max(processing_times),
        'p50': processing_times[len(processing_times) // 2],
        'p95': processing_times[int(len(processing_times) * 0.95)],
        'p99': processing_times[int(len(processing_times) * 0.99)],
        'within_sla': within_sla,
        'exceeding_sla': len(sessions) - within_sla,
        'compliance_rate': (within_sla / len(sessions)) * 100 if sessions else 0.0,
    }


def print_report(sessions: List[Dict], stats: Dict, unprocessed: List[Dict]):
    """Print performance report."""
    print("=" * 80)
    print("SESSION PROCESSING PERFORMANCE REPORT")
    print("=" * 80)
    print()
    
    print(f"Total Sessions Processed: {stats['total']}")
    print(f"Unprocessed Sessions: {len(unprocessed)}")
    print()
    
    if stats['total'] > 0:
        print("Processing Time Statistics:")
        print(f"  Average: {stats['avg']:.2f} seconds ({stats['avg']/60:.2f} minutes)")
        print(f"  Minimum: {stats['min']:.2f} seconds ({stats['min']/60:.2f} minutes)")
        print(f"  Maximum: {stats['max']:.2f} seconds ({stats['max']/60:.2f} minutes)")
        print(f"  P50 (Median): {stats['p50']:.2f} seconds ({stats['p50']/60:.2f} minutes)")
        print(f"  P95: {stats['p95']:.2f} seconds ({stats['p95']/60:.2f} minutes)")
        print(f"  P99: {stats['p99']:.2f} seconds ({stats['p99']/60:.2f} minutes)")
        print()
        
        print("SLA Compliance (1-hour threshold):")
        print(f"  Sessions within SLA: {stats['within_sla']} ({stats['compliance_rate']:.2f}%)")
        print(f"  Sessions exceeding SLA: {stats['exceeding_sla']} ({100 - stats['compliance_rate']:.2f}%)")
        print()
        
        if stats['exceeding_sla'] > 0:
            print("⚠️  WARNING: Some sessions exceeded the 1-hour SLA!")
            print("Top 10 slowest sessions:")
            slowest = sorted(sessions, key=lambda x: x['processing_seconds'] or 0, reverse=True)[:10]
            for session in slowest:
                if session['processing_seconds']:
                    print(f"  Session {session['session_id'][:8]}...: {session['processing_seconds']:.2f}s ({session['processing_seconds']/60:.2f} minutes)")
        else:
            print("✅ All sessions processed within 1-hour SLA!")
    
    if unprocessed:
        print(f"\n⚠️  WARNING: {len(unprocessed)} sessions have not been processed yet!")
        print("Unprocessed sessions (first 10):")
        for session in unprocessed[:10]:
            print(f"  Session {session['session_id'][:8]}...: Created at {session['created_at']}")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Track session processing performance')
    parser.add_argument(
        '--start-time',
        type=str,
        required=True,
        help='Start time for tracking (format: "YYYY-MM-DD HH:MM:SS")'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='Database URL (default: from DATABASE_URL env var)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for JSON report (optional)'
    )
    
    args = parser.parse_args()
    
    # Parse start time
    try:
        start_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print(f"Error: Invalid start time format. Use 'YYYY-MM-DD HH:MM:SS'")
        sys.exit(1)
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set or --database-url not provided")
        sys.exit(1)
    
    # Connect to database
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    try:
        # Get processing times
        print(f"Querying sessions created after {start_time}...")
        sessions = get_processing_times(db_session, start_time)
        
        # Get unprocessed sessions
        unprocessed = get_unprocessed_sessions(db_session, start_time)
        
        # Calculate statistics
        stats = calculate_statistics(sessions)
        
        # Print report
        print_report(sessions, stats, unprocessed)
        
        # Save to file if requested
        if args.output:
            import json
            report = {
                'start_time': start_time.isoformat(),
                'statistics': stats,
                'sessions': sessions[:100],  # Limit to first 100 for file size
                'unprocessed_count': len(unprocessed),
                'unprocessed': unprocessed[:100],
            }
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nReport saved to {args.output}")
        
        # Exit with error if SLA not met
        if stats['compliance_rate'] < 100.0:
            print("\n❌ SLA compliance is below 100%!")
            sys.exit(1)
        elif unprocessed:
            print("\n❌ Some sessions have not been processed!")
            sys.exit(1)
        else:
            print("\n✅ All sessions processed successfully within SLA!")
            sys.exit(0)
            
    finally:
        db_session.close()


if __name__ == '__main__':
    main()


