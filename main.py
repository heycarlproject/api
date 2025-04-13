from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import time

app = FastAPI()

PLAN_SETTINGS = {
    "lm_free": {"max_messages": 50, "delay": 2.5},
    "standard": {"max_messages": 500, "delay": 1.0},
    "mid_tier": {"max_messages": 2000, "delay": 0.5},
    "pro": {"max_messages": float('inf'), "delay": 0.0},
    "mu_business": {"max_messages": float('inf'), "delay": 0.0}
}

user_usage = {}
active_requests = 0
MAX_CONCURRENT_REQUESTS = 10

class ChatRequest(BaseModel):
    userId: str
    plan: str
    message: str

@app.post("/ask-carl")
async def ask_carl(data: ChatRequest):
    global active_requests
    if active_requests >= MAX_CONCURRENT_REQUESTS:
        return {"response": "🚫 Sorry, all of our servers are in use right now. Please try again later."}

    active_requests += 1
    try:
        plan = data.plan
        user_id = data.userId
        message = data.message

        if user_id not in user_usage:
            user_usage[user_id] = 0

        settings = PLAN_SETTINGS.get(plan, PLAN_SETTINGS["lm_free"])
        if user_usage[user_id] >= settings["max_messages"]:
            return {"response": "❌ You've hit your message limit. Upgrade to keep chatting!"}

        time.sleep(settings["delay"])
        user_usage[user_id] += 1

        api_key = os.getenv("OPENROUTER_API_KEY", "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")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral/mistral-7b-instruct",
                    "messages": [
                        {"role": "system", "content": "You are Carl, a helpful assistant."},
                        {"role": "user", "content": message}
                    ]
                }
            )
            try:
                result = response.json()
                ai_reply = result['choices'][0]['message']['content']
            except:
                ai_reply = "⚠️ Carl had an issue reaching the AI brain."

        return {"response": ai_reply}
    finally:
        active_requests -= 1