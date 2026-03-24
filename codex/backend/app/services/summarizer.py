import re
from collections import Counter

import httpx

from app.core.config import get_settings


def _build_mock_summary(text: str) -> tuple[str, list[str]]:
    normalized = " ".join(text.split())
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", normalized) if segment.strip()]
    if not sentences:
        summary = normalized[:240]
    else:
        summary = " ".join(sentences[:2])[:320]

    words = re.findall(r"[A-Za-z가-힣]{3,}", normalized.lower())
    tags = [word for word, _ in Counter(words).most_common(5)]
    return summary, tags


def summarize_text(title: str, raw_content: str) -> tuple[str, list[str]]:
    settings = get_settings()
    provider = settings.summary_provider.lower()
    if provider == "openai" and settings.openai_api_key:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        prompt = f"Summarize the following article in Korean. Title: {title}\n\n{raw_content}"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You summarize AI articles into concise Korean highlights and keyword tags."},
                {"role": "user", "content": prompt},
            ],
        }
        response = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]["content"]
        summary, tags = _build_mock_summary(message)
        return summary, tags

    return _build_mock_summary(f"{title}. {raw_content}")

