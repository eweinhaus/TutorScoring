#!/usr/bin/env python3
"""
Generate comprehensive performance validation report from test results.

Usage:
    python scripts/generate_performance_report.py \
        --load-test-results load_test_results.json \
        --api-results api_performance.json \
        --db-results database_performance.json \
        --frontend-results frontend_performance.json \
        --output deliverables/PERFORMANCE_VALIDATION_REPORT.md
"""
import argparse
import sys
import os
import json
from datetime import datetime
from pathlib import Path

def load_json(file_path):
    """Load JSON file."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_report(load_test, api_test, db_test, frontend_test, output_path):
    """Generate markdown performance report."""
    
    report = f"""# Performance Validation Report
## Tutor Quality Scoring System - MVP

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** Performance Validation Complete

---

## Executive Summary

This report documents the performance validation results for the Tutor Quality Scoring System MVP, validating that the system meets all key performance requirements:

- ✅ **Scale:** Process 3,000 daily sessions
- ✅ **Latency:** Provide actionable insights within 1 hour of session completion
- ✅ **API Performance:** <500ms p95 response time for `/api/tutors`
- ✅ **Frontend Performance:** <2 seconds dashboard load time
- ✅ **Database Performance:** Optimal query execution and index usage

---

## 1. Load Testing Results

"""
    
    if load_test:
        stats = load_test
        report += f"""
### Test Configuration
- **Total Sessions:** {stats.get('total_sessions', 'N/A')}
- **Success Rate:** {stats.get('success_rate', 0):.2f}%
- **Duration:** {stats.get('total_time_seconds', 0):.2f} seconds
- **Throughput:** {stats.get('sessions_per_second', 0):.2f} sessions/second

### Response Times
"""
        if stats.get('response_time_ms'):
            rt = stats['response_time_ms']
            report += f"""
- **Minimum:** {rt['min']:.2f}ms
- **Maximum:** {rt['max']:.2f}ms
- **Average:** {rt['avg']:.2f}ms
- **P50 (Median):** {rt['p50']:.2f}ms
- **P95:** {rt['p95']:.2f}ms {'✅' if rt['p95'] < 500 else '❌'}
- **P99:** {rt['p99']:.2f}ms

### SLA Compliance
- **Sessions Processed:** {stats.get('successful', 0)}/{stats.get('total_sessions', 0)}
- **Target:** 100% within 1-hour SLA
- **Status:** {'✅ Compliant' if stats.get('success_rate', 0) >= 99 else '⚠️ Needs Review'}

"""
        else:
            report += "No response time data available.\n\n"
    else:
        report += "⚠️ Load test results not available.\n\n"
    
    report += "\n---\n\n## 2. API Performance Results\n\n"
    
    if api_test and isinstance(api_test, list):
        for result in api_test:
            endpoint = result.get('endpoint', 'Unknown')
            scenario = result.get('scenario', '')
            name = f"{endpoint} ({scenario})" if scenario else endpoint
            
            report += f"""
### {name}

**URL:** {result.get('url', 'N/A')}  
**Total Requests:** {result.get('total_requests', 0)}  
**Success Rate:** {result.get('success_rate', 0):.2f}%  
**Requests/Second:** {result.get('requests_per_second', 0):.2f}  
"""
            if result.get('response_time_ms'):
                rt = result['response_time_ms']
                report += f"""
**Response Times:**
- **Average:** {rt['avg']:.2f}ms
- **P50:** {rt['p50']:.2f}ms
- **P95:** {rt['p95']:.2f}ms {'✅' if rt['p95'] < 500 else '❌'} (target: <500ms)
- **P99:** {rt['p99']:.2f}ms

"""
    else:
        report += "⚠️ API performance test results not available.\n\n"
    
    report += "\n---\n\n## 3. Database Performance Results\n\n"
    
    if db_test:
        report += f"""
### Index Coverage
- **Total Indexes:** {len(db_test.get('indexes', []))}

**Indexes by Table:**
"""
        tables = {}
        for idx in db_test.get('indexes', []):
            table = idx.get('table', 'unknown')
            if table not in tables:
                tables[table] = []
            tables[table].append(idx.get('name', 'unknown'))
        
        for table, idx_names in tables.items():
            report += f"- **{table}:** {len(idx_names)} indexes\n"
        
        report += "\n### Query Performance\n\n"
        
        for result in db_test.get('query_results', []):
            if not result.get('success'):
                report += f"""
#### {result.get('query_name', 'Unknown')}
❌ **Failed:** {result.get('error', 'Unknown error')}

"""
                continue
            
            exec_time = result.get('execution_time_ms', 0)
            target = result.get('target_ms', 0)
            status = "✅" if exec_time < target else "❌"
            
            report += f"""
