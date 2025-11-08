#!/usr/bin/env python3
"""
API Performance Testing Script

Tests API endpoints for performance metrics (p50, p95, p99 response times).

Usage:
    python scripts/performance_test/api_performance.py \
        --api-url http://localhost:8001 \
        --api-key your-api-key \
        --requests 1000 \
        --concurrency 50
"""
import argparse
import sys
import os
import time
import json
import statistics
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def percentile(data: List[float], p: float) -> float:
    """Calculate percentile."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * p)
    if index >= len(sorted_data):
        index = len(sorted_data) - 1
    return sorted_data[index]


def make_request(url: str, headers: Dict, timeout: int = 10) -> Dict:
    """Make HTTP request and return timing information."""
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'response_time_ms': elapsed,
            'error': None,
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            'success': False,
            'status_code': None,
            'response_time_ms': elapsed,
            'error': str(e),
        }


def test_endpoint(
    base_url: str,
    endpoint: str,
    api_key: str,
    num_requests: int,
    concurrency: int,
    params: Dict = None
) -> Dict:
    """Test a single endpoint with multiple concurrent requests."""
    url = f"{base_url}{endpoint}"
    if params:
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{query_string}"
    
    headers = {
        'X-API-Key': api_key,
    }
    
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
    
    response_times = []
    errors = []
    status_codes = []
    
    print(f"Testing {endpoint}...")
    print(f"  URL: {url}")
    print(f"  Requests: {num_requests}, Concurrency: {concurrency}")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(num_requests):
            future = executor.submit(make_request, url, headers)
            futures.append(future)
        
        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                response_times.append(result['response_time_ms'])
                status_codes.append(result['status_code'])
            else:
                errors.append(result)
    
    total_time = time.time() - start_time
    
    if response_times:
        return {
            'endpoint': endpoint,
            'url': url,
            'total_requests': num_requests,
            'successful_requests': len(response_times),
            'failed_requests': len(errors),
            'success_rate': (len(response_times) / num_requests) * 100,
            'total_time_seconds': total_time,
            'requests_per_second': num_requests / total_time,
            'response_time_ms': {
                'min': min(response_times),
                'max': max(response_times),
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p50': percentile(response_times, 0.50),
                'p95': percentile(response_times, 0.95),
                'p99': percentile(response_times, 0.99),
                'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            },
            'status_codes': dict(zip(*zip(*[(sc, status_codes.count(sc)) for sc in set(status_codes)]))),
            'errors': errors[:10] if errors else [],  # First 10 errors
        }
    else:
        return {
            'endpoint': endpoint,
            'url': url,
            'total_requests': num_requests,
            'successful_requests': 0,
            'failed_requests': len(errors),
            'success_rate': 0.0,
            'total_time_seconds': total_time,
            'requests_per_second': 0,
            'response_time_ms': None,
            'errors': errors,
        }


def print_results(results: Dict):
    """Print test results in a readable format."""
    print("\n" + "=" * 80)
    print(f"API Performance Test Results: {results['endpoint']}")
    print("=" * 80)
    print(f"URL: {results['url']}")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful: {results['successful_requests']}")
    print(f"Failed: {results['failed_requests']}")
    print(f"Success Rate: {results['success_rate']:.2f}%")
    print(f"Total Time: {results['total_time_seconds']:.2f} seconds")
    print(f"Requests/Second: {results['requests_per_second']:.2f}")
    
    if results['response_time_ms']:
        rt = results['response_time_ms']
        print(f"\nResponse Time (ms):")
        print(f"  Min: {rt['min']:.2f}")
        print(f"  Max: {rt['max']:.2f}")
        print(f"  Avg: {rt['avg']:.2f}")
        print(f"  Median: {rt['median']:.2f}")
        print(f"  P50: {rt['p50']:.2f}")
        print(f"  P95: {rt['p95']:.2f} {'✅' if rt['p95'] < 500 else '❌'}")
        print(f"  P99: {rt['p99']:.2f}")
        print(f"  Std Dev: {rt['std_dev']:.2f}")
        
        # Check if meets targets
        if rt['p95'] < 500:
            print("\n✅ P95 response time meets target (<500ms)")
        else:
            print(f"\n❌ P95 response time exceeds target ({rt['p95']:.2f}ms > 500ms)")
    
    if results['status_codes']:
        print(f"\nStatus Codes:")
        for code, count in results['status_codes'].items():
            print(f"  {code}: {count}")
    
    if results['errors']:
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results['errors'][:5]:
            print(f"  {error.get('error', 'Unknown error')}")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Test API performance')
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
        '--requests',
        type=int,
        default=1000,
        help='Number of requests per endpoint (default: 1000)'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=50,
        help='Number of concurrent requests (default: 50)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file (optional)'
    )
    parser.add_argument(
        '--endpoints',
        type=str,
        nargs='+',
        default=['/api/health', '/api/tutors', '/api/tutors/{id}'],
        help='Endpoints to test (default: /api/health /api/tutors /api/tutors/{id})'
    )
    parser.add_argument(
        '--tutor-id',
        type=str,
        default=None,
        help='Tutor ID for /api/tutors/{id} endpoint (required if testing that endpoint)'
    )
    
    args = parser.parse_args()
    
    all_results = []
    
    # Test each endpoint
    for endpoint in args.endpoints:
        # Replace {id} placeholder if needed
        if '{id}' in endpoint:
            if not args.tutor_id:
                print(f"Warning: Skipping {endpoint} - tutor-id not provided")
                continue
            endpoint = endpoint.replace('{id}', args.tutor_id)
        
        # Test with different query parameters for /api/tutors
        if endpoint == '/api/tutors':
            # Test multiple scenarios
            scenarios = [
                {'name': 'all_tutors', 'params': {'limit': 100}},
                {'name': 'high_risk', 'params': {'risk_status': 'high_risk', 'limit': 100}},
                {'name': 'sorted', 'params': {'sort_by': 'reschedule_rate_30d', 'sort_order': 'desc', 'limit': 100}},
                {'name': 'paginated', 'params': {'limit': 50, 'offset': 0}},
            ]
            
            for scenario in scenarios:
                result = test_endpoint(
                    args.api_url,
                    endpoint,
                    args.api_key,
                    args.requests,
                    args.concurrency,
                    scenario['params']
                )
                result['scenario'] = scenario['name']
                print_results(result)
                all_results.append(result)
        else:
            result = test_endpoint(
                args.api_url,
                endpoint,
                args.api_key,
                args.requests,
                args.concurrency
            )
            print_results(result)
            all_results.append(result)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✅ Results saved to {args.output}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for result in all_results:
        endpoint_name = result.get('scenario', result['endpoint'])
        if result['response_time_ms']:
            p95 = result['response_time_ms']['p95']
            status = '✅' if p95 < 500 else '❌'
            print(f"{status} {endpoint_name}: P95 = {p95:.2f}ms")
        else:
            print(f"❌ {endpoint_name}: All requests failed")


if __name__ == '__main__':
    main()


