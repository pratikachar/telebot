import base64
import json

import httpx

from config import CEREBRAS_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, ZAI_API_KEY

PROVIDERS = [
    {
        "name": "Gemini",
        "api_key": GEMINI_API_KEY,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ],
        "vision": True,
    },
    {
        "name": "Groq",
        "api_key": GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "moonshotai/kimi-k2-instruct",
        ],
        "vision_models": ["meta-llama/llama-4-scout-17b-16e-instruct"],
    },
    {
        "name": "Cerebras",
        "api_key": CEREBRAS_API_KEY,
        "base_url": "https://api.cerebras.ai/v1",
        "models": ["gpt-oss-120b", "gemma-4-31b"],
        "vision_models": ["gemma-4-31b"],
    },
    {
        "name": "GLM",
        "api_key": ZAI_API_KEY,
        "base_url": "https://api.z.ai/api/paas/v4",
        "models": ["glm-4.7-flash", "glm-4.5-flash"],
        "vision_models": ["glm-4.6v-flash"],
    },
]


async def _call(base_url, api_key, model, messages):
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 2048,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _with_image(messages, image_bytes):
    msgs = json.loads(json.dumps(messages))
    msgs[-1] = dict(msgs[-1])
    b64 = base64.b64encode(image_bytes).decode("ascii")
    msgs[-1]["content"] = [
        {"type": "text", "text": str(msgs[-1].get("content", ""))},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]
    return msgs


async def chat(messages, image_bytes=None, attempts: int = 2):
    """Try each configured provider in cascade order, up to `attempts` full passes.
    NEVER raises - returns (text, provider_label) or (None, None) if every attempt failed."""
    for _ in range(max(1, attempts)):
        for provider in PROVIDERS:
            try:
                if not provider.get("api_key"):
                    continue
                if image_bytes and provider.get("vision"):
                    models = provider["models"]
                elif image_bytes:
                    models = provider.get("vision_models") or []
                else:
                    models = provider["models"]
                for model in models:
                    try:
                        payload = _with_image(messages, image_bytes) if image_bytes else messages
                        text = await _call(provider["base_url"], provider["api_key"], model, payload)
                        if text and str(text).strip():
                            return text, f"{provider['name']} ({model})"
                    except Exception:
                        continue
            except Exception:
                continue
    return None, None


def configured_providers():
    names = []
    for p in PROVIDERS:
        if p["api_key"]:
            names.append(p["name"])
    return names or ["none"]
