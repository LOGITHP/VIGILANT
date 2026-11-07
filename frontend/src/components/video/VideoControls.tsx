import React, { useState, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Gauge
} from 'lucide-react';

interface VideoControlsProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  currentTime: number;
  duration: number;
  bufferedEnd: number;
  onSeek: (time: number) => void;
  playbackRate: number;
  onRateChange: (rate: number) => void;
  volume: number;
  onVolumeChange: (vol: number) => void;
  isMuted: boolean;
  onToggleMute: () => void;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
}

export const VideoControls: React.FC<VideoControlsProps> = ({
  isPlaying,
  onPlayPause,
  currentTime,
  duration,
  bufferedEnd,
  onSeek,
  playbackRate,
  onRateChange,
  volume,
  onVolumeChange,
  isMuted,
  onToggleMute,
  isFullscreen,
  onToggleFullscreen,
}) => {
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const progressBarRef = useRef<HTMLDivElement>(null);

  const formatTime = (seconds: number): string => {
    if (isNaN(seconds) || seconds < 0) return '00:00:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current || duration <= 0) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    onSeek(pos * duration);
  };

  const speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;
  const bufferedPercent = duration > 0 ? (bufferedEnd / duration) * 100 : 0;

  return (
    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/95 via-black/80 to-transparent p-4 flex flex-col gap-2.5 z-20 select-none">
      {/* Scrub Bar */}
      <div
        ref={progressBarRef}
        onClick={handleProgressClick}
        className="relative w-full h-2 bg-neutral-800/80 hover:h-3 rounded-full cursor-pointer transition-all duration-200 group"
      >
        {/* Buffered Progress */}
        <div
          className="absolute h-full bg-[#15b89a]/30 rounded-full"
          style={{ width: `${Math.min(bufferedPercent, 100)}%` }}
        />
        {/* Playhead Progress */}
        <div
          className="absolute h-full bg-gradient-to-r from-[#15b89a] to-[#2dd4bf] rounded-full shadow-[0_0_10px_rgba(45,212,191,0.5)]"
          style={{ width: `${Math.min(progressPercent, 100)}%` }}
        />
        {/* Scrub Handle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -ml-2 w-4 h-4 rounded-full bg-[#2dd4bf] border-2 border-white shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ left: `${Math.min(progressPercent, 100)}%` }}
        />
      </div>

      {/* Controls Strip */}
      <div className="flex items-center justify-between text-slate-200 text-xs sm:text-sm">
        {/* Left: Playback & Seeking */}
        <div className="flex items-center gap-3">
          {/* Play/Pause */}
          <button
            onClick={onPlayPause}
            className="p-2 rounded-xl bg-[#15b89a] text-slate-950 hover:bg-[#2dd4bf] transition-all shadow-[0_0_15px_rgba(21,184,154,0.4)]"
            title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
          >
            {isPlaying ? (
              <Pause className="w-4 h-4 fill-current" />
            ) : (
              <Play className="w-4 h-4 fill-current ml-0.5" />
            )}
          </button>

          {/* Quick Jumps */}
          <button
            onClick={() => onSeek(Math.max(currentTime - 10, 0))}
            className="p-1.5 text-slate-400 hover:text-white transition-colors"
            title="Rewind 10s (Left Arrow)"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => onSeek(Math.min(currentTime + 10, duration))}
            className="p-1.5 text-slate-400 hover:text-white transition-colors"
            title="Fast Forward 10s (Right Arrow)"
          >
            <RotateCw className="w-4 h-4" />
          </button>

          {/* Timestamp Display */}
          <div className="font-mono text-xs text-slate-300 ml-2">
            <span className="text-[#2dd4bf] font-medium">{formatTime(currentTime)}</span>
            <span className="text-slate-600 mx-1.5">/</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Right: Volume, Speed & Fullscreen */}
        <div className="flex items-center gap-4">
          {/* Volume Control */}
          <div className="flex items-center gap-2">
            <button
              onClick={onToggleMute}
              className="p-1.5 text-slate-400 hover:text-white transition-colors"
              title={isMuted ? 'Unmute (M)' : 'Mute (M)'}
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-4 h-4 text-red-400" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
              className="w-16 h-1 bg-neutral-700 accent-[#2dd4bf] rounded-full cursor-pointer"
            />
          </div>

          {/* Playback Speed Menu */}
          <div className="relative">
            <button
              onClick={() => setShowSpeedMenu(!showSpeedMenu)}
              className="px-2.5 py-1 rounded-lg bg-[#0e2729] hover:bg-[#13373a] border border-[#1a4447] text-xs font-mono text-[#2dd4bf] flex items-center gap-1.5 transition-colors"
            >
              <Gauge className="w-3.5 h-3.5" />
              {playbackRate}x
            </button>

            {showSpeedMenu && (
              <div className="absolute bottom-full right-0 mb-2 w-28 bg-[#0a1819] border border-[#14373a] rounded-xl p-1 shadow-2xl flex flex-col gap-0.5">
                {speeds.map((rate) => (
                  <button
                    key={rate}
                    onClick={() => {
                      onRateChange(rate);
                      setShowSpeedMenu(false);
                    }}
                    className={`px-3 py-1.5 text-xs text-left rounded-lg font-mono transition-colors ${
                      playbackRate === rate
                        ? 'bg-[#15b89a] text-slate-950 font-medium'
                        : 'text-slate-300 hover:bg-[#122e30]'
                    }`}
                  >
                    {rate}x Speed
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Fullscreen Toggle */}
          <button
            onClick={onToggleFullscreen}
            className="p-1.5 text-slate-400 hover:text-white transition-colors"
            title={isFullscreen ? 'Exit Fullscreen (F)' : 'Fullscreen (F)'}
          >
            {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};
