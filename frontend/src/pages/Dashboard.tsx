import React, { useState, useEffect } from 'react';
import {
  Video as VideoIcon,
  VideoOff,
  LogOut,
  Activity,
  Cpu,
  HardDrive,
  Plus,
  Clock,
  CheckCircle2,
  X,
  Camera,
  Archive,
  UploadCloud,
  Monitor
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/BrandLogo';
import { Video } from '../types/video';
import { VideoLibrary } from '../components/video/VideoLibrary';
import { UploadCenter } from '../components/video/UploadCenter';
import { VideoPlayerModal } from '../components/video/VideoPlayerModal';

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  // Active Tab: 'live' | 'archive' | 'upload'
  const [activeTab, setActiveTab] = useState<'live' | 'archive' | 'upload'>('live');

  // Active playing video modal
  const [activeVideo, setActiveVideo] = useState<Video | null>(null);

  // Clock
  const [currentTime, setCurrentTime] = useState<string>('');
  const [utcTime, setUtcTime] = useState<string>('');

  // Modal for Live Stream Connect
  const [showAddModal, setShowAddModal] = useState(false);
  const [streamName, setStreamName] = useState('');
  const [streamUrl, setStreamUrl] = useState('');
  const [protocol, setProtocol] = useState('RTSP');
  const [addNotice, setAddNotice] = useState<string | null>(null);

  useEffect(() => {
    const updateTimes = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString());
      setUtcTime(now.toUTCString().slice(17, 25) + ' UTC');
    };
    updateTimes();
    const timer = setInterval(updateTimes, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleConnectStream = (e: React.FormEvent) => {
    e.preventDefault();
    setAddNotice(`Feed configuration "${streamName || 'Camera 01'}" registered. Ready for pipeline ingestion.`);
    setTimeout(() => {
      setShowAddModal(false);
      setAddNotice(null);
      setStreamName('');
      setStreamUrl('');
    }, 1800);
  };

  return (
    <div className="min-h-screen bg-[#061213] text-slate-200 flex flex-col font-sans select-none">
      
      {/* Top Surveillance Navigation Bar */}
      <header className="sticky top-0 z-30 bg-[#081819]/90 border-b border-[#143234] backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <BrandLogo size="md" />
          <div className="h-5 w-[1px] bg-[#1a3f42] hidden sm:block" />
          <div className="hidden sm:flex flex-col">
            <span className="text-[11px] font-mono tracking-widest text-[#15b89a] uppercase">
              AI CCTV Intelligence Platform
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              SURVEILLANCE NODE #01
            </span>
          </div>
        </div>

        {/* Center Navigation Tabs */}
        <div className="flex items-center gap-1.5 bg-[#091718] p-1 rounded-2xl border border-[#16383b]">
          <button
            onClick={() => setActiveTab('live')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-mono transition-all ${
              activeTab === 'live'
                ? 'bg-[#15b89a] text-slate-950 font-semibold shadow-[0_0_15px_rgba(21,184,154,0.35)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Monitor className="w-3.5 h-3.5" />
            <span>LIVE CCTV</span>
          </button>

          <button
            onClick={() => setActiveTab('archive')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-mono transition-all ${
              activeTab === 'archive'
                ? 'bg-[#15b89a] text-slate-950 font-semibold shadow-[0_0_15px_rgba(21,184,154,0.35)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Archive className="w-3.5 h-3.5" />
            <span>VIDEO ARCHIVE</span>
          </button>

          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-mono transition-all ${
              activeTab === 'upload'
                ? 'bg-[#15b89a] text-slate-950 font-semibold shadow-[0_0_15px_rgba(21,184,154,0.35)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>UPLOAD CENTER</span>
          </button>
        </div>

        {/* Center Live Telemetry */}
        <div className="hidden xl:flex items-center gap-6 bg-[#0c1e20] px-4 py-1.5 rounded-full border border-[#16383b] text-xs font-mono">
          <div className="flex items-center gap-2 text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="tracking-wide text-[11px]">SYS ONLINE</span>
          </div>
          <div className="h-3 w-[1px] bg-[#1a3e40]" />
          <div className="flex items-center gap-1.5 text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span className="text-[11px]">{currentTime}</span>
            <span className="text-[10px] text-slate-500">({utcTime})</span>
          </div>
        </div>

        {/* Right Section: User & Logout */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5 bg-[#0b1b1d] px-3 py-1.5 rounded-xl border border-[#16393b]">
            <div className="w-7 h-7 rounded-lg bg-[#15b89a]/20 border border-[#15b89a]/40 flex items-center justify-center text-[#15b89a] font-semibold text-xs">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-medium text-slate-200 truncate max-w-[130px]">
                {user?.full_name || user?.email}
              </span>
              <span className="text-[10px] text-[#2dd4bf] font-mono">
                {user?.roles?.[0] || 'OPERATOR'}
              </span>
            </div>
          </div>

          <button
            onClick={logout}
            title="Terminate Session"
            className="p-2 rounded-xl bg-[#0c1b1c] hover:bg-red-950/40 border border-[#16383b] hover:border-red-800/60 text-slate-400 hover:text-red-400 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        
        {/* TAB 1: Live CCTV Streams */}
        {activeTab === 'live' && (
          <>
            {/* Telemetry Metrics Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-[#0b1b1d]/80 border border-[#163638] rounded-2xl p-4 flex items-center justify-between shadow-lg">
                <div>
                  <span className="text-xs text-slate-400 font-mono uppercase tracking-wider block mb-1">
                    Active Video Streams
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-semibold text-slate-100 font-mono">0</span>
                    <span className="text-xs text-slate-500 font-mono">/ 16 MAX</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#0e2729] border border-[#194042] flex items-center justify-center text-[#15b89a]">
                  <VideoIcon className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-[#0b1b1d]/80 border border-[#163638] rounded-2xl p-4 flex items-center justify-between shadow-lg">
                <div>
                  <span className="text-xs text-slate-400 font-mono uppercase tracking-wider block mb-1">
                    AI Detection Engine
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-semibold text-[#2dd4bf] font-mono">STANDBY</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#0e2729] border border-[#194042] flex items-center justify-center text-[#2dd4bf]">
                  <Cpu className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-[#0b1b1d]/80 border border-[#163638] rounded-2xl p-4 flex items-center justify-between shadow-lg">
                <div>
                  <span className="text-xs text-slate-400 font-mono uppercase tracking-wider block mb-1">
                    MinIO Object Storage
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-semibold text-emerald-400 font-mono">CONNECTED</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#0e2729] border border-[#194042] flex items-center justify-center text-emerald-400">
                  <HardDrive className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-[#0b1b1d]/80 border border-[#163638] rounded-2xl p-4 flex items-center justify-between shadow-lg">
                <div>
                  <span className="text-xs text-slate-400 font-mono uppercase tracking-wider block mb-1">
                    Network Latency
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-semibold text-emerald-400 font-mono">&lt; 1</span>
                    <span className="text-xs text-slate-500 font-mono">ms (Local)</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#0e2729] border border-[#194042] flex items-center justify-center text-emerald-400">
                  <Activity className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Video Streams Section Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
              <div>
                <h2 className="text-lg font-medium text-slate-100 tracking-wide">
                  Live CCTV Surveillance Grid
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Real-time multi-channel surveillance feeds and computer vision overlay.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowAddModal(true)}
                  className="px-4 py-2 rounded-xl bg-[#15b89a] hover:bg-[#2dd4bf] text-slate-950 font-semibold text-xs flex items-center gap-2 shadow-[0_0_20px_rgba(21,184,154,0.3)] transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Connect Camera Feed
                </button>
              </div>
            </div>

            {/* Empty Streams Grid State */}
            <div className="border border-dashed border-[#16393b] rounded-3xl p-16 text-center bg-[#071517]/50 flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-[#0c2224] border border-[#1b484b] flex items-center justify-center text-slate-500 mb-4">
                <VideoOff className="w-8 h-8 opacity-60" />
              </div>
              <h3 className="text-lg font-medium text-slate-200 mb-1">
                No Active Surveillance Feeds Connected
              </h3>
              <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
                Connect your IP cameras via RTSP/ONVIF streams, or switch to the{' '}
                <button
                  onClick={() => setActiveTab('upload')}
                  className="text-[#2dd4bf] underline hover:text-white"
                >
                  Upload Center
                </button>{' '}
                to ingest recorded surveillance video archives.
              </p>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-5 py-2.5 rounded-xl bg-[#0e2a2c] hover:bg-[#133c3f] border border-[#1b4b4e] text-[#2dd4bf] text-xs font-semibold flex items-center gap-2 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Register New Camera Stream
              </button>
            </div>
          </>
        )}

        {/* TAB 2: Video Archive Library */}
        {activeTab === 'archive' && (
          <VideoLibrary
            onPlayVideo={(video) => setActiveVideo(video)}
            onNavigateToUpload={() => setActiveTab('upload')}
          />
        )}

        {/* TAB 3: Upload Center */}
        {activeTab === 'upload' && (
          <UploadCenter onUploadComplete={() => {}} />
        )}

      </main>

      {/* Video Player Modal (Triggerable from any tab) */}
      <VideoPlayerModal
        video={activeVideo}
        onClose={() => setActiveVideo(null)}
      />

      {/* Add Camera Stream Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0a1819] border border-[#153a3d] rounded-3xl p-6 shadow-2xl relative">
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-[#0e2729] border border-[#1b494d] flex items-center justify-center text-[#15b89a]">
                <Camera className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-medium text-slate-100">Connect Camera Stream</h3>
                <p className="text-xs text-slate-400">Configure RTSP or HTTP camera pipeline</p>
              </div>
            </div>

            {addNotice ? (
              <div className="py-6 text-center text-xs text-emerald-400 flex flex-col items-center gap-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 animate-bounce" />
                <span>{addNotice}</span>
              </div>
            ) : (
              <form onSubmit={handleConnectStream} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Camera Name / Identifier
                  </label>
                  <input
                    type="text"
                    required
                    value={streamName}
                    onChange={(e) => setStreamName(e.target.value)}
                    placeholder="e.g. CAM-01 • North Entrance"
                    className="w-full bg-[#061112] border border-[#16383b] rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-[#15b89a]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Stream Protocol
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {['RTSP', 'WebRTC', 'HTTP-FLV'].map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setProtocol(p)}
                        className={`py-1.5 text-xs rounded-lg border font-mono transition-colors ${
                          protocol === p
                            ? 'bg-[#15b89a]/20 border-[#15b89a] text-[#2dd4bf]'
                            : 'bg-[#061112] border-[#16383b] text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Stream URL / Target Endpoint
                  </label>
                  <input
                    type="text"
                    required
                    value={streamUrl}
                    onChange={(e) => setStreamUrl(e.target.value)}
                    placeholder="rtsp://admin:pass@192.168.1.100:554/live"
                    className="w-full bg-[#061112] border border-[#16383b] rounded-xl px-3.5 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-[#15b89a]"
                  />
                </div>

                <div className="pt-2 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-[#15b89a] hover:bg-[#2dd4bf] text-slate-950 font-semibold text-xs transition-colors"
                  >
                    Connect Stream
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
};
