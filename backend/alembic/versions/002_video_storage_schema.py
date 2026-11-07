"""Video storage and upload sessions schema

Revision ID: 002_video_storage_schema
Revises: 001_initial_auth_schema
Create Date: 2026-11-07 11:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_video_storage_schema'
down_revision: Union[str, None] = '001_initial_auth_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create videos table
    op.create_table(
        'videos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False, server_default='video/mp4'),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=True),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_s3_key', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='UPLOADING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('video_codec', sa.String(length=50), nullable=True),
        sa.Column('audio_codec', sa.String(length=50), nullable=True),
        sa.Column('bitrate', sa.BigInteger(), nullable=True),
        sa.Column('raw_metadata', sa.JSON(), nullable=True),
        sa.Column('uploaded_by_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('s3_key')
    )
    op.create_index(op.f('ix_videos_title'), 'videos', ['title'], unique=False)
    op.create_index(op.f('ix_videos_status'), 'videos', ['status'], unique=False)
    op.create_index(op.f('ix_videos_uploaded_by_id'), 'videos', ['uploaded_by_id'], unique=False)
    op.create_index(op.f('ix_videos_created_at'), 'videos', ['created_at'], unique=False)

    # 2. Create video_upload_sessions table
    op.create_table(
        'video_upload_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('video_id', sa.UUID(), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='5242880'),
        sa.Column('uploaded_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expected_sha256', sa.String(length=64), nullable=True),
        sa.Column('temp_directory', sa.String(length=500), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_upload_sessions_video_id'), 'video_upload_sessions', ['video_id'], unique=False)

    # 3. Create video_chunks table
    op.create_table(
        'video_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('upload_session_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=False),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['upload_session_id'], ['video_upload_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_chunks_upload_session_id'), 'video_chunks', ['upload_session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_video_chunks_upload_session_id'), table_name='video_chunks')
    op.drop_table('video_chunks')
    op.drop_index(op.f('ix_video_upload_sessions_video_id'), table_name='video_upload_sessions')
    op.drop_table('video_upload_sessions')
    op.drop_index(op.f('ix_videos_created_at'), table_name='videos')
    op.drop_index(op.f('ix_videos_uploaded_by_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_status'), table_name='videos')
    op.drop_index(op.f('ix_videos_title'), table_name='videos')
    op.drop_table('videos')
