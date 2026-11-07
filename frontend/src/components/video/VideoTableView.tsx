import React from 'react';
import { Play, Trash2, Film, CheckCircle2, AlertTriangle, Loader2, FileSearch } from 'lucide-react';
import { Video } from '../../types/video';

interface VideoTableViewProps {
  videos: Video[];
  onPlay: (video: Video) => void;
  onDelete: (id: string) => void;
  onInspect?: (video: Video) => void;
}

export const VideoTableView: React.FC<VideoTableViewProps> = ({ videos, onPlay, onDelete, onInspect }) => {
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

  const formatDate = (isoString: string): string => {
    const d = new Date(isoString);
    return d.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-[#14373a] bg-[#0a1819]/80 backdrop-blur-md">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-[#14373a] bg-[#071314]/90 text-[11px] font-mono uppercase tracking-wider text-slate-400">
            <th className="py-3 px-4">Footage / Title</th>
            <th className="py-3 px-4">Source</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4">Resolution & FPS</th>
            <th className="py-3 px-4">Duration</th>
            <th className="py-3 px-4">Codecs</th>
            <th className="py-3 px-4">File Size</th>
            <th className="py-3 px-4">Ingested At</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#122e30] text-xs">
          {videos.map((video) => (
            <tr
              key={video.id}
              className="hover:bg-[#0e272a]/50 transition-colors group"
            >
              {/* Title & Preview */}
              <td className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <div
                    onClick={() => video.status === 'READY' && onPlay(video)}
                    className="relative w-12 h-8 rounded bg-[#050e0f] border border-[#14373a] shrink-0 overflow-hidden cursor-pointer"
                  >
                    {video.thumbnail_url ? (
                      <img
                        src={video.thumbnail_url}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-600">
                        <Film className="w-4 h-4" />
                      </div>
                    )}
                    {video.status === 'READY' && (
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Play className="w-3 h-3 text-[#2dd4bf] fill-current" />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 max-w-xs">
                    <p
                      onClick={() => video.status === 'READY' && onPlay(video)}
                      className="font-medium text-slate-100 hover:text-[#2dd4bf] truncate cursor-pointer transition-colors"
                    >
                      {video.title}
                    </p>
                    <p className="text-[11px] text-slate-500 font-mono truncate">
                      {video.original_filename}
                    </p>
                  </div>
                </div>
              </td>

              {/* Source Badge */}
              <td className="py-3 px-4">
                {video.source_type === 'LIVE' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-700/60 shadow-[0_0_8px_rgba(244,63,94,0.3)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                    LIVE REC
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-[#0b2527] text-[#2dd4bf] border border-[#16484c]">
                    UPLOADED
                  </span>
                )}
              </td>

              {/* Status */}
              <td className="py-3 px-4">
                {video.status === 'READY' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                    <CheckCircle2 className="w-3 h-3" /> READY
                  </span>
                )}
                {video.status === 'PROCESSING' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 animate-pulse">
                    <Loader2 className="w-3 h-3 animate-spin" /> PROCESSING
                  </span>
                )}
                {video.status === 'UPLOADING' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
                    <Loader2 className="w-3 h-3 animate-spin" /> UPLOADING
                  </span>
                )}
                {video.status === 'FAILED' && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-red-950/80 text-red-300 border border-red-800/60">
                    <AlertTriangle className="w-3 h-3" /> FAILED
                  </span>
                )}
              </td>

              {/* Resolution & FPS */}
              <td className="py-3 px-4 font-mono text-slate-300">
                {video.width && video.height ? (
                  <span>
                    {video.width}x{video.height}{' '}
                    {video.fps && <span className="text-slate-500">@{video.fps}fps</span>}
                  </span>
                ) : (
                  <span className="text-slate-600">--</span>
                )}
              </td>

              {/* Duration */}
              <td className="py-3 px-4 font-mono text-slate-300">
                {formatDuration(video.duration_seconds)}
              </td>

              {/* Codecs */}
              <td className="py-3 px-4 font-mono text-slate-400 uppercase">
                {video.video_codec ? (
                  <span className="px-1.5 py-0.5 rounded bg-[#0d2628] text-[#2dd4bf] text-[10px]">
                    {video.video_codec} {video.audio_codec && `/ ${video.audio_codec}`}
                  </span>
                ) : (
                  <span className="text-slate-600">--</span>
                )}
              </td>

              {/* File Size */}
              <td className="py-3 px-4 font-mono text-slate-300">
                {formatBytes(video.file_size)}
              </td>

              {/* Ingested Date */}
              <td className="py-3 px-4 font-mono text-slate-400">
                {formatDate(video.created_at)}
              </td>

              {/* Actions */}
              <td className="py-3 px-4 text-right">
                <div className="flex items-center justify-end gap-2">
                  {onInspect && (
                    <button
                      onClick={() => onInspect(video)}
                      className="p-1.5 rounded-lg bg-[#0e2a2c] hover:bg-[#164245] text-[#2dd4bf] hover:text-[#5eead4] transition-colors"
                      title="Inspect Metadata & Stream Manifest"
                    >
                      <FileSearch className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {video.status === 'READY' && (
                    <button
                      onClick={() => onPlay(video)}
                      className="p-1.5 rounded-lg bg-[#0e2a2c] hover:bg-[#15b89a] text-slate-300 hover:text-slate-950 transition-colors"
                      title="Play Footage"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Delete surveillance footage "${video.title}"?`)) {
                        onDelete(video.id);
                      }
                    }}
                    className="p-1.5 rounded-lg bg-[#0e2a2c] hover:bg-red-950/80 text-slate-400 hover:text-red-400 transition-colors"
                    title="Delete Footage"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
