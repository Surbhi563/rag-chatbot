# Fix: Railway distutils ModuleNotFoundError

## Problem

Railway/Nixpacks is using Python 3.12+ which removed `distutils` module. Some packages still depend on it during installation.

## Solution Applied

I've added multiple fixes to ensure Python 3.11 is used and setuptools (which provides distutils) is available:

### 1. Added `setuptools` to requirements.txt ✅
- `setuptools>=65.0.0` now included
- Provides `distutils` compatibility

### 2. Created `.python-version` ✅
- Specifies Python 3.11.0
- Railway/Nixpacks should detect this

### 3. Created `runtime.txt` ✅
- Heroku-style Python version specification
- Alternative method for Railway to detect version

### 4. Created `nixpacks.toml` ✅
- Explicitly sets Python 3.11
- Upgrades pip/setuptools during install phase

### 5. Updated `railway.json` ✅
- References nixpacks.toml (if supported)

## If Still Not Working

### Option A: Use Dockerfile Instead

Railway can use Docker instead of Nixpacks:

1. Update `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. Railway will use `backend/Dockerfile` which already uses Python 3.11

### Option B: Set Environment Variable in Railway

In Railway dashboard:
- Add environment variable: `PYTHON_VERSION=3.11`

### Option C: Use Better requirements.txt Path

Make sure Railway is using `backend/requirements.txt` instead of root `requirements.txt`:
- In Railway service settings, set **Root Directory** to `backend`

## Files Changed

✅ `requirements.txt` - Added setuptools
✅ `.python-version` - Python 3.11.0
✅ `runtime.txt` - Python 3.11.0  
✅ `nixpacks.toml` - Python 3.11 config
✅ `railway.json` - References nixpacks config

## Next Steps

1. **Commit and push** these changes
2. **Redeploy** on Railway
3. If still failing, **switch to Dockerfile** (Option A above)

The build should now work! 🎉

