#!/usr/bin/env python3
"""
Python-based load test script for session ingestion.

Alternative to K6 for users who don't have K6 installed.

Usage:
    python scripts/load_test/session_load.py \
        --api-url http://localhost:8001 \
        --api-key your-api-key \
        --sessions 3000 \
        --rate 125 \
        --duration 3600
"""
import argparse
import sys
import os
import time
import json
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))


def load_tutor_ids(file_path: str = 'tutor_ids.json') -> List[str]:
    """Load tutor IDs from JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get('tutor_ids', [])
    return []


def generate_session_payload(tutor_id: str) -> Dict:
    """Generate a realistic session payload."""
    session_id = str(uuid.uuid4())
    student_id = f"student-{random.randint(1000, 9999)}"
    
    # Generate timestamps
    now = datetime.now()
    scheduled_time = now - timedelta(hours=random.random())
    completed_time = scheduled_time + timedelta(minutes=30 + random.random() * 90)
    
    # Status distribution: 70% completed, 25% rescheduled, 5% no_show
    status_rand = random.random()
    if status_rand < 0.70:
        status = 'completed'
    elif status_rand < 0.95:
        status = 'rescheduled'
    else:
        status = 'no_show'
    
    payload = {
        'session_id': session_id,
        'tutor_id': tutor_id,
        'student_id': student_id,
        'scheduled_time': scheduled_time.isoformat(),
        'completed_time': completed_time.isoformat(),
        'status': status,
        'duration_minutes': int(30 + random.random() * 90),
    }
    
    # Add reschedule_info if status is 'rescheduled'
    if status == 'rescheduled':
        cancelled_at = scheduled_time - timedelta(hours=random.random() * 24)
        new_time = scheduled_time + timedelta(days=1 + random.random() * 7)
        
        payload['reschedule_info'] = {
            'initiator': 'tutor' if random.random() > 0.3 else 'student',
            'original_time': scheduled_time.isoformat(),
            'new_time': new_time.isoformat(),
            'reason': 'Schedule conflict',
            'reason_code': 'CONFLICT',
            'cancelled_at': cancelled_at.isoformat(),
        }
    
    return payload


def send_session(api_url: str, api_key: str, payload: Dict, timeout: int = 10) -> Dict:
    """Send a session creation request."""
    url = f"{api_url}/api/sessions"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        elapsed = (time.time() - start_time) * 1000  # milliseconds
        
        return {
            'success': response.status_code == 202,
            'status_code': response.status_code,
            'response_time_ms': elapsed,
            'session_id': payload['session_id'],
            'error': None,
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            'success': False,
            'status_code': None,
            'response_time_ms': elapsed,
            'session_id': payload['session_id'],
            'error': str(e),
        }


def run_load_test(
    api_url: str,
    api_key: str,
    tutor_ids: List[str],
    num_sessions: int,
    rate: float,  # sessions per hour
    duration: int = None  # seconds
) -> Dict:
    """Run load test."""
    print(f"Starting load test...")
    print(f"  API URL: {api_url}")
    print(f"  Sessions: {num_sessions}")
    print(f"  Rate: {rate} sessions/hour")
    print(f"  Duration: {duration} seconds" if duration else "  Duration: Until all sessions sent")
    print()
    
    if not tutor_ids:
        print("Error: No tutor IDs available. Run get_tutor_ids.py first.")
        sys.exit(1)
    
    # Create session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Calculate delay between requests
    delay = 3600.0 / rate if rate > 0 else 0  # seconds between requests
    
    results = []
    start_time = time.time()
    end_time = start_time + duration if duration else None
    
    print(f"Sending sessions (delay: {delay:.2f}s between requests)...")
    
    for i in range(num_sessions):
        # Check if we've exceeded duration
        if end_time and time.time() >= end_time:
            print(f"\nDuration limit reached. Sent {i} sessions.")
            break
        
        # Select random tutor
        tutor_id = random.choice(tutor_ids)
        
        # Generate payload
        payload = generate_session_payload(tutor_id)
        
        # Send request
        result = send_session(api_url, api_key, payload)
        results.append(result)
        
        # Print progress every 100 sessions
        if (i + 1) % 100 == 0:
            success_count = sum(1 for r in results if r['success'])
            print(f"  Sent {i + 1}/{num_sessions} sessions ({success_count} successful)")
        
        # Sleep between requests (except for last one)
        if i < num_sessions - 1 and delay > 0:
            time.sleep(delay)
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    response_times = [r['response_time_ms'] for r in successful]
    
    stats = {
        'total_sessions': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'success_rate': (len(successful) / len(results)) * 100 if results else 0,
        'total_time_seconds': total_time,
        'sessions_per_second': len(results) / total_time if total_time > 0 else 0,
    }
    
    if response_times:
        response_times.sort()
        stats['response_time_ms'] = {
            'min': min(response_times),
            'max': max(response_times),
            'avg': sum(response_times) / len(response_times),
            'p50': response_times[len(response_times) // 2],
            'p95': response_times[int(len(response_times) * 0.95)],
            'p99': response_times[int(len(response_times) * 0.99)],
        }
    else:
        stats['response_time_ms'] = None
    
    if failed:
        stats['errors'] = {}
        for error in failed[:10]:  # First 10 errors
            error_msg = error.get('error', 'Unknown')
            stats['errors'][error_msg] = stats['errors'].get(error_msg, 0) + 1
    
    return stats


def print_results(stats: Dict):
    """Print test results."""
    print("\n" + "=" * 80)
    print("LOAD TEST RESULTS")
    print("=" * 80)
    print(f"Total Sessions: {stats['total_sessions']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print(f"Total Time: {stats['total_time_seconds']:.2f} seconds")
    print(f"Sessions/Second: {stats['sessions_per_second']:.2f}")
    
    if stats['response_time_ms']:
        rt = stats['response_time_ms']
        print(f"\nResponse Time (ms):")
        print(f"  Min: {rt['min']:.2f}")
        print(f"  Max: {rt['max']:.2f}")
        print(f"  Avg: {rt['avg']:.2f}")
        print(f"  P50: {rt['p50']:.2f}")
        print(f"  P95: {rt['p95']:.2f}")
        print(f"  P99: {rt['p99']:.2f}")
    
    if stats.get('errors'):
        print(f"\nErrors:")
        for error, count in stats['errors'].items():
            print(f"  {error}: {count}")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Load test session ingestion')
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:8001',
        help='API base URL (default: http://localhost:8001)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        required=True,
        help='API key for authentication'
    )
    parser.add_argument(
        '--sessions',
        type=int,
        default=3000,
        help='Number of sessions to send (default: 3000)'
    )
    parser.add_argument(
        '--rate',
        type=float,
        default=125.0,
        help='Sessions per hour (default: 125)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Maximum duration in seconds (default: calculate from rate)'
    )
    parser.add_argument(
        '--tutor-ids-file',
        type=str,
        default='tutor_ids.json',
        help='File containing tutor IDs (default: tutor_ids.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file (optional)'
    )
    
    args = parser.parse_args()
    
    # Load tutor IDs
    tutor_ids = load_tutor_ids(args.tutor_ids_file)
    
    if not tutor_ids:
        print(f"Error: No tutor IDs found in {args.tutor_ids_file}")
        print("Run: python scripts/load_test/get_tutor_ids.py")
        sys.exit(1)
    
    print(f"Loaded {len(tutor_ids)} tutor IDs")
    
    # Run load test
    stats = run_load_test(
        args.api_url,
        args.api_key,
        tutor_ids,
        args.sessions,
        args.rate,
        args.duration
    )
    
    # Print results
    print_results(stats)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()