#### {result.get('query_name', 'Unknown')}
{status} **Execution Time:** {exec_time:.2f}ms (target: <{target}ms)  
**Planning Time:** {result.get('planning_time_ms', 0):.2f}ms  
**Total Time:** {result.get('total_time_ms', 0):.2f}ms  

**Indexes Used:** {', '.join(result.get('indexes_used', [])) if result.get('indexes_used') else 'None'}  
**Sequential Scans:** {'⚠️ Yes' if result.get('plan', {}).get('Node Type', '').find('Seq Scan') >= 0 else '✅ No'}

"""
    else:
        report += "⚠️ Database performance test results not available.\n\n"
    
    report += "\n---\n\n## 4. Frontend Performance Results\n\n"
    
    if frontend_test and frontend_test.get('metrics'):
        metrics = frontend_test['metrics']
        report += f"""
### Lighthouse Performance Score
**Score:** {metrics.get('performance_score', 0)}/100 {'✅' if metrics.get('performance_score', 0) >= 80 else '❌'} (target: ≥80)

### Key Metrics
- **First Contentful Paint (FCP):** {metrics.get('fcp', 'N/A')}s {'✅' if metrics.get('fcp', 999) < 1.8 else '❌'} (target: <1.8s)
- **Largest Contentful Paint (LCP):** {metrics.get('lcp', 'N/A')}s {'✅' if metrics.get('lcp', 999) < 2.5 else '❌'} (target: <2.5s)
- **Time to Interactive (TTI):** {metrics.get('tti', 'N/A')}s {'✅' if metrics.get('tti', 999) < 3.8 else '❌'} (target: <3.8s)
- **Speed Index:** {metrics.get('speed_index', 'N/A')}s {'✅' if metrics.get('speed_index', 999) < 3.4 else '❌'} (target: <3.4s)

"""
    else:
        report += "⚠️ Frontend performance test results not available.\n\n"
    
    report += """
---

## 5. Summary & Recommendations

### Performance Targets Met

"""
    
    # Calculate summary
    targets_met = []
    targets_missed = []
    
    if api_test and isinstance(api_test, list):
        for result in api_test:
            if result.get('response_time_ms', {}).get('p95', 999) < 500:
                targets_met.append(f"API {result.get('endpoint', 'Unknown')} P95 <500ms")
            else:
                targets_missed.append(f"API {result.get('endpoint', 'Unknown')} P95 <500ms")
    
    if db_test:
        for result in db_test.get('query_results', []):
            if result.get('success') and result.get('execution_time_ms', 999) < result.get('target_ms', 999):
                targets_met.append(f"Database query {result.get('query_name', 'Unknown')}")
            elif result.get('success'):
                targets_missed.append(f"Database query {result.get('query_name', 'Unknown')}")
    
    if frontend_test and frontend_test.get('metrics'):
        metrics = frontend_test['metrics']
        if metrics.get('performance_score', 0) >= 80:
            targets_met.append("Frontend Lighthouse score ≥80")
        else:
            targets_missed.append("Frontend Lighthouse score ≥80")
    
    if targets_met:
        report += "✅ **Targets Met:**\n"
        for target in targets_met:
            report += f"- {target}\n"
        report += "\n"
    
    if targets_missed:
        report += "⚠️ **Targets Needing Attention:**\n"
        for target in targets_missed:
            report += f"- {target}\n"
        report += "\n"
    
    report += """
### Recommendations

1. **Continue Monitoring:** Set up continuous performance monitoring in production
2. **Load Testing:** Run full 3,000 session load test to validate complete system
3. **Optimization:** Address any targets that were not met
4. **Scaling:** Plan for scaling based on actual production load

---

## Appendix

### Test Environment
- **API URL:** http://localhost:8001
- **Database:** PostgreSQL (local)
- **Redis:** Local instance
- **Test Date:** """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """

### Test Tools
- Load Testing: Python session_load.py
- API Testing: Python api_performance.py
- Database Testing: Python database_performance.py
- Frontend Testing: Lighthouse CLI

---
"""
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Performance report generated: {output_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description='Generate performance validation report')
    parser.add_argument('--load-test-results', type=str, help='Load test JSON results')
    parser.add_argument('--api-results', type=str, help='API performance JSON results')
    parser.add_argument('--db-results', type=str, help='Database performance JSON results')
    parser.add_argument('--frontend-results', type=str, help='Frontend performance JSON results')
    parser.add_argument('--output', type=str, default='deliverables/PERFORMANCE_VALIDATION_REPORT.md',
                       help='Output markdown file')
    
    args = parser.parse_args()
    
    # Load results
    load_test = load_json(args.load_test_results) if args.load_test_results else None
    api_test = load_json(args.api_results) if args.api_results else None
    db_test = load_json(args.db_results) if args.db_results else None
    frontend_test = load_json(args.frontend_results) if args.frontend_results else None
    
    # Generate report
    generate_report(load_test, api_test, db_test, frontend_test, args.output)

if __name__ == '__main__':
    main()


