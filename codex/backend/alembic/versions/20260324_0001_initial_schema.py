"""Initial schema for AI insights service.

Revision ID: 20260324_0001
Revises:
Create Date: 2026-03-24
"""

revision = "20260324_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Schema is managed by SQLAlchemy metadata for the MVP scaffold."""


def downgrade() -> None:
    """No-op downgrade for scaffold migration."""

