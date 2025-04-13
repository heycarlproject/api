from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import time

app = FastAPI()

# Define subscription tiers and limits
PLAN_SETTINGS = {
    "lm_free": {"max_messages": 50, "delay": 2.5},
    "standard": {"max_messages": 500, "delay": 1.0},
    "mid_tier": {"max_messages": 2000, "delay": 0.5},
    "pro": {"max_messages": float('inf'), "delay": 0.0},
    "mu_business": {"max_messages": float('inf'), "delay": 0.0}
}

# Simulated in-memory user data
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

    # Initialize user if not in memory
    if user_id not in user_usage:
        user_usage[user_id] = 0

    # Check plan limits
    settings = PLAN_SETTINGS.get(plan, PLAN_SETTINGS["lm_free"])
    if user_usage[user_id] >= settings["max_messages"]:
        return {"response": "🚫 You've hit your message limit for this plan. Upgrade to keep chatting!"}

    # Delay for lower tiers (simulate slower response)
    time.sleep(settings["delay"])

    # Update usage
    user_usage[user_id] += 1

    # Call real AI (OpenRouter)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer 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",  # Replace with your OpenRouter key
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
            ai_reply = "⚠️ Carl is having trouble thinking right now. Try again later."

    return {"response": ai_reply}
