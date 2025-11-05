# Deploy to Render Now - Quick Guide

## 🚀 Fastest Deployment Method: Render Dashboard Blueprint

Since Render MCP requires workspace selection, let's use the Render Dashboard which is actually simpler and more reliable.

### Step 1: Deploy via Blueprint (2 minutes)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** (top right)
3. **Select "Blueprint"**
4. **Connect your GitHub repository**:
   - Repository: `eweinhaus/TutorScoring`
   - Branch: `main`
   - Render will auto-detect `render.yaml`
5. **Click "Apply"** - Render will create all 5 services automatically:
   - ✅ PostgreSQL Database (`tutor-scoring-db`)
   - ✅ Redis Instance (`tutor-scoring-redis`)
   - ✅ Backend API (`tutor-scoring-api`)
   - ✅ Celery Worker (`tutor-scoring-worker`)
   - ✅ Frontend Static Site (`tutor-scoring-frontend`)

### Step 2: Wait for Services to Build (5-10 minutes)

Monitor the build logs in Render dashboard. Services will deploy in this order:
1. Database (fastest)
2. Redis (fast)
3. Backend API (builds Python dependencies)
4. Worker (builds Python dependencies)
5. Frontend (builds Node.js dependencies)

### Step 3: Configure Environment Variables

After services are created, add these environment variables to **Backend API** and **Worker** services:

1. Go to each service → **Environment** tab
2. Add these variables:
   - `SENDGRID_API_KEY` = (your SendGrid API key from .env)
   - `ADMIN_EMAIL` = (your email address)
   - `SECRET_KEY` = `1fGValreU6KyIDH9K7NhjBVThSw-e93hkd9nSIT_Rvg`
   - `API_KEY` = `qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg`

**Note**: Database and Redis connection strings are automatically set by Render.

### Step 4: Run Database Migrations

1. Wait for Backend API to finish deploying (green status)
2. Go to Backend API service → **Shell** tab
3. Run:
   ```bash
   cd backend && alembic upgrade head
   ```

### Step 5: Update Frontend API URL

1. Note the Backend API URL (e.g., `https://tutor-scoring-api.onrender.com`)
2. Go to Frontend service → **Environment** tab
3. Update `VITE_API_URL` to your backend URL
4. Add `VITE_API_KEY` = `qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg`
5. Redeploy frontend (or it will auto-redeploy)

### Step 6: Optional - Seed Test Data

1. Go to Backend API service → **Shell**
2. Run:
   ```bash
   cd backend && python scripts/generate_data.py
   ```

### Step 7: Verify Deployment

1. **Backend Health Check**: 
   ```
   https://tutor-scoring-api.onrender.com/api/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Frontend Dashboard**:
   ```
   https://tutor-scoring-frontend.onrender.com
   ```
   Should load the dashboard

3. **Test API**:
   ```bash
   curl https://tutor-scoring-api.onrender.com/api/tutors
   ```

## 🎯 Expected Results

After deployment, you'll have:
- ✅ Backend API running on Render
- ✅ Celery worker processing tasks
- ✅ PostgreSQL database with schema
- ✅ Redis for queue and cache
- ✅ Frontend dashboard accessible via URL

## ⚠️ Important Notes

- **Free Tier**: Services spin down after 15 minutes of inactivity (first request may be slow)
- **Environment Variables**: Must be set before services can fully function
- **Migrations**: Must run before database can be used
- **Frontend URL**: Update after backend deploys to get the correct URL

## 🐛 Troubleshooting

### Services Not Starting
- Check service logs in Render dashboard
- Verify all environment variables are set
- Check build logs for errors

### Database Connection Errors
- Verify migrations ran successfully
- Check DATABASE_URL is set correctly (auto-set by Render)

### Frontend Can't Connect
- Verify VITE_API_URL is correct
- Check backend is running and healthy
- Verify CORS is configured

---

**Ready to deploy?** Go to https://dashboard.render.com and click "New +" → "Blueprint"!

