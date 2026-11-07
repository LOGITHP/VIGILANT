import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Film,
  Volume2,
  VolumeX,
  Layers,
  Cpu,
  HardDrive,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Code2,
  Hourglass
} from 'lucide-react';
import { Video, VideoInspectionReport } from '../../types/video';
import { videoApi } from '../../services/videoApi';

interface VideoInspectionDrawerProps {
  video: Video | null;
  isOpen: boolean;
  onClose: () => void;
}

export const VideoInspectionDrawer: React.FC<VideoInspectionDrawerProps> = ({
  video,
  isOpen,
  onClose,
}) => {
  const [report, setReport] = useState<VideoInspectionReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'container' | 'video' | 'audio' | 'streams' | 'raw'>('overview');

  const fetchInspection = async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await videoApi.getInspectionReport(id);
      setReport(data);
    } catch (err: unknown) {
      setError('Media inspection report not available or processing is still in progress.');
      setReport(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && video) {
      fetchInspection(video.id);
      setActiveTab('overview');
    } else {
      setReport(null);
      setError(null);
    }
  }, [isOpen, video]);

  const handleTriggerInspection = async () => {
    if (!video) return;
    setIsRefreshing(true);
    try {
      await videoApi.triggerInspection(video.id);
      setTimeout(() => {
        fetchInspection(video.id);
        setIsRefreshing(false);
      }, 2500);
    } catch (err) {
      setIsRefreshing(false);
      alert('Failed to trigger inspection.');
    }
  };

  if (!isOpen || !video) return null;

  const formatBytes = (bytes?: number | null) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDuration = (seconds?: number | null) => {
    if (!seconds) return '--:--';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = (seconds % 60).toFixed(2);
    if (hrs > 0) {
      return `${hrs}h ${mins}m ${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-5xl max-h-[92vh] bg-[#071315] border border-[#164346] rounded-3xl shadow-[0_25px_60px_rgba(0,0,0,0.8),0_0_35px_rgba(21,184,154,0.15)] flex flex-col overflow-hidden text-slate-200">
        
        {/* Header Bar */}
        <div className="px-6 py-4.5 border-b border-[#13373a] bg-[#091b1d]/90 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#0e2a2c] border border-[#1b4b4e] flex items-center justify-center text-[#2dd4bf]">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-semibold text-slate-100 tracking-wide line-clamp-1">
                  {video.title}
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0b2426] text-[#2dd4bf] border border-[#17464a]">
                  INSPECTION MANIFEST (3.1.1)
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                UUID: {video.id}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleTriggerInspection}
              disabled={isRefreshing}
              className="px-3 py-1.5 rounded-xl bg-[#0e2a2c] hover:bg-[#143d40] border border-[#1b4b4e] text-xs font-mono text-[#2dd4bf] flex items-center gap-1.5 transition-colors disabled:opacity-50"
              title="Re-run FFprobe subprocess extraction"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>{isRefreshing ? 'Re-inspecting...' : 'Re-probe'}</span>
            </button>

            <button
              onClick={onClose}
              className="w-9 h-9 rounded-xl bg-[#0b2224] hover:bg-[#123639] border border-[#164144] flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Dual Status Banner */}
        <div className="px-6 py-3 bg-[#050e0f] border-b border-[#113133] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-4 flex-wrap">
            {/* Metadata Extraction Status */}
            <div className="flex items-center gap-2">
              <span className="text-slate-500 uppercase text-[11px]">Metadata Status:</span>
              {report?.metadata_status === 'COMPLETED' ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/70 font-semibold text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  EXTRACTED (v{report.extractor_version})
                </span>
              ) : report?.metadata_status === 'FAILED' ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-950/80 text-red-300 border border-red-800 font-semibold text-[11px]">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  EXTRACTION FAILED
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800 font-semibold text-[11px]">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  PROBING CONTAINER
                </span>
              )}
            </div>

            {/* Media Decode Validation Status (Crucial Separation!) */}
            <div className="flex items-center gap-2">
              <span className="text-slate-500 uppercase text-[11px]">Media Validation:</span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-950/70 text-amber-300 border border-amber-800/60 font-semibold text-[11px]">
                <Hourglass className="w-3.5 h-3.5" />
                PENDING (Phase 3.1.2 Decode Pass)
              </span>
            </div>
          </div>

          <div className="text-[11px] text-slate-500">
            Source: <span className="text-slate-300 font-semibold">{video.source_type}</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 pt-3 bg-[#081819] border-b border-[#123134] flex items-center gap-2 overflow-x-auto">
          {[
            { id: 'overview', label: '1. Overview', icon: FileText },
            { id: 'container', label: '2. File & Container', icon: HardDrive },
            { id: 'video', label: '3. Primary Video Stream', icon: Film },
            { id: 'audio', label: '4. Audio Stream', icon: Volume2 },
            { id: 'streams', label: '5. Stream Catalog', icon: Layers },
            { id: 'raw', label: 'Raw FFprobe JSON', icon: Code2 },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 text-xs font-mono transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-[#15b89a] text-[#2dd4bf] font-semibold bg-[#0c2426]/50'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading && (
            <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
              <Loader2 className="w-8 h-8 text-[#2dd4bf] animate-spin" />
              <p className="text-xs font-mono tracking-widest uppercase">Executing Subprocess FFprobe Inspection...</p>
            </div>
          )}

          {error && !isLoading && (
            <div className="p-6 rounded-2xl bg-red-950/40 border border-red-800 text-red-200 flex flex-col items-center text-center gap-3">
              <AlertTriangle className="w-8 h-8 text-red-400" />
              <p className="text-sm font-medium">{error}</p>
              <button
                onClick={handleTriggerInspection}
                className="mt-2 px-4 py-2 rounded-xl bg-red-900/60 hover:bg-red-800 text-white text-xs font-mono transition-colors"
              >
                Trigger Inspection Now
              </button>
            </div>
          )}

          {report && !isLoading && (
            <>
              {/* TAB 1: OVERVIEW */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-[#091a1c] border border-[#14373a] rounded-2xl p-4">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Resolution</span>
                      <span className="text-xl font-bold font-mono text-[#2dd4bf]">
                        {report.video_stream ? `${report.video_stream.width}×${report.video_stream.height}` : 'N/A'}
                      </span>
                    </div>

                    <div className="bg-[#091a1c] border border-[#14373a] rounded-2xl p-4">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Frame Rate</span>
                      <span className="text-xl font-bold font-mono text-emerald-400">
                        {report.video_stream?.fps ? `${report.video_stream.fps} FPS` : 'N/A'}
                      </span>
                    </div>

                    <div className="bg-[#091a1c] border border-[#14373a] rounded-2xl p-4">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Duration</span>
                      <span className="text-xl font-bold font-mono text-slate-100">
                        {formatDuration(report.container_info.duration_seconds)}
                      </span>
                    </div>

                    <div className="bg-[#091a1c] border border-[#14373a] rounded-2xl p-4">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-1">Total Streams</span>
                      <span className="text-xl font-bold font-mono text-indigo-300">
                        {report.all_streams.length}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="bg-[#09191b] border border-[#13383a] rounded-2xl p-5 space-y-3">
                      <h4 className="text-xs font-mono uppercase tracking-wider text-[#15b89a] font-semibold flex items-center gap-2">
                        <Film className="w-4 h-4" /> Primary Video Stream (Stream #{report.video_stream?.stream_index ?? 0})
                      </h4>
                      <div className="space-y-2 text-xs font-mono">
                        <div className="flex justify-between py-1 border-b border-[#122e30]">
                          <span className="text-slate-400">Codec:</span>
                          <span className="text-slate-100 uppercase font-semibold">{report.video_stream?.codec_name || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-[#122e30]">
                          <span className="text-slate-400">Pixel Format:</span>
                          <span className="text-slate-200">{report.video_stream?.pixel_format || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-[#122e30]">
                          <span className="text-slate-400">Time Base:</span>
                          <span className="text-slate-200">{report.video_stream?.time_base || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-[#122e30]">
                          <span className="text-slate-400">Rational FPS:</span>
                          <span className="text-[#2dd4bf]">{report.video_stream?.rational_fps || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between py-1">
                          <span className="text-slate-400">Reported Frame Count:</span>
                          <span className="text-slate-200">{report.video_stream?.reported_frame_count?.toLocaleString() || 'N/A (Header unpopulated)'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-[#09191b] border border-[#13383a] rounded-2xl p-5 space-y-3">
                      <h4 className="text-xs font-mono uppercase tracking-wider text-[#15b89a] font-semibold flex items-center gap-2">
                        {report.audio_stream.has_audio ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                        Primary Audio Stream
                      </h4>
                      {report.audio_stream.has_audio ? (
                        <div className="space-y-2 text-xs font-mono">
                          <div className="flex justify-between py-1 border-b border-[#122e30]">
                            <span className="text-slate-400">Audio Codec:</span>
                            <span className="text-slate-100 uppercase font-semibold">{report.audio_stream.codec_name}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[#122e30]">
                            <span className="text-slate-400">Sample Rate:</span>
                            <span className="text-slate-200">{report.audio_stream.sample_rate?.toLocaleString()} Hz</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[#122e30]">
                            <span className="text-slate-400">Channels:</span>
                            <span className="text-slate-200">{report.audio_stream.channels} ({report.audio_stream.channel_layout})</span>
                          </div>
                          <div className="flex justify-between py-1">
                            <span className="text-slate-400">Stream Duration:</span>
                            <span className="text-slate-200">{formatDuration(report.audio_stream.duration_seconds)}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="py-6 text-center text-slate-500 font-mono text-xs">
                          No audio stream present (Silent surveillance stream)
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: FILE & CONTAINER */}
              {activeTab === 'container' && (
                <div className="space-y-5">
                  <div className="bg-[#09191b] border border-[#13383a] rounded-2xl p-5 space-y-4">
                    <h3 className="text-xs font-mono uppercase tracking-wider text-[#15b89a] font-semibold">
                      Category A: File Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Original Filename:</span>
                        <span className="text-slate-200 break-all">{report.file_info.original_filename}</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Physical File Size:</span>
                        <span className="text-slate-200">{formatBytes(report.file_info.file_size)} ({report.file_info.file_size.toLocaleString()} bytes)</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30] md:col-span-2">
                        <span className="text-slate-500 block mb-1">SHA-256 Checksum:</span>
                        <span className="text-[#2dd4bf] font-mono break-all text-[11px]">{report.file_info.sha256_checksum || 'N/A'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-[#09191b] border border-[#13383a] rounded-2xl p-5 space-y-4">
                    <h3 className="text-xs font-mono uppercase tracking-wider text-[#15b89a] font-semibold">
                      Category B: Container Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Container Format:</span>
                        <span className="text-slate-100 font-semibold uppercase">{report.container_info.format_name}</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Format Long Name:</span>
                        <span className="text-slate-200">{report.container_info.format_long_name}</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Container Duration:</span>
                        <span className="text-slate-200">{report.container_info.duration_seconds?.toFixed(3)}s</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Average Bitrate:</span>
                        <span className="text-slate-200">{report.container_info.bitrate ? `${(report.container_info.bitrate / 1000).toFixed(0)} kbps` : 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: PRIMARY VIDEO */}
              {activeTab === 'video' && report.video_stream && (
                <div className="bg-[#09191b] border border-[#13383a] rounded-2xl p-5 space-y-4">
                  <h3 className="text-xs font-mono uppercase tracking-wider text-[#15b89a] font-semibold">
                    Category C: Primary Video Stream Details (Stream #{report.video_stream.stream_index})
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs font-mono">
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Codec:</span>
                      <span className="text-slate-100 uppercase font-semibold">{report.video_stream.codec_name}</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Resolution:</span>
                      <span className="text-[#2dd4bf] font-bold">{report.video_stream.width} × {report.video_stream.height}</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Evaluated Frame Rate:</span>
                      <span className="text-emerald-400 font-semibold">{report.video_stream.fps} FPS</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Exact Rational FPS:</span>
                      <span className="text-slate-200">{report.video_stream.rational_fps}</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Pixel Representation:</span>
                      <span className="text-slate-200">{report.video_stream.pixel_format}</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Stream Time Base:</span>
                      <span className="text-slate-200">{report.video_stream.time_base}</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Stream Start Timestamp:</span>
                      <span className="text-slate-200">{report.video_stream.start_timestamp ?? '0.000'}s</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Reported Frames:</span>
                      <span className="text-slate-200">{report.video_stream.reported_frame_count ?? 'Unspecified'}</span>
                    </div>
                    <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                      <span className="text-slate-500 block mb-1">Full Codec Designation:</span>
                      <span className="text-slate-300 truncate block">{report.video_stream.codec_long_name}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: AUDIO */}
              {activeTab === 'audio' && (
                <div className="bg-[#09191b] border border-[#13383a] rounded-2xl p-5 space-y-4">
                  <h3 className="text-xs font-mono uppercase tracking-wider text-[#15b89a] font-semibold">
                    Category D: Audio Stream Details
                  </h3>
                  {report.audio_stream.has_audio ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs font-mono">
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Audio Stream Index:</span>
                        <span className="text-slate-100 font-semibold">#{report.audio_stream.stream_index}</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Audio Codec:</span>
                        <span className="text-slate-100 uppercase font-semibold">{report.audio_stream.codec_name}</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Sample Rate:</span>
                        <span className="text-[#2dd4bf]">{report.audio_stream.sample_rate?.toLocaleString()} Hz</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Channels & Layout:</span>
                        <span className="text-slate-200">{report.audio_stream.channels} ({report.audio_stream.channel_layout})</span>
                      </div>
                      <div className="p-3 bg-[#061214] rounded-xl border border-[#122e30]">
                        <span className="text-slate-500 block mb-1">Audio Duration:</span>
                        <span className="text-slate-200">{report.audio_stream.duration_seconds?.toFixed(3)}s</span>
                      </div>
                    </div>
                  ) : (
                    <div className="p-12 text-center text-slate-500 font-mono text-xs border border-dashed border-[#14373a] rounded-2xl">
                      No audio stream was detected in this surveillance video file.
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: STREAM CATALOG */}
              {activeTab === 'streams' && (
                <div className="space-y-4">
                  <div className="overflow-x-auto rounded-2xl border border-[#14373a] bg-[#09191b]">
                    <table className="w-full text-left border-collapse text-xs font-mono">
                      <thead>
                        <tr className="border-b border-[#14373a] bg-[#061214] text-[11px] text-slate-400 uppercase tracking-wider">
                          <th className="py-3 px-4">Index</th>
                          <th className="py-3 px-4">Type</th>
                          <th className="py-3 px-4">Codec</th>
                          <th className="py-3 px-4">Resolution / Rate</th>
                          <th className="py-3 px-4">Flags</th>
                          <th className="py-3 px-4">Time Base</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#122e30]">
                        {report.all_streams.map((s) => (
                          <tr key={s.stream_index} className="hover:bg-[#0c2426]/50 transition-colors">
                            <td className="py-3 px-4 font-bold text-slate-100">#{s.stream_index}</td>
                            <td className="py-3 px-4 uppercase text-[#2dd4bf] font-semibold">{s.stream_type}</td>
                            <td className="py-3 px-4 uppercase text-slate-200">{s.codec_name}</td>
                            <td className="py-3 px-4 text-slate-300">
                              {s.stream_type === 'video' ? `${s.width}×${s.height} @ ${s.fps || '--'} FPS` : `${s.sample_rate?.toLocaleString() || '--'} Hz`}
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                {s.is_primary && (
                                  <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px]">
                                    PRIMARY
                                  </span>
                                )}
                                {s.is_default && (
                                  <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px]">
                                    DEFAULT
                                  </span>
                                )}
                                {s.is_attached_pic && (
                                  <span className="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px]">
                                    COVER ART
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-4 text-slate-400">{s.time_base || '--'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 6: RAW FFPROBE JSON */}
              {activeTab === 'raw' && (
                <div className="bg-[#050e0f] border border-[#14373a] rounded-2xl p-4 overflow-x-auto max-h-[500px]">
                  <pre className="text-[11px] font-mono text-emerald-300 leading-relaxed">
                    {JSON.stringify(report.raw_metadata || {}, null, 2)}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>

      </div>
    </div>
  );
};
