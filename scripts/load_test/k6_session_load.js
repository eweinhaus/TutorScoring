/**
 * K6 Load Test Script for Session Ingestion
 * 
 * Simulates 3,000 daily sessions over 24 hours (or compressed).
 * 
 * Usage:
 *   k6 run scripts/load_test/k6_session_load.js \
 *     --env API_URL=http://localhost:8001 \
 *     --env API_KEY=your-api-key-here
 * 
 * Compressed version (1 hour):
 *   k6 run scripts/load_test/k6_session_load.js \
 *     --env API_URL=http://localhost:8001 \
 *     --env API_KEY=your-api-key-here \
 *     --env COMPRESSED=true
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// Configuration
const API_URL = __ENV.API_URL || 'http://localhost:8001';
const API_KEY = __ENV.API_KEY || 'test-api-key';
const COMPRESSED = __ENV.COMPRESSED === 'true';

// Load test options
export const options = COMPRESSED
  ? {
      // Compressed version: 3,000 sessions in 1 hour
      stages: [
        { duration: '5m', target: 100 },   // Ramp up to 100 concurrent users
        { duration: '50m', target: 3000 },  // Maintain 3,000 sessions/hour
        { duration: '5m', target: 0 },      // Ramp down
      ],
      thresholds: {
        http_req_duration: ['p(95)<500'],  // 95% of requests should be below 500ms
        http_req_failed: ['rate<0.01'],     // Error rate should be less than 1%
      },
    }
  : {
      // Real-time version: 3,000 sessions over 24 hours (~125/hour)
      stages: [
        { duration: '1h', target: 5 },      // Ramp up slowly
        { duration: '22h', target: 125 },   // Maintain ~125 sessions/hour
        { duration: '1h', target: 0 },      // Ramp down
      ],
      thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
      },
    };

// Tutor IDs - update these by running: python scripts/load_test/get_tutor_ids.py
// Then copy the IDs from the output into this array
const SAMPLE_TUTOR_IDS = [
  'b9fe3168-5dbd-441e-9552-85059eea9bee',
  '502883b8-11af-4506-a560-51be8390c6b9',
  'bbd35be6-f882-496c-ac98-478fa44c8ba2',
  'db3e46ea-d81b-436a-960a-f45754b0d195',
  'a4af1600-eb61-4284-84a3-8ac6e73257c1',
  '1c269e13-9e13-4bc8-9c88-74987b55ff00',
  '2b45a2f3-eff5-4714-bfb8-e8c6e8c84b9f',
  '11a4e19e-3b69-4c47-9828-d01c56993d33',
  'c39201d5-0635-4ceb-9183-2d929ceb6897',
  'da86b154-f75a-42fd-b650-cc5152fbf153',
];

// Status distribution: 70% completed, 25% rescheduled, 5% no_show
const STATUSES = ['completed', 'completed', 'completed', 'completed', 'completed', 'completed', 'completed', 'rescheduled', 'rescheduled', 'no_show'];

export default function () {
  // Generate unique session ID
  const sessionId = uuidv4();
  
  // Select random tutor ID (in production, fetch from API)
  const tutorId = SAMPLE_TUTOR_IDS[Math.floor(Math.random() * SAMPLE_TUTOR_IDS.length)];
  
  // Generate student ID
  const studentId = `student-${Math.floor(Math.random() * 10000)}`;
  
  // Generate timestamps
  const now = new Date();
  const scheduledTime = new Date(now.getTime() - Math.random() * 3600000); // 0-1 hour ago
  const completedTime = new Date(scheduledTime.getTime() + (30 + Math.random() * 90) * 60000); // 30-120 minutes after scheduled
  
  // Select status
  const status = STATUSES[Math.floor(Math.random() * STATUSES.length)];
  
  // Build request payload
  const payload = {
    session_id: sessionId,
    tutor_id: tutorId,
    student_id: studentId,
    scheduled_time: scheduledTime.toISOString(),
    completed_time: completedTime.toISOString(),
    status: status,
    duration_minutes: Math.floor(30 + Math.random() * 90), // 30-120 minutes
  };
  
  // Add reschedule_info if status is 'rescheduled'
  if (status === 'rescheduled') {
    const cancelledAt = new Date(scheduledTime.getTime() - Math.random() * 86400000); // 0-24 hours before scheduled
    const newTime = new Date(scheduledTime.getTime() + (1 + Math.random() * 7) * 86400000); // 1-7 days later
    
    payload.reschedule_info = {
      initiator: Math.random() > 0.3 ? 'tutor' : 'student', // 70% tutor-initiated
      original_time: scheduledTime.toISOString(),
      new_time: newTime.toISOString(),
      reason: 'Schedule conflict',
      reason_code: 'CONFLICT',
      cancelled_at: cancelledAt.toISOString(),
    };
  }
  
  // Set headers
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  };
  
  // Make POST request
  const response = http.post(
    `${API_URL}/api/sessions`,
    JSON.stringify(payload),
    { headers: headers }
  );
  
  // Check response
  const success = check(response, {
    'status is 202': (r) => r.status === 202,
    'response has session_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id !== undefined;
      } catch (e) {
        return false;
      }
    },
  });
  
  if (!success) {
    console.error(`Failed request: ${response.status} - ${response.body}`);
  }
  
  // Sleep between requests (for real-time simulation)
  if (!COMPRESSED) {
    sleep(Math.random() * 28.8); // Average ~125 requests/hour = ~28.8 seconds between requests
  } else {
    sleep(0.1); // Minimal sleep for compressed test
  }
}

export function handleSummary(data) {
  return {
    'stdout': `
========================================
Load Test Summary
========================================
Duration: ${Math.round(data.state.testRunDurationMs / 1000)}s
Requests: ${data.metrics.http_reqs.values.count}
Failed: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
Avg Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
========================================
`,
    'scripts/load_test/k6_results.json': JSON.stringify(data),
  };
}

