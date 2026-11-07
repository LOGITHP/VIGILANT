import React, { useState, useEffect } from 'react';
import {
  Video,
  VideoOff,
  LogOut,
  Shield,
  Activity,
  Cpu,
  HardDrive,
  Plus,
  Radio,
  Clock,
  Layers,
  CheckCircle2,
  X,
  Camera
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/BrandLogo';

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  // Clock
  const [currentTime, setCurrentTime] = useState<string>('');
  const [utcTime, setUtcTime] = useState<string>('');

  // Modal
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

        {/* Center Live Telemetry */}
        <div className="hidden md:flex items-center gap-6 bg-[#0c1e20] px-4 py-1.5 rounded-full border border-[#16383b] text-xs font-mono">
          <div className="flex items-center gap-2 text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="tracking-wide text-[11px]">SYS ONLINE</span>
          </div>
          <div className="h-3 w-[1px] bg-[#1a3e40]" />
          <div className="flex items-center gap-2 text-[#2dd4bf]">
            <Cpu className="w-3.5 h-3.5" />
            <span className="text-[11px]">AI ENGINE: STANDBY</span>
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
              {user?.email ? user.email.slice(0, 2).toUpperCase() : 'OP'}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-slate-200 leading-tight">
                {user?.email}
              </span>
              <div className="flex items-center gap-1">
                <span className="text-[10px] font-mono text-[#19c39e] uppercase font-semibold">
                  {user?.roles?.length ? user.roles[0] : (user?.is_superuser ? 'SUPERADMIN' : 'OPERATOR')}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={logout}
            className="flex items-center gap-1.5 bg-[#122b2d] hover:bg-red-950/40 hover:text-red-400 hover:border-red-900/60 border border-[#193f42] text-slate-300 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer"
            title="Logout from session"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto flex flex-col gap-6">
        
        {/* Metric Cards Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[#0b191a] border border-[#143436] rounded-2xl p-4 flex items-center justify-between shadow-lg shadow-black/40">
            <div>
              <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Active Cameras</p>
              <p className="text-2xl font-bold text-slate-100 font-mono mt-1">0 <span className="text-xs text-slate-500 font-normal">/ 64</span></p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#143234]/60 flex items-center justify-center text-[#15b89a]">
              <Video className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-[#0b191a] border border-[#143436] rounded-2xl p-4 flex items-center justify-between shadow-lg shadow-black/40">
            <div>
              <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">AI Detections (24h)</p>
              <p className="text-2xl font-bold text-slate-100 font-mono mt-1">0</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#143234]/60 flex items-center justify-center text-[#2dd4bf]">
              <Activity className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-[#0b191a] border border-[#143436] rounded-2xl p-4 flex items-center justify-between shadow-lg shadow-black/40">
            <div>
              <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Neural Latency</p>
              <p className="text-2xl font-bold text-slate-100 font-mono mt-1">0.0 <span className="text-xs text-slate-500 font-normal">ms</span></p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#143234]/60 flex items-center justify-center text-[#15b89a]">
              <Cpu className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-[#0b191a] border border-[#143436] rounded-2xl p-4 flex items-center justify-between shadow-lg shadow-black/40">
            <div>
              <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Storage Allocated</p>
              <p className="text-2xl font-bold text-slate-100 font-mono mt-1">0.0 <span className="text-xs text-slate-500 font-normal">GB</span></p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#143234]/60 flex items-center justify-center text-slate-400">
              <HardDrive className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Central Surveillance Viewport Area (Empty State) */}
        <div className="flex-1 min-h-[460px] bg-[#091516] border border-[#143234] rounded-3xl p-8 flex flex-col items-center justify-center relative overflow-hidden shadow-2xl shadow-black/60">
          
          {/* Subtle Grid crosshairs & surveillance raster effect */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#0d2526_1px,transparent_1px),linear-gradient(to_bottom,#0d2526_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-40 pointer-events-none" />

          {/* Corner camera viewport brackets */}
          <div className="absolute top-6 left-6 w-8 h-8 border-t-2 border-l-2 border-[#19c39e]/40 pointer-events-none" />
          <div className="absolute top-6 right-6 w-8 h-8 border-t-2 border-r-2 border-[#19c39e]/40 pointer-events-none" />
          <div className="absolute bottom-6 left-6 w-8 h-8 border-b-2 border-l-2 border-[#19c39e]/40 pointer-events-none" />
          <div className="absolute bottom-6 right-6 w-8 h-8 border-b-2 border-r-2 border-[#19c39e]/40 pointer-events-none" />

          {/* Main Empty State Content */}
          <div className="relative z-10 max-w-md text-center flex flex-col items-center">
            
            <div className="relative mb-6">
              <div className="w-20 h-20 rounded-3xl bg-[#0e2728] border border-[#194b4e] flex items-center justify-center text-[#15b89a] shadow-xl shadow-black/60">
                <VideoOff className="w-10 h-10 text-[#15b89a]/80" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-[#15b89a] text-black flex items-center justify-center text-xs font-bold">
                0
              </div>
            </div>

            <h2 className="text-xl font-semibold tracking-wide text-slate-100 mb-2 font-mono">
              NO ACTIVE CCTV FEEDS CONNECTED
            </h2>

            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Connect your first RTSP, ONVIF, or WebRTC IP camera feed to activate automated neural surveillance, object tracking, boundary intrusion detection, and real-time alert dispatching.
            </p>

            <div className="flex flex-col sm:flex-row items-center gap-3 w-full justify-center">
              <button
                onClick={() => setShowAddModal(true)}
                className="w-full sm:w-auto bg-[#1ea885] hover:bg-[#1bb891] text-white px-5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all shadow-lg shadow-[#1ea885]/20 flex items-center justify-center gap-2 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Connect Camera Feed</span>
              </button>

              <button
                onClick={() => alert("Audit log telemetry is actively recording in PostgreSQL.")}
                className="w-full sm:w-auto bg-[#0d2325] hover:bg-[#122e30] border border-[#163a3d] text-slate-300 px-4 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <Shield className="w-4 h-4 text-[#15b89a]" />
                <span>Security Audit Logs</span>
              </button>
            </div>

            <div className="mt-8 flex items-center gap-4 text-[11px] font-mono text-slate-500">
              <span className="flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-slate-400" /> RTSP / H.264 / H.265
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" /> YOLO Neural Pipeline Ready
              </span>
            </div>

          </div>

        </div>

      </main>

      {/* Connect Camera Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-[#0c181a] border border-[#173b3e] rounded-3xl p-6 shadow-2xl text-slate-200">
            <div className="flex items-center justify-between mb-5 pb-3 border-b border-[#143234]">
              <div className="flex items-center gap-2.5 text-[#15b89a] font-semibold">
                <Camera className="w-5 h-5" />
                <span>Connect New Camera Stream</span>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {addNotice ? (
              <div className="py-8 flex flex-col items-center justify-center text-center">
                <CheckCircle2 className="w-12 h-12 text-[#15b89a] mb-3 animate-bounce" />
                <p className="text-sm font-medium text-slate-200">{addNotice}</p>
              </div>
            ) : (
              <form onSubmit={handleConnectStream} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Camera Display Name
                  </label>
                  <input
                    type="text"
                    required
                    value={streamName}
                    onChange={(e) => setStreamName(e.target.value)}
                    placeholder="e.g. Gate 1 - North Entrance PTZ"
                    className="w-full bg-[#081314] border border-[#153436] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-[#15b89a]"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Protocol
                    </label>
                    <select
                      value={protocol}
                      onChange={(e) => setProtocol(e.target.value)}
                      className="w-full bg-[#081314] border border-[#153436] rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-[#15b89a]"
                    >
                      <option value="RTSP">RTSP</option>
                      <option value="ONVIF">ONVIF</option>
                      <option value="WebRTC">WebRTC</option>
                      <option value="HLS">HLS</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Stream URI / Endpoint
                    </label>
                    <input
                      type="text"
                      required
                      value={streamUrl}
                      onChange={(e) => setStreamUrl(e.target.value)}
                      placeholder="rtsp://admin:pass@192.168.1.100:554/live"
                      className="w-full bg-[#081314] border border-[#153436] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-[#15b89a]"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#071314] border border-[#153032] text-[11px] text-slate-400">
                  <span className="text-[#15b89a] font-semibold">AI Surveillance Pipeline:</span> Once connected, frames will automatically route to the background neural engine for real-time person, vehicle, and perimeter anomaly analysis.
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#143234]">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-[#1ea885] hover:bg-[#1bb891] text-white px-5 py-2 rounded-xl text-xs font-semibold"
                  >
                    Register Stream
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
