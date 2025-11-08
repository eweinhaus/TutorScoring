#!/usr/bin/env python3
"""
Monitor system resources during load testing.

Monitors:
- Celery queue depth (Redis)
- Worker CPU/memory usage
- Database connection pool usage
- API response times

Usage:
    python scripts/load_test/monitor_resources.py \
        --interval 60 \
        --duration 3600 \
        --output monitoring.csv
"""
import argparse
import sys
import os
import time
import csv
from datetime import datetime
from typing import Dict, Optional
import psutil
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))


def get_redis_queue_depth(redis_client: redis.Redis, queue_name: str = 'celery') -> int:
    """Get current queue depth from Redis."""
    try:
        # Celery uses a list for the queue
        return redis_client.llen(queue_name)
    except Exception as e:
        print(f"Error getting queue depth: {e}")
        return -1


def get_worker_processes() -> Dict:
    """Find Celery worker processes and get their CPU/memory usage."""
    workers = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'celery' in cmdline.lower() and 'worker' in cmdline.lower():
                    workers.append({
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.cpu_percent(interval=0.1),
                        'memory_percent': proc.info['memory_percent'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if workers:
        return {
            'count': len(workers),
            'total_cpu': sum(w['cpu_percent'] for w in workers),
            'avg_cpu': sum(w['cpu_percent'] for w in workers) / len(workers),
            'total_memory_mb': sum(w['memory_mb'] for w in workers),
            'avg_memory_percent': sum(w['memory_percent'] for w in workers) / len(workers),
        }
    else:
        return {
            'count': 0,
            'total_cpu': 0,
            'avg_cpu': 0,
            'total_memory_mb': 0,
            'avg_memory_percent': 0,
        }


def get_database_connections(db_session) -> Dict:
    """Get database connection pool statistics."""
    try:
        query = text("""
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """)
        result = db_session.execute(query)
        row = result.fetchone()
        
        return {
            'total': row.total_connections if row else 0,
            'active': row.active_connections if row else 0,
            'idle': row.idle_connections if row else 0,
        }
    except Exception as e:
        print(f"Error getting database connections: {e}")
        return {'total': -1, 'active': -1, 'idle': -1}


def monitor_loop(
    redis_client: redis.Redis,
    db_session,
    interval: int,
    duration: int,
    output_file: Optional[str]
):
    """Main monitoring loop."""
    start_time = time.time()
    end_time = start_time + duration
    
    metrics = []
    
    print(f"Starting monitoring (interval: {interval}s, duration: {duration}s)")
    print("=" * 80)
    
    try:
        while time.time() < end_time:
            timestamp = datetime.now()
            
            # Collect metrics
            queue_depth = get_redis_queue_depth(redis_client)
            workers = get_worker_processes()
            db_connections = get_database_connections(db_session)
            
            metric = {
                'timestamp': timestamp.isoformat(),
                'queue_depth': queue_depth,
                'worker_count': workers['count'],
                'worker_avg_cpu': workers['avg_cpu'],
                'worker_total_memory_mb': workers['total_memory_mb'],
                'worker_avg_memory_percent': workers['avg_memory_percent'],
                'db_total_connections': db_connections['total'],
                'db_active_connections': db_connections['active'],
                'db_idle_connections': db_connections['idle'],
            }
            
            metrics.append(metric)
            
            # Print current metrics
            print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"Queue: {queue_depth:4d} | "
                  f"Workers: {workers['count']} (CPU: {workers['avg_cpu']:5.1f}%, "
                  f"Mem: {workers['avg_memory_percent']:5.1f}%) | "
                  f"DB: {db_connections['active']}/{db_connections['total']} active")
            
            # Sleep until next interval
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    
    print("\n" + "=" * 80)
    print("Monitoring complete")
    
    # Save to CSV if requested
    if output_file and metrics:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)
        print(f"Metrics saved to {output_file}")
    
    # Print summary
    if metrics:
        print("\nSummary Statistics:")
        queue_depths = [m['queue_depth'] for m in metrics if m['queue_depth'] >= 0]
        if queue_depths:
            print(f"  Queue Depth - Avg: {sum(queue_depths)/len(queue_depths):.1f}, "
                  f"Max: {max(queue_depths)}, Min: {min(queue_depths)}")
        
        worker_cpus = [m['worker_avg_cpu'] for m in metrics if m['worker_count'] > 0]
        if worker_cpus:
            print(f"  Worker CPU - Avg: {sum(worker_cpus)/len(worker_cpus):.1f}%, "
                  f"Max: {max(worker_cpus):.1f}%")
        
        db_active = [m['db_active_connections'] for m in metrics if m['db_active_connections'] >= 0]
        if db_active:
            print(f"  DB Active Connections - Avg: {sum(db_active)/len(db_active):.1f}, "
                  f"Max: {max(db_active)}")


def main():
    parser = argparse.ArgumentParser(description='Monitor system resources during load testing')
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Monitoring interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=3600,
        help='Monitoring duration in seconds (default: 3600 = 1 hour)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV file (optional)'
    )
    parser.add_argument(
        '--redis-url',
        type=str,
        default=None,
        help='Redis URL (default: from REDIS_URL env var)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='Database URL (default: from DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Get Redis URL
    redis_url = args.redis_url or os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL')
    if not redis_url:
        print("Error: REDIS_URL or CELERY_BROKER_URL environment variable not set")
        sys.exit(1)
    
    # Connect to Redis
    try:
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        sys.exit(1)
    
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
        monitor_loop(redis_client, db_session, args.interval, args.duration, args.output)
    finally:
        db_session.close()


if __name__ == '__main__':
    main()


