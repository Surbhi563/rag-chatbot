# Fixing Memory Issues on Render Free Tier

## Problem

Ollama service is running out of memory (512MB limit on Render free tier).

**Error:** "Ran out of memory (used over 512MB)"

## Why This Happens

- **Model Size:** `llama3.2:3b` is ~2GB when loaded
- **Inference Memory:** Running inference needs additional RAM
- **Free Tier Limit:** Render free tier = 512MB RAM
- **Total Need:** Model + inference ≈ 2-3GB (way over limit)

## Solutions

### Option 1: Use Smaller Model (Recommended for Free Tier)

Use a smaller quantized model that fits in 512MB:

**Change in Render Dashboard → Ollama Service → Environment:**
```
# Use a smaller model variant
# Options:
# - llama3.2:1b (if available) - much smaller
# - tinyllama (if available) - very small
# - gemma:2b (might fit better)
```

Or modify Dockerfile to pull smaller model.

### Option 2: Upgrade Render Service ⭐ (Best Solution)

**Upgrade to Starter Plan** ($7/month):
- **512MB → 2GB RAM** (enough for model + inference)
- Always-on service (no spin-down)
- More reliable

**How to Upgrade:**
1. Render Dashboard → Ollama Service
2. Settings → Plan
3. Upgrade to Starter ($7/month)

### Option 3: Switch to OpenAI API (No Memory Issues)

- No local memory needed
- Pay per use (~$0.10 per 1000 questions)
- More reliable
- Requires code changes to support OpenAI

### Option 4: Use Lighter Weight Setup

If available, try smaller models:
- Use model variants with higher quantization (smaller size)
- Reduce max_tokens to lower memory per request

## Immediate Workaround

**Reduce concurrent requests:**
- Only one user at a time
- Wait 30+ seconds between requests
- This won't fix OOM but reduces crashes

## Recommendation

**For Production:** 
- **Option 2** (Upgrade to Starter) - Best balance of cost and reliability
- **Option 3** (OpenAI API) - Most reliable, pay-as-you-go

**For Testing/Development:**
- **Option 1** (Smaller model) - If available
- Accept occasional OOM errors on free tier

## What to Do Now

1. **Upgrade Ollama service** to Starter plan ($7/month)
   - Gives you 2GB RAM (enough for the model)
   - Solves memory issues

2. **OR switch to OpenAI API**
   - I can add OpenAI support to the code
   - No memory issues
   - More reliable

3. **OR accept limitations:**
   - Free tier will keep crashing
   - Service will restart automatically
   - May need to wait after crashes

## Cost Comparison

- **Render Starter:** $7/month (fixed cost)
- **OpenAI API:** ~$0.10-0.50 per 1000 questions (usage-based)
- **Free Tier:** Free but unreliable (memory limits)

For low-to-medium usage, OpenAI API is likely cheaper and more reliable.

## Next Steps

Would you like me to:
1. **Add OpenAI API support** so you can switch easily?
2. **Optimize for smaller memory** (if smaller models available)?
3. **Help upgrade the service** on Render?

The choice depends on your usage and budget!

