# Render Deployment Guide

## Generated Secrets (Save these securely!)

- **SECRET_KEY**: `1fGValreU6KyIDH9K7NhjBVThSw-e93hkd9nSIT_Rvg`
- **API_KEY**: `qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg`
- **SENDGRID_API_KEY**: (Already in your .env file)

## Deployment Steps

### Option 1: Using Render MCP (if configured in Cursor)

If you have Render MCP set up in Cursor, you can:

1. **Deploy via Blueprint**:
   - Use the MCP interface to deploy from `render.yaml`
   - Render will automatically create all services from the blueprint

2. **Set Environment Variables**:
   After services are created, set these environment variables in each service:
   - `SENDGRID_API_KEY` - Your SendGrid API key
   - `ADMIN_EMAIL` - Your email address
   - `SECRET_KEY` - `1fGValreU6KyIDH9K7NhjBVThSw-e93hkd9nSIT_Rvg`
   - `API_KEY` - `qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg`

### Option 2: Using Render Dashboard

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Create Blueprint**: 
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository: `eweinhaus/TutorScoring`
   - Render will detect `render.yaml` and create all services

3. **Services Created**:
   - `tutor-scoring-db` (PostgreSQL database)
   - `tutor-scoring-redis` (Redis instance)
   - `tutor-scoring-api` (Backend API web service)
   - `tutor-scoring-worker` (Celery worker service)
   - `tutor-scoring-frontend` (Frontend static site)

4. **Configure Environment Variables**:
   For each service (API and Worker), add:
   - `SENDGRID_API_KEY` - Your SendGrid API key
   - `ADMIN_EMAIL` - Your email address  
   - `SECRET_KEY` - `1fGValreU6KyIDH9K7NhjBVThSw-e93hkd9nSIT_Rvg`
   - `API_KEY` - `qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg`

5. **Run Database Migrations**:
   - Wait for backend API to deploy
   - Go to backend API service → Shell
   - Run: `cd backend && alembic upgrade head`

6. **Update Frontend API URL** (After backend deploys):
   - Note the backend URL (e.g., `https://tutor-scoring-api.onrender.com`)
   - Update frontend service environment variable:
     - `VITE_API_URL` = `https://tutor-scoring-api.onrender.com`
     - `VITE_API_KEY` = `qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg`

7. **Optional: Seed Test Data**:
   - Go to backend API service → Shell
   - Run: `cd backend && python scripts/generate_data.py`

## Service URLs

After deployment, you'll have:
- **Backend API**: `https://tutor-scoring-api.onrender.com`
- **Frontend**: `https://tutor-scoring-frontend.onrender.com`
- **Health Check**: `https://tutor-scoring-api.onrender.com/api/health`

## Verification Steps

1. **Check Backend Health**:
   ```bash
   curl https://tutor-scoring-api.onrender.com/api/health
   ```

2. **Test API Endpoint**:
   ```bash
   curl https://tutor-scoring-api.onrender.com/api/tutors
   ```

3. **Visit Frontend**:
   - Open `https://tutor-scoring-frontend.onrender.com` in browser
   - Verify dashboard loads

## Troubleshooting

### Services Not Starting
- Check service logs in Render dashboard
- Verify environment variables are set correctly
- Ensure database migrations ran successfully

### Frontend Can't Connect to Backend
- Verify `VITE_API_URL` is set to correct backend URL
- Check backend is running and healthy
- Verify CORS is configured correctly

### Database Connection Issues
- Verify `DATABASE_URL` is automatically set from database service
- Check database is running and accessible

### Worker Not Processing Tasks
- Verify Redis connection strings are correct
- Check worker service is running
- View worker logs for errors

## Next Steps After Deployment

1. ✅ Verify all services are running
2. ✅ Test API endpoints
3. ✅ Test frontend dashboard
4. ✅ Run load tests (Phase 3)
5. ✅ Document performance results

