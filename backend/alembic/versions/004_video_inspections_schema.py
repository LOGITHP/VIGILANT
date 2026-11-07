"""Create video_inspections and video_streams tables

Revision ID: 004_video_inspections_schema
Revises: 003_add_video_source_type
Create Date: 2026-11-07 13:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_video_inspections_schema'
down_revision: Union[str, None] = '003_add_video_source_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update videos table with inspection and validation state
    op.add_column(
        'videos',
        sa.Column('metadata_status', sa.String(length=30), nullable=False, server_default='PENDING')
    )
    op.create_index(op.f('ix_videos_metadata_status'), 'videos', ['metadata_status'], unique=False)

    op.add_column(
        'videos',
        sa.Column('validation_status', sa.String(length=30), nullable=False, server_default='PENDING')
    )
    op.create_index(op.f('ix_videos_validation_status'), 'videos', ['validation_status'], unique=False)

    # 2. Create video_inspections table
    op.create_table(
        'video_inspections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('video_id', sa.UUID(), nullable=False),
        sa.Column('extractor_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('metadata_status', sa.String(length=30), nullable=False, server_default='EXTRACTING'),
        sa.Column('validation_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        # Category A: File Information
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_format', sa.String(length=100), nullable=True),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=True),
        # Category B: Container Information
        sa.Column('format_name', sa.String(length=100), nullable=True),
        sa.Column('format_long_name', sa.String(length=255), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('bitrate', sa.BigInteger(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=True),
        sa.Column('container_size', sa.BigInteger(), nullable=True),
        # Category C: Primary Video Stream Information
        sa.Column('primary_video_stream_index', sa.Integer(), nullable=True),
        sa.Column('video_codec', sa.String(length=50), nullable=True),
        sa.Column('video_codec_long_name', sa.String(length=255), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('rational_fps', sa.String(length=50), nullable=True),
        sa.Column('pixel_format', sa.String(length=50), nullable=True),
        sa.Column('time_base', sa.String(length=50), nullable=True),
        sa.Column('video_start_time', sa.Float(), nullable=True),
        sa.Column('video_duration_seconds', sa.Float(), nullable=True),
        sa.Column('reported_frame_count', sa.BigInteger(), nullable=True),
        # Category D: Primary Audio Stream Information
        sa.Column('has_audio', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('primary_audio_stream_index', sa.Integer(), nullable=True),
        sa.Column('audio_codec', sa.String(length=50), nullable=True),
        sa.Column('audio_sample_rate', sa.Integer(), nullable=True),
        sa.Column('audio_channels', sa.Integer(), nullable=True),
        sa.Column('audio_channel_layout', sa.String(length=50), nullable=True),
        sa.Column('audio_duration_seconds', sa.Float(), nullable=True),
        # Category E & Raw Telemetry
        sa.Column('raw_ffprobe_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_inspections_video_id'), 'video_inspections', ['video_id'], unique=False)
    op.create_index(op.f('ix_video_inspections_metadata_status'), 'video_inspections', ['metadata_status'], unique=False)
    op.create_index(op.f('ix_video_inspections_validation_status'), 'video_inspections', ['validation_status'], unique=False)

    # 3. Create video_streams table
    op.create_table(
        'video_streams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('inspection_id', sa.UUID(), nullable=False),
        sa.Column('stream_index', sa.Integer(), nullable=False),
        sa.Column('stream_type', sa.String(length=30), nullable=False),
        sa.Column('codec_name', sa.String(length=50), nullable=True),
        sa.Column('codec_long_name', sa.String(length=255), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_attached_pic', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('rational_fps', sa.String(length=50), nullable=True),
        sa.Column('pixel_format', sa.String(length=50), nullable=True),
        sa.Column('time_base', sa.String(length=50), nullable=True),
        sa.Column('sample_rate', sa.Integer(), nullable=True),
        sa.Column('channels', sa.Integer(), nullable=True),
        sa.Column('channel_layout', sa.String(length=50), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('bitrate', sa.BigInteger(), nullable=True),
        sa.Column('disposition', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('stream_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['inspection_id'], ['video_inspections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_streams_inspection_id'), 'video_streams', ['inspection_id'], unique=False)
    op.create_index(op.f('ix_video_streams_stream_type'), 'video_streams', ['stream_type'], unique=False)


def downgrade() -> None:
    op.drop_table('video_streams')
    op.drop_table('video_inspections')
    op.drop_index(op.f('ix_videos_validation_status'), table_name='videos')
    op.drop_column('videos', 'validation_status')
    op.drop_index(op.f('ix_videos_metadata_status'), table_name='videos')
    op.drop_column('videos', 'metadata_status')
