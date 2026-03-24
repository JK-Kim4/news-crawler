import json
import logging
import re
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = (
    "다음 기술 문서의 핵심 내용을 3-5문장으로 한국어로 요약해주세요. "
    "주요 키워드 태그도 5개 이내로 추출해주세요.\n\n"
    "반드시 아래 JSON 형식으로만 응답해주세요:\n"
    '{"summary": "요약 텍스트", "tags": ["태그1", "태그2"]}\n\n'
    "문서 내용:\n"
)


def mock_summarize(title: str, content: str) -> dict[str, Any]:
    words = title.split()
    tags = [w.strip(".:,;!?") for w in words if len(w) > 2][:5]
    summary = f"이 문서는 '{title}'에 대한 내용을 다루고 있습니다. "
    if content:
        preview = content[:200].replace("\n", " ").strip()
        summary += f"주요 내용: {preview}..."
    else:
        summary += "상세 내용은 원문을 참조해주세요."
    return {"summary": summary, "tags": tags}


async def anthropic_summarize(title: str, content: str) -> dict[str, Any]:
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, falling back to mock summarizer")
        return mock_summarize(title, content)

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        truncated_content = content[:8000] if content else title

        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"{SUMMARIZE_PROMPT}{truncated_content}",
                }
            ],
        )

        response_text = message.content[0].text.strip()

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "summary": result.get("summary", ""),
                "tags": result.get("tags", []),
            }

        return {"summary": response_text, "tags": []}

    except Exception as e:
        logger.error(f"Anthropic summarization failed: {e}")
        return mock_summarize(title, content)


async def summarize(title: str, content: str) -> dict[str, Any]:
    if settings.ANTHROPIC_API_KEY:
        return await anthropic_summarize(title, content)
    return mock_summarize(title, content)
