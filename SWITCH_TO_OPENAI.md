# Switching to OpenAI API (No Memory Issues!)

## Why Switch?

- ✅ **No Memory Issues** - No local model loading (no 512MB limit)
- ✅ **More Reliable** - No service crashes or memory errors
- ✅ **Faster** - Better response times
- ✅ **No Deployment** - No need for separate Ollama service
- ✅ **Better Rate Limits** - More requests allowed

**Cost:** ~$0.10-0.50 per 1000 questions (very affordable)

---

## How to Switch

### Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-`)

### Step 2: Update Backend Environment Variables

**In Render Dashboard → Backend Service → Environment:**

**Option A: Replace Ollama with OpenAI (Recommended)**

Remove/Update these:
```
# Remove or comment out Ollama settings:
# LLM_BASE_URL=https://rag-chatbot-back.onrender.com
# LLM_DEFAULT_MODEL=llama3.2:3b

# Add OpenAI settings:
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-openai-api-key-here
LLM_DEFAULT_MODEL=gpt-3.5-turbo
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_TEMPERATURE=0.1
LLM_DEFAULT_MAX_TOKENS=2000
```

**Option B: Use OpenAI but keep Ollama URL structure**

The code auto-detects OpenAI when you provide an API key:
```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-openai-api-key-here
LLM_DEFAULT_MODEL=gpt-3.5-turbo
LLM_DEFAULT_PROVIDER=openai
```

### Step 3: Redeploy Backend

After updating environment variables:
1. Render will automatically redeploy
2. Or click **"Manual Deploy"** → **"Deploy latest commit"**

### Step 4: Test

```bash
curl -X POST https://rag-chatbot-backend-szgj.onrender.com/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AI?", "context_limit": 3}'
```

Should work without memory errors!

---

## Available Models

You can use any OpenAI model:

- `gpt-3.5-turbo` - Fast and cheap (~$0.0015/1K tokens)
- `gpt-4` - Better quality (~$0.03/1K tokens)
- `gpt-4-turbo` - Latest and best (~$0.01/1K tokens)
- `gpt-4o-mini` - Fast and affordable (~$0.15/1M tokens input)

Just update `LLM_DEFAULT_MODEL` in environment variables.

---

## Cost Estimate

**Example:** 1000 questions × 1000 tokens each = 1M tokens

- **gpt-3.5-turbo:** ~$2 ($0.002/1K tokens)
- **gpt-4-turbo:** ~$10 ($0.01/1K tokens)
- **gpt-4o-mini:** ~$0.30 ($0.30/1M tokens)

**Very affordable for most use cases!**

---

## What Happens to Ollama?

- You can **keep Ollama service** running (it won't be used)
- Or **delete it** to save resources
- You can **switch back anytime** by changing env vars

---

## Troubleshooting

**Error: "OpenAI API error: Invalid API key"**
- Check your API key is correct
- Make sure it starts with `sk-`
- Verify key has credits in your OpenAI account

**Error: "OpenAI API error: Rate limit exceeded"**
- Wait a few seconds and retry
- Check your OpenAI account limits
- Consider upgrading OpenAI plan

**Still using Ollama?**
- Check `LLM_DEFAULT_PROVIDER` is set to `openai`
- Verify `LLM_API_KEY` is set correctly
- Check logs to see which provider is being used

---

## Benefits Summary

✅ No memory crashes (no local model)
✅ More reliable (99.9% uptime)
✅ Faster responses
✅ No separate Ollama service needed
✅ Better error handling
✅ Auto-detection (just set API key)

**You're all set!** 🎉

