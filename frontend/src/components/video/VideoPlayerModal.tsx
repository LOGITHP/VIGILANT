import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Info,
  Layers
} from 'lucide-react';
import { Video } from '../../types/video';
import { VideoControls } from './VideoControls';

interface VideoPlayerModalProps {
  video: Video | null;
  onClose: () => void;
}

export const VideoPlayerModal: React.FC<VideoPlayerModalProps> = ({ video, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(video?.duration_seconds || 0);
  const [bufferedEnd, setBufferedEnd] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showTelemetry, setShowTelemetry] = useState(true);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.code === 'Space') {
        e.preventDefault();
        togglePlayPause();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        seek(currentTime - 5);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        seek(currentTime + 5);
      } else if (e.key.toLowerCase() === 'f') {
        e.preventDefault();
        toggleFullscreen();
      } else if (e.key.toLowerCase() === 'm') {
        e.preventDefault();
        toggleMute();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentTime, duration, isPlaying, isFullscreen, isMuted]);

  if (!video) return null;

  const togglePlayPause = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const seek = (time: number) => {
    if (!videoRef.current) return;
    const clamped = Math.max(0, Math.min(time, duration));
    videoRef.current.currentTime = clamped;
    setCurrentTime(clamped);
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    setCurrentTime(videoRef.current.currentTime);

    // Calculate buffered range
    const buf = videoRef.current.buffered;
    if (buf.length > 0) {
      setBufferedEnd(buf.end(buf.length - 1));
    }
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    if (videoRef.current.duration && !isNaN(videoRef.current.duration)) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleRateChange = (rate: number) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const handleVolumeChange = (vol: number) => {
    if (!videoRef.current) return;
    videoRef.current.volume = vol;
    setVolume(vol);
    setIsMuted(vol === 0);
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 select-none animate-fadeIn">
      <div
        ref={containerRef}
        className="relative w-full max-w-6xl bg-[#061112] border border-[#143c3f] rounded-3xl overflow-hidden shadow-[0_25px_80px_rgba(0,0,0,0.9),0_0_50px_rgba(21,184,154,0.1)] flex flex-col"
      >
        {/* Modal Top Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#13373a] bg-[#071517]">
          <div className="flex items-center gap-3 min-w-0">
            <span className="w-2.5 h-2.5 rounded-full bg-[#15b89a] animate-pulse" />
            <div className="min-w-0">
              <h2 className="text-sm sm:text-base font-medium text-slate-100 truncate tracking-wide">
                {video.title}
              </h2>
              <div className="flex items-center gap-3 text-xs text-slate-400 font-mono mt-0.5">
                <span className="truncate">{video.original_filename}</span>
                <span>•</span>
                <span>{formatBytes(video.file_size)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setShowTelemetry(!showTelemetry)}
              title="Toggle Surveillance Telemetry"
              className={`p-2 rounded-xl transition-colors ${
                showTelemetry
                  ? 'bg-[#15b89a]/20 text-[#2dd4bf] border border-[#15b89a]/40'
                  : 'bg-[#0a1e20] text-slate-400 hover:text-white'
              }`}
            >
              <Info className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-[#0a1e20] hover:bg-red-950/60 text-slate-400 hover:text-red-300 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Video Viewport Stage */}
        <div className="relative aspect-video w-full bg-black flex items-center justify-center overflow-hidden">
          <video
            ref={videoRef}
            src={video.stream_url}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={() => setIsPlaying(false)}
            onClick={togglePlayPause}
            className="w-full h-full object-contain cursor-pointer"
            autoPlay
            playsInline
          />

          {/* Range Streaming Video Controls Overlay */}
          <VideoControls
            isPlaying={isPlaying}
            onPlayPause={togglePlayPause}
            currentTime={currentTime}
            duration={duration}
            bufferedEnd={bufferedEnd}
            onSeek={seek}
            playbackRate={playbackRate}
            onRateChange={handleRateChange}
            volume={volume}
            onVolumeChange={handleVolumeChange}
            isMuted={isMuted}
            onToggleMute={toggleMute}
            isFullscreen={isFullscreen}
            onToggleFullscreen={toggleFullscreen}
          />
        </div>

        {/* Technical Telemetry Drawer */}
        {showTelemetry && (
          <div className="px-6 py-4 bg-[#071517] border-t border-[#13373a] grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs font-mono">
            <div>
              <span className="text-slate-500 block uppercase text-[10px]">Resolution</span>
              <span className="text-slate-200 font-medium">
                {video.width && video.height ? `${video.width} x ${video.height}` : 'Standard'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block uppercase text-[10px]">Frame Rate</span>
              <span className="text-[#2dd4bf] font-medium">
                {video.fps ? `${video.fps} FPS` : 'Variable'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block uppercase text-[10px]">Video Codec</span>
              <span className="text-slate-200 font-medium uppercase">
                {video.video_codec || 'H.264'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block uppercase text-[10px]">Audio Codec</span>
              <span className="text-slate-200 font-medium uppercase">
                {video.audio_codec || 'None / Muted'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block uppercase text-[10px]">Bitrate</span>
              <span className="text-slate-200 font-medium">
                {video.bitrate ? `${(video.bitrate / 1000000).toFixed(2)} Mbps` : 'Adaptive'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block uppercase text-[10px]">Storage Engine</span>
              <span className="text-[#2dd4bf] font-medium flex items-center gap-1">
                <Layers className="w-3 h-3" /> MinIO S3
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
