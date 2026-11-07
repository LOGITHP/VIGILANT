export type VideoStatus = 'UPLOADING' | 'PROCESSING' | 'READY' | 'FAILED';
export type VideoSourceType = 'LIVE' | 'UPLOADED';

export interface Video {
  id: string;
  title: string;
  source_type: VideoSourceType;
  description?: string | null;
  original_filename: string;
  file_size: number;
  content_type: string;
  sha256_checksum?: string | null;
  status: VideoStatus;
  error_message?: string | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  video_codec?: string | null;
  audio_codec?: string | null;
  bitrate?: number | null;
  thumbnail_url?: string | null;
  stream_url: string;
  uploaded_by?: string | null;
  metadata_status?: 'PENDING' | 'EXTRACTING' | 'COMPLETED' | 'FAILED';
  validation_status?: 'PENDING' | 'VALIDATING' | 'VALIDATED' | 'INVALID';
  created_at: string;
  updated_at: string;
}

export interface VideoListResponse {
  items: Video[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface VideoFilterParams {
  page?: number;
  limit?: number;
  q?: string;
  status?: string;
  source_type?: 'LIVE' | 'UPLOADED' | 'ALL';
  codec?: string;
}

export interface UploadInitRequest {
  title: string;
  filename: string;
  file_size: number;
  content_type: string;
  total_chunks: number;
  chunk_size: number;
  source_type?: VideoSourceType;
  description?: string;
  expected_sha256?: string;
}

export interface LiveCaptureRequest {
  camera_id: string;
  title?: string;
  duration_seconds?: number;
  description?: string;
}

export interface UploadInitResponse {
  upload_id: string;
  video_id: string;
  chunk_size: number;
  total_chunks: number;
  uploaded_chunks: number[];
}

export interface UploadStatusResponse {
  upload_id: string;
  video_id: string;
  total_chunks: number;
  uploaded_chunks: number[];
  is_completed: boolean;
}

export interface UploadItem {
  id: string;
  file: File;
  title: string;
  sourceType?: VideoSourceType;
  description: string;
  status: 'QUEUED' | 'CALCULATING_HASH' | 'UPLOADING' | 'ASSEMBLING' | 'PROCESSING' | 'READY' | 'FAILED' | 'PAUSED';
  progress: number; // 0 - 100
  uploadedBytes: number;
  totalBytes: number;
  speedBps: number;
  etaSeconds: number;
  currentChunk: number;
  totalChunks: number;
  errorMessage?: string;
  videoId?: string;
}

export interface FileInfo {
  original_filename: string;
  file_size: number;
  file_format?: string | null;
  sha256_checksum?: string | null;
  upload_timestamp: string;
}

export interface ContainerInfo {
  format_name?: string | null;
  format_long_name?: string | null;
  duration_seconds?: number | null;
  bitrate?: number | null;
  start_time?: number | null;
  container_size?: number | null;
}

export interface VideoStreamInfo {
  stream_index: number;
  codec_name: string;
  codec_long_name?: string | null;
  width: number;
  height: number;
  fps?: number | null;
  rational_fps?: string | null;
  pixel_format?: string | null;
  time_base?: string | null;
  start_timestamp?: number | null;
  duration_seconds?: number | null;
  reported_frame_count?: number | null;
}

export interface AudioStreamInfo {
  has_audio: boolean;
  stream_index?: number | null;
  codec_name?: string | null;
  sample_rate?: number | null;
  channels?: number | null;
  channel_layout?: string | null;
  duration_seconds?: number | null;
}

export interface StreamSummary {
  stream_index: number;
  stream_type: string;
  codec_name?: string | null;
  codec_long_name?: string | null;
  is_primary: boolean;
  is_default: boolean;
  is_attached_pic: boolean;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  rational_fps?: string | null;
  pixel_format?: string | null;
  time_base?: string | null;
  sample_rate?: number | null;
  channels?: number | null;
  channel_layout?: string | null;
  duration_seconds?: number | null;
  bitrate?: number | null;
  disposition?: Record<string, any> | null;
  stream_metadata?: Record<string, any> | null;
}

export interface VideoInspectionReport {
  inspection_id: string;
  video_id: string;
  extractor_version: string;
  metadata_status: 'EXTRACTING' | 'COMPLETED' | 'FAILED';
  validation_status: 'PENDING' | 'VALIDATED' | 'INVALID';
  error_message?: string | null;
  inspected_at: string;
  file_info: FileInfo;
  container_info: ContainerInfo;
  video_stream?: VideoStreamInfo | null;
  audio_stream: AudioStreamInfo;
  all_streams: StreamSummary[];
  raw_metadata?: Record<string, any> | null;
}


