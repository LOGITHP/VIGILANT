import { apiClient } from './api';
import {
  Video,
  VideoListResponse,
  VideoFilterParams,
  UploadInitRequest,
  UploadInitResponse,
  UploadStatusResponse,
  VideoInspectionReport
} from '../types/video';

export const videoApi = {
  initUpload: async (payload: UploadInitRequest): Promise<UploadInitResponse> => {
    const res = await apiClient.post<UploadInitResponse>('/videos/upload/init', payload);
    return res.data;
  },

  uploadChunk: async (
    uploadId: string,
    chunkIndex: number,
    chunkBlob: Blob,
    chunkHash?: string
  ): Promise<{ upload_id: string; chunk_index: number; status: string; uploaded_count: number }> => {
    const formData = new FormData();
    formData.append('upload_id', uploadId);
    formData.append('chunk_index', chunkIndex.toString());
    if (chunkHash) {
      formData.append('chunk_hash', chunkHash);
    }
    formData.append('file', chunkBlob, `${chunkIndex}.part`);

    const res = await apiClient.post('/videos/upload/chunk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getUploadStatus: async (uploadId: string): Promise<UploadStatusResponse> => {
    const res = await apiClient.get<UploadStatusResponse>(`/videos/upload/${uploadId}/status`);
    return res.data;
  },

  completeUpload: async (uploadId: string, expectedSha256?: string): Promise<Video> => {
    const res = await apiClient.post<Video>('/videos/upload/complete', {
      upload_id: uploadId,
      expected_sha256: expectedSha256 || undefined,
    });
    return res.data;
  },

  getVideos: async (params?: VideoFilterParams): Promise<VideoListResponse> => {
    const res = await apiClient.get<VideoListResponse>('/videos', { params });
    return res.data;
  },

  getVideo: async (id: string): Promise<Video> => {
    const res = await apiClient.get<Video>(`/videos/${id}`);
    return res.data;
  },

  deleteVideo: async (id: string): Promise<void> => {
    await apiClient.delete(`/videos/${id}`);
  },

  recordLiveFeed: async (payload: { camera_id: string; title?: string; duration_seconds?: number; description?: string }): Promise<Video> => {
    const res = await apiClient.post<Video>('/videos/live/record', payload);
    return res.data;
  },

  getInspectionReport: async (videoId: string): Promise<VideoInspectionReport> => {
    const res = await apiClient.get<VideoInspectionReport>(`/videos/${videoId}/inspection`);
    return res.data;
  },

  triggerInspection: async (videoId: string): Promise<{ message: string; status: string }> => {
    const res = await apiClient.post<{ message: string; status: string }>(`/videos/${videoId}/inspect`);
    return res.data;
  },

  getStreamUrl: (id: string): string => {
    const base = apiClient.defaults.baseURL || 'http://localhost:8000/api/v1';
    return `${base}/videos/${id}/stream`;
  },

  getThumbnailUrl: (id: string): string => {
    const base = apiClient.defaults.baseURL || 'http://localhost:8000/api/v1';
    return `${base}/videos/${id}/thumbnail`;
  },
};

