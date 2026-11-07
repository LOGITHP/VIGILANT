import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  ShieldCheck,
  Cpu,
  Layers,
  Sparkles,
  Trash2,
  Radio,
  FolderArchive
} from 'lucide-react';
import { UploadItem, VideoSourceType } from '../../types/video';
import { ResumableChunkUploader } from '../../utils/chunkUploader';
import { UploadQueueItem } from './UploadQueueItem';

interface UploadCenterProps {
  onUploadComplete?: () => void;
}

export const UploadCenter: React.FC<UploadCenterProps> = ({ onUploadComplete }) => {
  const [queue, setQueue] = useState<UploadItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [sourceType, setSourceType] = useState<VideoSourceType>('UPLOADED');
  const [cameraTag, setCameraTag] = useState('');
  const [description, setDescription] = useState('');
  const uploadersRef = useRef<Map<string, ResumableChunkUploader>>(new Map());
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const newItems: UploadItem[] = Array.from(files).map((file) => ({
      id: `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      file,
      title: cameraTag.trim() ? `${cameraTag.trim()} - ${file.name}` : file.name,
      sourceType,
      description: description.trim(),
      status: 'QUEUED',
      progress: 0,
      uploadedBytes: 0,
      totalBytes: file.size,
      speedBps: 0,
      etaSeconds: 0,
      currentChunk: 0,
      totalChunks: Math.ceil(file.size / (5 * 1024 * 1024)),
    }));

    setQueue((prev) => [...prev, ...newItems]);
    // Start uploading newly added items
    newItems.forEach((item) => startUpload(item));
  };

  const startUpload = async (item: UploadItem) => {
    const uploader = new ResumableChunkUploader(item.file, (progressUpdate) => {
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, ...progressUpdate } : q))
      );
    });

    uploadersRef.current.set(item.id, uploader);

    try {
      await uploader.start(item.title, item.description, item.sourceType || 'UPLOADED');
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, status: 'READY', progress: 100 } : q))
      );
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      if (msg !== 'Upload cancelled by user') {
        setQueue((prev) =>
          prev.map((q) =>
            q.id === item.id ? { ...q, status: 'FAILED', errorMessage: msg } : q
          )
        );
      }
    } finally {
      uploadersRef.current.delete(item.id);
    }
  };

  const handlePause = (id: string) => {
    const uploader = uploadersRef.current.get(id);
    if (uploader) {
      uploader.pause();
      setQueue((prev) =>
        prev.map((q) => (q.id === id ? { ...q, status: 'PAUSED' } : q))
      );
    }
  };

  const handleResume = (id: string) => {
    const uploader = uploadersRef.current.get(id);
    if (uploader) {
      uploader.resume();
      setQueue((prev) =>
        prev.map((q) => (q.id === id ? { ...q, status: 'UPLOADING' } : q))
      );
    }
  };

  const handleCancel = (id: string) => {
    const uploader = uploadersRef.current.get(id);
    if (uploader) {
      uploader.cancel();
      uploadersRef.current.delete(id);
    }
    setQueue((prev) => prev.filter((q) => q.id !== id));
  };

  const handleRetry = (id: string) => {
    const item = queue.find((q) => q.id === id);
    if (item) {
      startUpload(item);
    }
  };

  const handleClearCompleted = () => {
    setQueue((prev) => prev.filter((q) => q.status !== 'READY'));
  };

  return (
    <div className="space-y-6">
      {/* Target Archive Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#0a1819] border border-[#14373a] rounded-2xl p-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-[#15b89a] block font-semibold">
            Destination Surveillance Archive
          </span>
          <span className="text-xs text-slate-400">
            Select the designated archive catalog for this video ingestion batch.
          </span>
        </div>

        <div className="flex items-center gap-2 bg-[#061112] border border-[#183d40] p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setSourceType('UPLOADED')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
              sourceType === 'UPLOADED'
                ? 'bg-[#15b89a] text-slate-950 font-semibold shadow-[0_0_12px_rgba(21,184,154,0.3)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FolderArchive className="w-3.5 h-3.5" />
            <span>Uploaded Archive</span>
          </button>

          <button
            type="button"
            onClick={() => setSourceType('LIVE')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
              sourceType === 'LIVE'
                ? 'bg-rose-600 text-white font-semibold shadow-[0_0_12px_rgba(244,63,94,0.4)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Live Camera Dump</span>
          </button>
        </div>
      </div>

      {/* Upload Settings & Metadata Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#0a1618]/70 border border-[#133436] rounded-2xl p-5 backdrop-blur-md">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
            Camera Channel / Tag (Optional)
          </label>
          <input
            type="text"
            value={cameraTag}
            onChange={(e) => setCameraTag(e.target.value)}
            placeholder="e.g. CAM-01 • Perimeter North Gate"
            className="w-full bg-[#071314] border border-[#1a4447] rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#15b89a] transition-colors"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
            Surveillance Notes / Incident Context (Optional)
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Scheduled night shift patrol footage"
            className="w-full bg-[#071314] border border-[#1a4447] rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#15b89a] transition-colors"
          />
        </div>
      </div>

      {/* Drag & Drop Hero Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-10 sm:p-14 text-center cursor-pointer transition-all duration-300 overflow-hidden group ${
          isDragging
            ? 'border-[#2dd4bf] bg-[#15b89a]/10 scale-[1.01]'
            : 'border-[#173e40] hover:border-[#15b89a]/60 bg-[#081719]/60 hover:bg-[#0b1e20]/60'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="video/mp4,video/mkv,video/avi,video/webm,video/quicktime,.mp4,.mkv,.avi,.webm,.mov"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {/* Ambient Glow in Background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-[#15b89a]/10 rounded-full blur-3xl pointer-events-none group-hover:bg-[#15b89a]/15 transition-colors" />

        <div className="relative z-10 flex flex-col items-center">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-b from-[#133c3e] to-[#0a1e20] border border-[#1d5255] flex items-center justify-center text-[#2dd4bf] shadow-[0_10px_30px_rgba(21,184,154,0.15)] group-hover:scale-110 transition-transform duration-300 mb-5">
            <UploadCloud className="w-10 h-10 animate-pulse" />
          </div>

          <h3 className="text-xl font-medium text-slate-100 tracking-wide mb-2">
            Drag & Drop Surveillance Video Recordings
          </h3>
          <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
            Upload CCTV footage files (<span className="text-[#2dd4bf] font-mono">.mp4</span>,{' '}
            <span className="text-[#2dd4bf] font-mono">.mkv</span>,{' '}
            <span className="text-[#2dd4bf] font-mono">.webm</span>,{' '}
            <span className="text-[#2dd4bf] font-mono">.avi</span>). Files are automatically partitioned into 5MB chunks with SHA-256 integrity verification.
          </p>

          <button
            type="button"
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#15b89a] to-[#0d9488] hover:from-[#2dd4bf] hover:to-[#0f766e] text-slate-950 font-semibold text-sm shadow-[0_0_20px_rgba(21,184,154,0.3)] transition-all duration-300"
          >
            Browse Surveillance Files
          </button>
        </div>

        {/* Feature Badges */}
        <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto mt-10 pt-8 border-t border-[#143436]/60 text-left">
          <div className="flex items-center gap-2.5 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-[#2dd4bf] shrink-0" />
            <span>SHA-256 Chunk Verification</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-slate-400">
            <Cpu className="w-4 h-4 text-[#2dd4bf] shrink-0" />
            <span>Automated FFprobe Telemetry</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-slate-400">
            <Layers className="w-4 h-4 text-[#2dd4bf] shrink-0" />
            <span>MinIO S3 Object Storage</span>
          </div>
        </div>
      </div>

      {/* Upload Queue Section */}
      {queue.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-slate-200 tracking-wide uppercase flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#2dd4bf]" />
              Active Ingestion Queue ({queue.length})
            </h4>
            {queue.some((q) => q.status === 'READY') && (
              <button
                onClick={handleClearCompleted}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear Completed
              </button>
            )}
          </div>

          <div className="space-y-3">
            {queue.map((item) => (
              <UploadQueueItem
                key={item.id}
                item={item}
                onPause={handlePause}
                onResume={handleResume}
                onCancel={handleCancel}
                onRetry={handleRetry}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
