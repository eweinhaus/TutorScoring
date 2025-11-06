# Quick Fix for Loading Issues

## Problem
Frontend is trying to connect to port 8001, but backend is on port 8000.

## Solution Applied
1. ✅ Updated `vite.config.js` - proxy now points to port 8000
2. ✅ Updated `api.js` - uses relative URLs (goes through Vite proxy)
3. ✅ Updated `matchingApi.js` - uses relative URLs

## Steps to Fix

### 1. Restart Frontend Dev Server
The Vite dev server needs to be restarted to pick up the vite.config.js changes:

```bash
# Stop the current frontend (Ctrl+C in the terminal running it)
# Then restart:
cd frontend
npm run dev
```

### 2. Hard Refresh Browser
- **Mac**: Cmd + Shift + R
- **Windows/Linux**: Ctrl + Shift + R
- Or open DevTools → Network tab → Check "Disable cache"

### 3. Verify Proxy is Working
Open browser console and check:
- Requests should go to `/api/tutors` (relative URL)
- Not `http://localhost:8001/api/tutors`

### 4. Check Browser Console
Look for:
- CORS errors (should be gone now)
- 404 errors (check if proxy is working)
- Network tab to see actual request URLs

## Verification

Test the proxy directly:
```bash
curl http://localhost:3000/api/health
```

Should return: `{"status":"healthy",...}`

## If Still Not Working

1. **Check Vite is using the new config:**
   - Look at the terminal where `npm run dev` is running
   - Should see "VITE v5.x.x" and no errors

2. **Clear browser cache completely:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Or use Incognito/Private window

3. **Check for multiple backend instances:**
   ```bash
   lsof -ti:8000
   ```
   If multiple PIDs, kill duplicates:
   ```bash
   pkill -f "uvicorn.*TutorScoring"
   ```

4. **Restart both services:**
   ```bash
   # Backend
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Frontend (new terminal)
   cd frontend
   npm run dev
   ```
