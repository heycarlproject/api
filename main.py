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

class ChatRequest(BaseModel):
    userId: str
    plan: str
    message: str

@app.post("/ask-carl")
async def ask_carl(data: ChatRequest):
    plan = data.plan
    user_id = data.userId
    message = data.message

    if user_id not in user_usage:
        user_usage[user_id] = 0

    settings = PLAN_SETTINGS.get(plan, PLAN_SETTINGS["lm_free"])
    if user_usage[user_id] >= settings["max_messages"]:
        return {"response": "🚫 You've hit your message limit for this plan."}

    time.sleep(settings["delay"])
    user_usage[user_id] += 1

    api_key = os.getenv("OPENROUTER_API_KEY", "")
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
            ai_reply = "⚠️ Carl is having trouble thinking right now."

    return {"response": ai_reply}
