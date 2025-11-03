# Worker Troubleshooting Guide

## Problem: Generation stuck at "PENDING" for 10+ minutes

This typically means the **ARQ worker is not running** or cannot pick up jobs from Redis.

## ✅ What I've Added

1. **Comprehensive Logging** - Every step now logs:
   - `[GENERATION INIT]` - When job is enqueued from API
   - `[WORKER]` - All worker steps with timing
   - Step-by-step progress with durations
   - Error details with full tracebacks

2. **Diagnostic Script** - `check_worker.py` to verify setup

## 🔍 Step-by-Step Debugging

### 1. Check if Worker is Running

```bash
# Check for running worker process
ps aux | grep run_worker
# OR
pgrep -f "run_worker"
```

**Expected**: You should see a Python process running `run_worker.py`

**If not running**: Start it:
```bash
cd backend
python run_worker.py
```

You should see:
```
================================================================================
🔧 ARQ WORKER STARTING UP...
Redis Settings: host=localhost, port=6379, db=0
Registered Functions: ['process_repository_analysis', 'generate_tutorial']
Max Jobs: 10
Job Timeout: 3600s
================================================================================
```

### 2. Verify Redis Connection & Queue Status

```bash
cd backend
python check_worker.py
```

This will show:
- Redis connection status
- Number of pending/in-progress/completed jobs
- Registered worker functions

### 3. Check API Logs

When you initiate generation, look for these logs in your **FastAPI server terminal**:

```
[GENERATION INIT] Starting job enqueue for generation_id: <uuid>
[GENERATION INIT] Redis pool found, enqueueing job...
[GENERATION INIT] ✅ Job enqueued successfully! Job ID: <job_id>
```

### 4. Check Worker Logs

In your **worker terminal**, you should immediately see:

```
================================================================================
[WORKER] ========== TUTORIAL GENERATION WORKER STARTED ==========
[WORKER] Received job_data: {...}
[WORKER] Parsed parameters:
[WORKER]   - generation_id: <uuid>
[WORKER]   - repo_id: <uuid>
...
```

## 🚨 Common Issues

### Issue 1: Worker Not Running

**Symptoms**: Job stays in PENDING, no logs in worker terminal

**Solution**:
```bash
cd backend
python run_worker.py
```

Keep this terminal open - it shows all worker activity.

### Issue 2: Redis Not Running

**Symptoms**: `check_worker.py` fails or API shows "Redis pool not initialized"

**Solution**:
```bash
# Start Redis (Mac with Homebrew)
brew services start redis

# Start Redis (Docker)
docker run -d -p 6379:6379 redis

# Check Redis
redis-cli ping
# Should return: PONG
```

### Issue 3: Function Name Mismatch

**Symptoms**: Worker logs show "Function not found"

**Check**: Function name in `enqueue_job()` must match the actual function name:
- API uses: `'generate_tutorial'` (string)
- Worker registers: `generate_tutorial` (function)
- ✅ These match!

### Issue 4: Worker Crashes Immediately

**Symptoms**: Worker starts then exits

**Check**: Look at the full error in worker terminal. Common causes:
- Database connection issues
- Missing environment variables
- Import errors

## 📊 Understanding the Logs

### API Logs (when you click "Generate")
```
[GENERATION INIT] Starting job enqueue...
[GENERATION INIT] ✅ Job enqueued successfully!
```

### Worker Logs (every step)
```
[WORKER] ========== STEP 1: CLONING REPOSITORY ==========
[WORKER] Cloning https://github.com/... to /tmp/reploai/<uuid>...
[WORKER] ✅ Repository cloned successfully in 5.23 seconds

[WORKER] ========== STEP 2: ANALYZING CODE STRUCTURE ==========
[WORKER] Starting tree-sitter analysis...
[WORKER] ✅ Code structure analysis completed in 3.45 seconds
```

### Timing Information
Every major step shows:
- Start time
- Duration
- Success/failure status

## 🔧 Quick Fix Commands

```bash
# 1. Stop any existing worker
pkill -f run_worker

# 2. Verify Redis is running
redis-cli ping

# 3. Check worker setup
cd backend && python check_worker.py

# 4. Start worker (in one terminal)
cd backend && python run_worker.py

# 5. Start API (in another terminal)
cd backend && python run.py
```

## 📝 Monitoring Generation Progress

### From Database
```sql
SELECT 
    generation_id, 
    status, 
    generation_step, 
    generation_progress, 
    error_message,
    created_at,
    updated_at
FROM tutorial_generations
ORDER BY created_at DESC
LIMIT 5;
```

### Status Values
- `PENDING` - Job enqueued, waiting for worker
- `CLONING` - Step 1 (10%) - Cloning repository
- `ANALYZING` - Step 2 (30%) - Code structure analysis
- `PROCESSING` - Step 3 (50%) - Code summarization
- `GENERATING` - Step 4 (65-100%) - AI generation
- `COMPLETED` - Success!
- `FAILED` - Error occurred (check `error_message`)

## 🎯 Next Steps After Fix

Once worker is running:
1. Initiate a new generation
2. Watch worker terminal for real-time logs
3. Check progress in database or frontend
4. Each step will log its duration

## ⚠️ Important Notes

1. **Worker Must Stay Running**: The worker process must remain active. Don't close its terminal.

2. **Separate Processes**: API and Worker run separately:
   - API: `python run.py` (handles HTTP requests)
   - Worker: `python run_worker.py` (processes background jobs)

3. **Redis is Shared**: Both API and Worker connect to the same Redis instance.

4. **One Worker is Enough**: Multiple workers can run, but one is sufficient for testing.

