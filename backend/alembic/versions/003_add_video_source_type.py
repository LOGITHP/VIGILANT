"""Add source_type to videos table

Revision ID: 003_add_video_source_type
Revises: 002_video_storage_schema
Create Date: 2026-11-07 12:11:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_video_source_type'
down_revision: Union[str, None] = '002_video_storage_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'videos',
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='UPLOADED')
    )
    op.create_index(op.f('ix_videos_source_type'), 'videos', ['source_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_videos_source_type'), table_name='videos')
    op.drop_column('videos', 'source_type')

