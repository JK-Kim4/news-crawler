from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.content import CommentCreateRequest, CommentResponse, ContentDetailResponse, ContentListResponse
from app.services.content import add_comment, get_content, list_contents, set_bookmark


router = APIRouter(prefix="/content", tags=["content"])


def _serialize_comment(comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        username=comment.user.username if comment.user else "",
        content=comment.content_text,
        created_at=comment.created_at,
    )


def _serialize_content(content, current_user: User | None = None, include_comments: bool = False):
    bookmarked = False
    if current_user is not None:
        bookmarked = any(bookmark.user_id == current_user.id for bookmark in content.bookmarks)

    payload = {
        "id": content.id,
        "source_name": content.source_name,
        "source_type": content.source_type.value,
        "language": content.language,
        "title": content.title,
        "original_url": content.original_url,
        "summary": content.summary,
        "tags": content.tags,
        "published_at": content.published_at,
        "author": content.author,
        "bookmarked": bookmarked,
    }
    if include_comments:
        return ContentDetailResponse(
            **payload,
            raw_content=content.raw_content,
            comments=[_serialize_comment(comment) for comment in content.comments],
        )
    return ContentListResponse(**payload)


@router.get("", response_model=list[ContentListResponse])
def list_content_items(
    q: str | None = Query(default=None),
    language: str | None = Query(default=None),
    source_name: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ContentListResponse]:
    return [_serialize_content(content) for content in list_contents(db, q=q, language=language, source_name=source_name, source_type=source_type)]


@router.get("/{content_id}", response_model=ContentDetailResponse)
def get_content_item(content_id: str, db: Session = Depends(get_db)) -> ContentDetailResponse:
    content = get_content(db, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return _serialize_content(content, include_comments=True)


@router.post("/{content_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def create_bookmark(content_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    set_bookmark(db, user.id, content_id, True)


@router.delete("/{content_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def remove_bookmark(content_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    set_bookmark(db, user.id, content_id, False)


@router.post("/{content_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    content_id: str,
    payload: CommentCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CommentResponse:
    comment = add_comment(db, user.id, content_id, payload.content)
    comment.user = user
    return _serialize_comment(comment)

