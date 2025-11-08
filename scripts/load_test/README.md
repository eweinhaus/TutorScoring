# Load Testing Scripts

This directory contains scripts for load testing the Tutor Quality Scoring System.

## Scripts

### `k6_session_load.js`
K6 load test script for simulating 3,000 daily sessions.

**Usage:**
```bash
# Real-time simulation (24 hours, ~125 sessions/hour)
k6 run scripts/load_test/k6_session_load.js \
  --env API_URL=http://localhost:8001 \
  --env API_KEY=your-api-key

# Compressed simulation (1 hour, 3,000 sessions)
k6 run scripts/load_test/k6_session_load.js \
  --env API_URL=http://localhost:8001 \
  --env API_KEY=your-api-key \
  --env COMPRESSED=true
```

**Prerequisites:**
- K6 installed: `brew install k6`
- Valid tutor IDs in database (update SAMPLE_TUTOR_IDS in script or use `get_tutor_ids.py`)

### `get_tutor_ids.py`
Fetches valid tutor IDs from the database for use in load tests.

**Usage:**
```bash
python scripts/load_test/get_tutor_ids.py --output tutor_ids.json
```

### `track_processing.py`
Tracks session processing performance and validates 1-hour SLA.

**Usage:**
```bash
python scripts/load_test/track_processing.py \
  --start-time "2024-01-01 00:00:00" \
  --output processing_report.json
```

### `monitor_resources.py`
Monitors system resources during load testing (queue depth, CPU, memory, DB connections).

**Usage:**
```bash
python scripts/load_test/monitor_resources.py \
  --interval 60 \
  --duration 3600 \
  --output monitoring.csv
```

## Quick Start

1. **Get tutor IDs:**
   ```bash
   python scripts/load_test/get_tutor_ids.py
   ```
   Update `k6_session_load.js` with the tutor IDs.

2. **Start monitoring (in separate terminal):**
   ```bash
   python scripts/load_test/monitor_resources.py --duration 3600
   ```

3. **Run load test:**
   ```bash
   k6 run scripts/load_test/k6_session_load.js \
     --env API_URL=http://localhost:8001 \
     --env API_KEY=your-api-key \
     --env COMPRESSED=true
   ```

4. **Track processing:**
   ```bash
   python scripts/load_test/track_processing.py \
     --start-time "2024-01-01 00:00:00"
   ```

## Notes

- Make sure backend API and Celery worker are running before starting tests
- For compressed tests, validate SLA separately (tests capacity, not real-time processing)
- Monitor queue depth - should stay <100 during test
- Check worker logs for any processing errors


