import React from 'react';
import {
  Film,
  CheckCircle2,
  AlertCircle,
  Pause,
  Play,
  X,
  RotateCcw,
  Clock,
  Zap,
  HardDrive
} from 'lucide-react';
import { UploadItem } from '../../types/video';

interface UploadQueueItemProps {
  item: UploadItem;
  onPause: (id: string) => void;
  onResume: (id: string) => void;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
}

export const UploadQueueItem: React.FC<UploadQueueItemProps> = ({
  item,
  onPause,
  onResume,
  onCancel,
  onRetry,
}) => {
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatSpeed = (bps: number): string => {
    if (bps <= 0) return '0 KB/s';
    return `${formatBytes(bps)}/s`;
  };

  const formatEta = (seconds: number): string => {
    if (seconds <= 0) return '--';
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
  };

  const getStatusBadge = () => {
    switch (item.status) {
      case 'QUEUED':
        return <span className="text-xs px-2.5 py-0.5 rounded-full bg-neutral-800 text-neutral-400">QUEUED</span>;
      case 'CALCULATING_HASH':
        return <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 animate-pulse">VERIFYING</span>;
      case 'UPLOADING':
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#15b89a]/15 text-[#2dd4bf] border border-[#15b89a]/30 animate-pulse">
            UPLOADING {item.currentChunk}/{item.totalChunks}
          </span>
        );
      case 'ASSEMBLING':
        return <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-950/80 text-amber-400 border border-amber-800/60 animate-pulse">ASSEMBLING STREAM</span>;
      case 'PROCESSING':
        return <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950/80 text-indigo-400 border border-indigo-800/60 animate-pulse">EXTRACTING TELEMETRY</span>;
      case 'READY':
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> READY
          </span>
        );
      case 'PAUSED':
        return <span className="text-xs px-2.5 py-0.5 rounded-full bg-yellow-950/80 text-yellow-400 border border-yellow-800/60">PAUSED</span>;
      case 'FAILED':
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-red-950/80 text-red-400 border border-red-800/60 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> FAILED
          </span>
        );
    }
  };

  return (
    <div className="bg-[#0b1b1d]/80 border border-[#163638] rounded-xl p-4 transition-all duration-300 hover:border-[#15b89a]/40 shadow-lg">
      <div className="flex items-start justify-between gap-4">
        {/* Left: Icon & File Meta */}
        <div className="flex items-start gap-3.5 min-w-0">
          <div className="w-10 h-10 rounded-lg bg-[#0e2a2c] border border-[#1a4447] flex items-center justify-center shrink-0 text-[#2dd4bf]">
            <Film className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-medium text-slate-100 truncate">{item.title}</h4>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span className="truncate">{item.file.name}</span>
              <span>•</span>
              <span className="shrink-0">{formatBytes(item.totalBytes)}</span>
            </div>
          </div>
        </div>

        {/* Right: Status Pill & Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {getStatusBadge()}

          {item.status === 'UPLOADING' && (
            <button
              onClick={() => onPause(item.id)}
              title="Pause Upload"
              className="p-1.5 rounded-lg bg-[#0e2a2c] hover:bg-[#13393c] text-slate-300 hover:text-white transition-colors"
            >
              <Pause className="w-3.5 h-3.5" />
            </button>
          )}

          {item.status === 'PAUSED' && (
            <button
              onClick={() => onResume(item.id)}
              title="Resume Upload"
              className="p-1.5 rounded-lg bg-[#0e2a2c] hover:bg-[#13393c] text-[#2dd4bf] hover:text-white transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
            </button>
          )}

          {item.status === 'FAILED' && (
            <button
              onClick={() => onRetry(item.id)}
              title="Retry Upload"
              className="p-1.5 rounded-lg bg-red-950/60 hover:bg-red-900/60 text-red-300 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}

          {item.status !== 'READY' && (
            <button
              onClick={() => onCancel(item.id)}
              title="Cancel Upload"
              className="p-1.5 rounded-lg bg-[#0e2a2c] hover:bg-red-950/60 text-slate-400 hover:text-red-300 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-3.5">
        <div className="w-full h-1.5 bg-[#081718] rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              item.status === 'FAILED'
                ? 'bg-red-500'
                : item.status === 'READY'
                ? 'bg-emerald-500'
                : 'bg-gradient-to-r from-[#15b89a] to-[#2dd4bf]'
            }`}
            style={{ width: `${item.progress}%` }}
          />
        </div>
      </div>

      {/* Telemetry Footer */}
      <div className="flex items-center justify-between text-xs text-slate-400 mt-2 font-mono">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <HardDrive className="w-3 h-3 text-slate-500" />
            {formatBytes(item.uploadedBytes)} / {formatBytes(item.totalBytes)} ({item.progress}%)
          </span>
          {item.status === 'UPLOADING' && item.speedBps > 0 && (
            <span className="flex items-center gap-1 text-[#2dd4bf]">
              <Zap className="w-3 h-3" />
              {formatSpeed(item.speedBps)}
            </span>
          )}
        </div>

        {item.status === 'UPLOADING' && item.etaSeconds > 0 && (
          <span className="flex items-center gap-1 text-slate-400">
            <Clock className="w-3 h-3 text-slate-500" />
            ETA: {formatEta(item.etaSeconds)}
          </span>
        )}

        {item.errorMessage && (
          <span className="text-red-400 truncate max-w-xs">{item.errorMessage}</span>
        )}
      </div>
    </div>
  );
};

