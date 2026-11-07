import { videoApi } from '../services/videoApi';
import { UploadItem, Video } from '../types/video';

export const CHUNK_SIZE = 5 * 1024 * 1024; // 5 MB

export async function computeBlobSha256(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(digest));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

export class ResumableChunkUploader {
  private file: File;
  private uploadId: string | null = null;
  private isPaused: boolean = false;
  private isCancelled: boolean = false;
  private onProgressCallback: (item: Partial<UploadItem>) => void;

  constructor(
    file: File,
    onProgress: (item: Partial<UploadItem>) => void,
    existingUploadId?: string
  ) {
    this.file = file;
    this.onProgressCallback = onProgress;
    this.uploadId = existingUploadId || null;
  }

  public pause() {
    this.isPaused = true;
  }

  public cancel() {
    this.isCancelled = true;
    this.isPaused = false;
  }

  public resume() {
    this.isPaused = false;
  }

  public async start(title: string, description?: string, sourceType: 'LIVE' | 'UPLOADED' = 'UPLOADED'): Promise<Video> {
    const totalBytes = this.file.size;
    const totalChunks = Math.ceil(totalBytes / CHUNK_SIZE);
    let uploadedChunksSet = new Set<number>();

    // 1. Initialize or resume upload session
    if (!this.uploadId) {
      this.onProgressCallback({
        status: 'UPLOADING',
        progress: 0,
        uploadedBytes: 0,
        totalBytes,
        totalChunks,
        currentChunk: 0,
      });

      const initData = await videoApi.initUpload({
        title: title || this.file.name,
        filename: this.file.name,
        file_size: totalBytes,
        content_type: this.file.type || 'video/mp4',
        total_chunks: totalChunks,
        chunk_size: CHUNK_SIZE,
        source_type: sourceType,
        description: description || undefined,
      });

      this.uploadId = initData.upload_id;
      uploadedChunksSet = new Set(initData.uploaded_chunks || []);
    } else {
      // Check existing status for resumption
      const statusData = await videoApi.getUploadStatus(this.uploadId);
      uploadedChunksSet = new Set(statusData.uploaded_chunks);
    }

    let uploadedBytes = 0;
    // Calculate already uploaded bytes
    for (let i = 0; i < totalChunks; i++) {
      if (uploadedChunksSet.has(i)) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, totalBytes);
        uploadedBytes += end - start;
      }
    }

    let lastTime = Date.now();
    let bytesSinceLastTime = 0;
    let speedBps = 0;

    // 2. Upload chunks sequentially with retry
    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      if (this.isCancelled) {
        throw new Error('Upload cancelled by user');
      }

      while (this.isPaused) {
        await new Promise((resolve) => setTimeout(resolve, 300));
        if (this.isCancelled) throw new Error('Upload cancelled by user');
      }

      if (uploadedChunksSet.has(chunkIndex)) {
        continue;
      }

      const start = chunkIndex * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, totalBytes);
      const chunkBlob = this.file.slice(start, end);
      const chunkSize = end - start;

      // Compute chunk SHA-256
      const chunkHash = await computeBlobSha256(chunkBlob);

      // Retry up to 3 times on network glitch
      let attempt = 0;
      let chunkSuccess = false;
      while (attempt < 3 && !chunkSuccess) {
        try {
          await videoApi.uploadChunk(this.uploadId!, chunkIndex, chunkBlob, chunkHash);
          chunkSuccess = true;
        } catch (err) {
          attempt++;
          if (attempt >= 3) throw err;
          await new Promise((r) => setTimeout(r, 1000 * attempt));
        }
      }

      uploadedBytes += chunkSize;
      bytesSinceLastTime += chunkSize;

      const now = Date.now();
      const elapsed = (now - lastTime) / 1000;
      if (elapsed >= 0.5) {
        speedBps = Math.round(bytesSinceLastTime / elapsed);
        lastTime = now;
        bytesSinceLastTime = 0;
      }

      const remainingBytes = totalBytes - uploadedBytes;
      const etaSeconds = speedBps > 0 ? Math.round(remainingBytes / speedBps) : 0;
      const progress = Math.min(Math.round((uploadedBytes / totalBytes) * 100), 99);

      this.onProgressCallback({
        status: 'UPLOADING',
        progress,
        uploadedBytes,
        totalBytes,
        currentChunk: chunkIndex + 1,
        totalChunks,
        speedBps,
        etaSeconds,
      });
    }

    // 3. Complete and assemble upload
    this.onProgressCallback({
      status: 'ASSEMBLING',
      progress: 99,
      uploadedBytes: totalBytes,
      speedBps: 0,
      etaSeconds: 0,
    });

    const video = await videoApi.completeUpload(this.uploadId!);

    this.onProgressCallback({
      status: 'PROCESSING',
      progress: 100,
      videoId: video.id,
    });

    return video;
  }
}

