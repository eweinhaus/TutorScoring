# Load Testing Setup Instructions

## Prerequisites

1. **Install K6:**
   ```bash
   brew install k6
   # Verify: k6 version
   ```

2. **Install Python dependencies:**
   ```bash
   cd backend
   source venv/bin/activate
   pip install psutil requests
   ```

3. **Ensure services are running:**
   - Backend API: `uvicorn app.main:app --host 0.0.0.0 --port 8001`
   - Celery Worker: `celery -A app.tasks.celery_app worker --loglevel=info`
   - PostgreSQL: Running on port 5432
   - Redis: Running on port 6379

4. **Get API Key:**
   - Check `backend/.env` for `API_KEY` value
   - Or set it as environment variable

5. **Get Tutor IDs:**
   ```bash
   python scripts/load_test/get_tutor_ids.py --limit 100
   ```
   - This creates `tutor_ids.json`
   - Update `k6_session_load.js` with tutor IDs from the output

## Quick Test (Small Scale)

Before running the full 3,000 session test, run a small test:

```bash
# Update k6_session_load.js with tutor IDs first
# Then run a quick 10-session test:
k6 run scripts/load_test/k6_session_load.js \
  --env API_URL=http://localhost:8001 \
  --env API_KEY=your-api-key \
  --env COMPRESSED=true \
  --vus 1 \
  --iterations 10
```

## Full Load Test

### Option 1: Compressed Test (Recommended for quick validation)
```bash
# 3,000 sessions in 1 hour
k6 run scripts/load_test/k6_session_load.js \
  --env API_URL=http://localhost:8001 \
  --env API_KEY=your-api-key \
  --env COMPRESSED=true
```

### Option 2: Real-Time Test (Most accurate, takes 24 hours)
```bash
# 3,000 sessions over 24 hours (~125/hour)
k6 run scripts/load_test/k6_session_load.js \
  --env API_URL=http://localhost:8001 \
  --env API_KEY=your-api-key
```

## Monitoring During Test

In a separate terminal, run:
```bash
python scripts/load_test/monitor_resources.py \
  --interval 60 \
  --duration 3600 \
  --output monitoring.csv
```

## Tracking Processing After Test

After the load test completes, track processing:
```bash
python scripts/load_test/track_processing.py \
  --start-time "2024-01-01 00:00:00" \
  --output processing_report.json
```

Replace the start-time with when your test actually started.

## Troubleshooting

1. **401 Unauthorized errors:**
   - Check API_KEY is correct
   - Verify API key is set in backend/.env

2. **400 Bad Request errors:**
   - Check tutor IDs are valid UUIDs
   - Verify tutor IDs exist in database
   - Run `get_tutor_ids.py` to get valid IDs

3. **Connection errors:**
   - Verify API is running on correct port
   - Check firewall settings

4. **Queue depth growing:**
   - Check Celery worker is running
   - Monitor worker CPU/memory
   - May need to scale workers

