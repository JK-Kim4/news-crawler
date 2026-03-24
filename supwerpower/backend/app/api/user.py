from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.content import Content
from app.models.interaction import Bookmark, Comment
from app.models.user import User
from app.schemas.interaction import (
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
    CommentCreate,
    CommentListResponse,
    CommentResponse,
)
from app.schemas.content import ContentResponse
from app.schemas.user import UserMe

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserMe)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookmark_count_result = await db.execute(
        select(func.count()).select_from(Bookmark).where(Bookmark.user_id == current_user.id)
    )
    bookmark_count = bookmark_count_result.scalar() or 0

    comment_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.user_id == current_user.id)
    )
    comment_count = comment_count_result.scalar() or 0

    return UserMe(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at,
        bookmark_count=bookmark_count,
        comment_count=comment_count,
    )


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .options(selectinload(Bookmark.content))
        .order_by(Bookmark.created_at.desc())
    )
    bookmarks = result.scalars().all()

    items = []
    for bm in bookmarks:
        content_resp = None
        if bm.content:
            content_resp = ContentResponse.model_validate(bm.content)
        items.append(
            BookmarkResponse(
                id=bm.id,
                user_id=bm.user_id,
                content_id=bm.content_id,
                created_at=bm.created_at,
                content=content_resp,
            )
        )

    return BookmarkListResponse(items=items, total=len(items))


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    body: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_result = await db.execute(
        select(Content).where(Content.id == body.content_id)
    )
    if not content_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    existing = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.content_id == body.content_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already bookmarked",
        )

    bookmark = Bookmark(user_id=current_user.id, content_id=body.content_id)
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        content_id=bookmark.content_id,
        created_at=bookmark.created_at,
    )


@router.delete("/bookmarks/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.content_id == content_id,
        )
    )
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    await db.delete(bookmark)
    await db.commit()


@router.post(
    "/contents/{content_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    content_id: str,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    if not content_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    comment = Comment(
        user_id=current_user.id,
        content_id=content_id,
        text=body.text,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        content_id=comment.content_id,
        text=comment.text,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        username=current_user.username,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment",
        )

    await db.delete(comment)
    await db.commit()


@router.get("/contents/{content_id}/comments", response_model=CommentListResponse)
async def list_comments(
    content_id: str,
    db: AsyncSession = Depends(get_db),
):
    content_result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    if not content_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    result = await db.execute(
        select(Comment)
        .where(Comment.content_id == content_id)
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at.desc())
    )
    comments = result.scalars().all()

    items = []
    for c in comments:
        items.append(
            CommentResponse(
                id=c.id,
                user_id=c.user_id,
                content_id=c.content_id,
                text=c.text,
                created_at=c.created_at,
                updated_at=c.updated_at,
                username=c.user.username if c.user else None,
            )
        )

    return CommentListResponse(items=items, total=len(items))
