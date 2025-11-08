#!/usr/bin/env python3
"""
Automated Frontend Performance Testing using Lighthouse CLI.

Tests frontend performance metrics (FCP, TTI, LCP, Lighthouse scores).

Usage:
    python scripts/performance_test/frontend_performance.py \
        --url http://localhost:4173 \
        --output frontend_performance.json
"""
import argparse
import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path


def check_lighthouse_installed() -> bool:
    """Check if Lighthouse CLI is installed."""
    try:
        result = subprocess.run(
            ['lighthouse', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_lighthouse():
    """Install Lighthouse CLI."""
    print("Installing Lighthouse CLI...")
    try:
        subprocess.run(['npm', 'install', '-g', 'lighthouse'], check=True)
        print("✅ Lighthouse installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Lighthouse: {e}")
        return False
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js first.")
        return False


def run_lighthouse(url: str, output_dir: str) -> dict:
    """Run Lighthouse audit."""
    output_file = os.path.join(output_dir, 'lighthouse-report.json')
    
    print(f"Running Lighthouse audit on {url}...")
    print("This may take 30-60 seconds...")
    
    try:
        result = subprocess.run(
            [
                'lighthouse',
                url,
                '--output=json',
                '--output-path=' + output_file,
                '--chrome-flags="--headless --no-sandbox"',
                '--quiet',
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"❌ Lighthouse failed: {result.stderr}")
            return None
        
        # Read the JSON report
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        return report
        
    except subprocess.TimeoutExpired:
        print("❌ Lighthouse timed out")
        return None
    except Exception as e:
        print(f"❌ Error running Lighthouse: {e}")
        return None


def extract_metrics(report: dict) -> dict:
    """Extract performance metrics from Lighthouse report."""
    if not report or 'lhr' not in report:
        return None
    
    lhr = report['lhr']
    audits = lhr.get('audits', {})
    categories = lhr.get('categories', {})
    
    performance_category = categories.get('performance', {})
    performance_score = performance_category.get('score', 0) * 100
    
    metrics = {
        'performance_score': round(performance_score, 1),
        'fcp': None,  # First Contentful Paint
        'lcp': None,  # Largest Contentful Paint
        'tti': None,  # Time to Interactive
        'speed_index': None,
        'total_blocking_time': None,
        'cumulative_layout_shift': None,
    }
    
    # Extract metrics from audits
    metric_map = {
        'first-contentful-paint': 'fcp',
        'largest-contentful-paint': 'lcp',
        'interactive': 'tti',
        'speed-index': 'speed_index',
        'total-blocking-time': 'total_blocking_time',
        'cumulative-layout-shift': 'cumulative_layout_shift',
    }
    
    for audit_key, metric_key in metric_map.items():
        audit = audits.get(audit_key, {})
        if audit and 'numericValue' in audit:
            value = audit['numericValue']
            # Convert to seconds for time-based metrics
            if metric_key in ['fcp', 'lcp', 'tti', 'speed_index']:
                metrics[metric_key] = round(value / 1000, 2)  # ms to seconds
            else:
                metrics[metric_key] = round(value, 2)
    
    return metrics


def print_results(metrics: dict, url: str):
    """Print performance results."""
    print("\n" + "=" * 80)
    print("FRONTEND PERFORMANCE RESULTS")
    print("=" * 80)
    print(f"URL: {url}")
    print()
    
    if not metrics:
        print("❌ No metrics available")
        return
    
    print(f"Performance Score: {metrics['performance_score']}/100")
    if metrics['performance_score'] >= 80:
        print("✅ Performance score meets target (≥80)")
    else:
        print("❌ Performance score below target (<80)")
    print()
    
    print("Key Metrics:")
    if metrics['fcp']:
        status = "✅" if metrics['fcp'] < 1.8 else "❌"
        print(f"  {status} First Contentful Paint (FCP): {metrics['fcp']}s (target: <1.8s)")
    
    if metrics['lcp']:
        status = "✅" if metrics['lcp'] < 2.5 else "❌"
        print(f"  {status} Largest Contentful Paint (LCP): {metrics['lcp']}s (target: <2.5s)")
    
    if metrics['tti']:
        status = "✅" if metrics['tti'] < 3.8 else "❌"
        print(f"  {status} Time to Interactive (TTI): {metrics['tti']}s (target: <3.8s)")
    
    if metrics['speed_index']:
        status = "✅" if metrics['speed_index'] < 3.4 else "❌"
        print(f"  {status} Speed Index: {metrics['speed_index']}s (target: <3.4s)")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Test frontend performance with Lighthouse')
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:4173',
        help='Frontend URL to test (default: http://localhost:4173)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='frontend_performance.json',
        help='Output JSON file (default: frontend_performance.json)'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install Lighthouse if not found'
    )
    
    args = parser.parse_args()
    
    # Check if Lighthouse is installed
    if not check_lighthouse_installed():
        print("⚠️  Lighthouse CLI not found")
        if args.install:
            if not install_lighthouse():
                sys.exit(1)
        else:
            print("Install with: npm install -g lighthouse")
            print("Or run with --install flag")
            sys.exit(1)
    
    # Create temp directory for Lighthouse output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run Lighthouse
        report = run_lighthouse(args.url, temp_dir)
        
        if not report:
            print("❌ Failed to generate Lighthouse report")
            sys.exit(1)
        
        # Extract metrics
        metrics = extract_metrics(report)
        
        if not metrics:
            print("❌ Failed to extract metrics from report")
            sys.exit(1)
        
        # Print results
        print_results(metrics, args.url)
        
        # Save results
        output_data = {
            'url': args.url,
            'metrics': metrics,
            'full_report_path': os.path.join(temp_dir, 'lighthouse-report.json'),
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✅ Results saved to {args.output}")
        
        # Check if all targets met
        targets_met = (
            metrics['performance_score'] >= 80 and
            metrics.get('fcp', 999) < 1.8 and
            metrics.get('tti', 999) < 3.8
        )
        
        if targets_met:
            print("\n✅ All performance targets met!")
            sys.exit(0)
        else:
            print("\n⚠️  Some performance targets not met")
            sys.exit(1)


if __name__ == '__main__':
    main()


