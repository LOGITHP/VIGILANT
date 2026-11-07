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

