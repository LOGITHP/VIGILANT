import React from 'react';
import {
  Play,
  Film,
  HardDrive,
  Trash2,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import { Video } from '../../types/video';

interface VideoCardProps {
  video: Video;
  onPlay: (video: Video) => void;
  onDelete: (id: string) => void;
}

export const VideoCard: React.FC<VideoCardProps> = ({ video, onPlay, onDelete }) => {
  const formatDuration = (seconds?: number | null): string => {
    if (!seconds) return '--:--';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const getResolutionBadge = () => {
    if (!video.height) return null;
    if (video.height >= 2160) {
      return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-800/60 font-semibold">4K UHD</span>;
    }
    if (video.height >= 1080) {
      return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 font-semibold">1080p FHD</span>;
    }
    if (video.height >= 720) {
      return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950/80 text-teal-300 border border-teal-800/60 font-semibold">720p HD</span>;
    }
    return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 font-semibold">{video.height}p</span>;
  };

  return (
    <div className="group relative bg-[#0a1819] border border-[#14373a] hover:border-[#15b89a]/60 rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-[0_15px_35px_rgba(0,0,0,0.6),0_0_20px_rgba(21,184,154,0.15)] flex flex-col">
      {/* Thumbnail Area */}
      <div
        onClick={() => video.status === 'READY' && onPlay(video)}
        className="relative aspect-video w-full bg-[#050e0f] overflow-hidden cursor-pointer select-none"
      >
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-slate-600 gap-2">
            <Film className="w-8 h-8 opacity-40" />
            <span className="text-xs font-mono opacity-50">CCTV STREAM</span>
          </div>
        )}

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20" />

        {/* Status Pill on Top Left */}
        <div className="absolute top-2.5 left-2.5">
          {video.status === 'READY' && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 backdrop-blur-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              READY
            </span>
          )}
          {video.status === 'PROCESSING' && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 backdrop-blur-sm">
              <Loader2 className="w-2.5 h-2.5 animate-spin" />
              PROCESSING
            </span>
          )}
          {video.status === 'UPLOADING' && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 backdrop-blur-sm">
              <Loader2 className="w-2.5 h-2.5 animate-spin" />
              INGESTING
            </span>
          )}
          {video.status === 'FAILED' && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-red-950/80 text-red-300 border border-red-800/60 backdrop-blur-sm">
              <AlertTriangle className="w-2.5 h-2.5" />
              FAILED
            </span>
          )}
        </div>

        {/* Duration Badge Bottom Right */}
        {video.duration_seconds && (
          <div className="absolute bottom-2.5 right-2.5 text-xs font-mono font-medium px-2 py-0.5 rounded bg-black/80 text-slate-200 border border-white/10 backdrop-blur-sm">
            {formatDuration(video.duration_seconds)}
          </div>
        )}

        {/* Hover Play Button */}
        {video.status === 'READY' && (
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/40 backdrop-blur-[2px]">
            <div className="w-12 h-12 rounded-full bg-[#15b89a] text-slate-950 flex items-center justify-center shadow-[0_0_25px_rgba(21,184,154,0.6)] transform scale-75 group-hover:scale-100 transition-transform duration-300">
              <Play className="w-5 h-5 ml-0.5 fill-current" />
            </div>
          </div>
        )}
      </div>

      {/* Details Body */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <h3
              onClick={() => video.status === 'READY' && onPlay(video)}
              className="text-sm font-medium text-slate-100 hover:text-[#2dd4bf] transition-colors line-clamp-1 cursor-pointer"
              title={video.title}
            >
              {video.title}
            </h3>
            {getResolutionBadge()}
          </div>

          <p className="text-xs text-slate-400 line-clamp-1 mb-3 font-mono">
            {video.original_filename}
          </p>
        </div>

        {/* Footer Meta */}
        <div className="pt-3 border-t border-[#123133] flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 font-mono">
              <HardDrive className="w-3 h-3 text-slate-500" />
              {formatBytes(video.file_size)}
            </span>
            {video.video_codec && (
              <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-[#0e2729] text-[#2dd4bf]">
                {video.video_codec}
              </span>
            )}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Delete surveillance footage "${video.title}"?`)) {
                onDelete(video.id);
              }
            }}
            title="Delete Video"
            className="p-1 rounded text-slate-500 hover:text-red-400 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
