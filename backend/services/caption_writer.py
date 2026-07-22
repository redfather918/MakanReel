"""新加坡本地化 IG Caption 生成引擎。

对应 TRD 3.3 文案部分。
优先调用 OpenAI 兼容 LLM；无密钥或失败时走模板兜底，保证可用。
"""
from __future__ import annotations
import json
import httpx

import config

DEFAULT_HASHTAGS = ["#SGFoodie", "#SGBubbleTea", "#SingaporeEats", "#SGDeals", "#SGDrinks"]

LOCAL_FLAVORS = ["Shiok!", "So refreshing!", "Mai tu liao!", "Confirm shiok!", "Power!", "Steady pom pi pi!"]


def _build_prompt(note: str, style_prompt: str) -> str:
    return (
        "You are a social media copywriter for a Singapore F&B brand (bubble tea / drinks, 180+ outlets).\n"
        "Write ONE Instagram Reels caption in English with a Singaporean local vibe.\n"
        f"Product / promo note: {note or 'a delicious drink'}\n"
        f"Visual style: {style_prompt or 'cool and refreshing'}\n"
        "Requirements:\n"
        "- 2-3 short punchy lines, use 1-2 local phrases (e.g. Shiok!, refreshing, confirm shiok).\n"
        "- End with a call to action.\n"
        "- Return STRICT JSON: {\"caption\": \"...\", \"hashtags\": [\"#SGFoodie\", ...]}\n"
        "- Include 5 relevant hashtags starting with #SG or #Singapore.\n"
        "- No markdown, no explanation, only the JSON object."
    )


def _template_caption(note: str, style_prompt: str) -> tuple[str, list[str]]:
    """模板兜底：组合本地语气词 + 备注 + Hashtag。"""
    base = note.strip() if note else "our signature drink"
    flavor = LOCAL_FLAVORS[hash(note) % len(LOCAL_FLAVORS)]
    caption = (
        f"{flavor} {base.capitalize()} is here! \U0001F929\n"
        f"Crisp, cold and oh-so-refreshing \u2014 the perfect pick-me-up for Singapore's heat. \u2600\ufe0f\n"
        f"Grab yours today at your nearest outlet. Confirm won't regret! \U0001F44D"
    )
    return caption, DEFAULT_HASHTAGS


def generate_caption(note: str, style_prompt: str) -> tuple[str, list[str]]:
    """生成 Caption + Hashtag。优先 LLM，失败兜底。"""
    if not config.LLM_API_KEY:
        print("[caption] 无 API 密钥，使用模板兜底")
        return _template_caption(note, style_prompt)

    prompt = _build_prompt(note, style_prompt)
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{config.LLM_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                json={
                    "model": config.LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 400,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # 提取 JSON
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("LLM 返回非 JSON")
            data = json.loads(content[start:end + 1])
            caption = data.get("caption", "").strip()
            hashtags = data.get("hashtags", DEFAULT_HASHTAGS)
            if not caption:
                raise ValueError("空 caption")
            print("[caption] LLM 生成成功")
            return caption, hashtags
    except Exception as e:
        print(f"[caption] LLM 失败，兜底: {e}")
        return _template_caption(note, style_prompt)
