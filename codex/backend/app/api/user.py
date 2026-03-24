from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.content import NotificationPreferenceRequest, NotificationPreferenceResponse
from app.services.content import get_notification_preference, list_bookmarks, update_notification_preference


router = APIRouter(prefix="/me", tags=["user"])


@router.get("", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.get("/bookmarks")
def bookmarks(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    items = list_bookmarks(db, user.id)
    return [
        {
            "id": content.id,
            "title": content.title,
            "summary": content.summary,
            "source_name": content.source_name,
            "source_type": content.source_type.value,
            "language": content.language,
            "original_url": content.original_url,
            "tags": content.tags,
            "published_at": content.published_at,
            "author": content.author,
            "bookmarked": True,
        }
        for content in items
    ]


@router.get("/notifications", response_model=NotificationPreferenceResponse)
def notification_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> NotificationPreferenceResponse:
    preference = get_notification_preference(db, user.id)
    return NotificationPreferenceResponse(
        id=preference.id,
        keywords=preference.keywords,
        email_enabled=preference.email_enabled,
        slack_enabled=preference.slack_enabled,
    )


@router.put("/notifications", response_model=NotificationPreferenceResponse)
def update_notifications(
    payload: NotificationPreferenceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationPreferenceResponse:
    if not payload.keywords and not payload.email_enabled and not payload.slack_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one notification option is required")
    preference = update_notification_preference(
        db,
        user.id,
        keywords=payload.keywords,
        email_enabled=payload.email_enabled,
        slack_enabled=payload.slack_enabled,
    )
    return NotificationPreferenceResponse(
        id=preference.id,
        keywords=preference.keywords,
        email_enabled=preference.email_enabled,
        slack_enabled=preference.slack_enabled,
    )

