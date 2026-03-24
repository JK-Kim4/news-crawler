from datetime import UTC, datetime

from app.models.content import Content
from app.models.enums import SourceType
from app.models.source import Source


def test_content_feed_filters_and_searches(client, db_session):
    source = db_session.query(Source).first()
    content = Content(
        source_id=source.id,
        source_type=SourceType.BLOG,
        source_name="Test Source",
        language="ko",
        title="AI 에이전트 설계 패턴",
        original_url="https://example.com/agent-design",
        published_at=datetime.now(UTC),
        author="Tester",
        summary="에이전트 시스템과 워크플로 설계 핵심 요약",
        tags=["ai", "agent", "workflow"],
        raw_content="원문 본문",
    )
    db_session.add(content)
    db_session.commit()

    response = client.get("/api/content", params={"q": "에이전트", "language": "ko"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "AI 에이전트 설계 패턴"

