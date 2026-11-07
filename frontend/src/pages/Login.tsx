import React, { useState } from 'react';
import { Eye, EyeOff, Loader2, AlertCircle, X, ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/BrandLogo';
import cctvCameraAsset from '../assets/cctv-camera.png';

export const Login: React.FC = () => {
  const { login, register, error, clearError } = useAuth();

  // Mode: 'signin' | 'signup'
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');

  // Form states
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [fullName, setFullName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Modals
  const [showForgotModal, setShowForgotModal] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setIsSubmitting(true);

    try {
      if (mode === 'signin') {
        await login({ username, password });
      } else {
        await register({
          email: username,
          password,
          full_name: fullName.trim() || undefined,
        });
      }
    } catch {
      // Error handled by AuthContext
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleMode = () => {
    clearError();
    setMode((prev) => (prev === 'signin' ? 'signup' : 'signin'));
  };

  return (
    <div className="relative min-h-screen w-full bg-[#081818] overflow-hidden flex items-center justify-center p-4 sm:p-6 lg:p-10 font-sans select-none">
      {/* Background Lighting & Ambiance */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_25%_45%,#113735_0%,#081a1a_45%,#040e0e_100%)] pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#15b89a]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-80 h-80 bg-[#0d2a2a]/40 rounded-full blur-2xl pointer-events-none" />

      {/* Main Container Frame */}
      <div className="relative z-10 w-full max-w-[1180px] h-[680px] rounded-3xl border border-[#163638]/60 bg-[#081818]/60 backdrop-blur-sm shadow-[0_25px_70px_rgba(0,0,0,0.85)] flex flex-col justify-between p-8 sm:p-12 overflow-hidden">
        
        {/* Top Header: Brand Identity */}
        <div className="flex items-center justify-between w-full">
          <BrandLogo size="md" />
        </div>

        {/* Content Section: 2 Columns */}
        <div className="flex-1 flex flex-col lg:flex-row items-center justify-between gap-8 my-auto relative">
          
          {/* Left Column: CCTV Camera Showcase */}
          <div className="relative flex-1 w-full flex items-center justify-center lg:justify-start lg:pl-10">
            {/* Ambient Spotlight Ring behind pedestal */}
            <div className="absolute w-72 h-72 sm:w-88 sm:h-88 rounded-full bg-gradient-to-t from-[#15b89a]/20 via-[#0e2929]/10 to-transparent blur-2xl pointer-events-none" />
            
            <div className="relative group transition-transform duration-500 hover:scale-[1.02]">
              <img
                src={cctvCameraAsset}
                alt="VIGILANT AI CCTV Surveillance Camera"
                className="max-h-[360px] sm:max-h-[420px] object-contain drop-shadow-[0_20px_40px_rgba(0,0,0,0.9)]"
              />
            </div>
          </div>

          {/* Right Column: Floating Dark Authentication Card */}
          <div className="w-full lg:w-[380px] shrink-0">
            <div className="relative w-full bg-[#0c1618]/95 border border-[#153133] rounded-[26px] p-8 shadow-[0_20px_50px_rgba(0,0,0,0.7),0_0_30px_rgba(21,184,154,0.06)] backdrop-blur-xl">
              
              {/* Card Title */}
              <h1 className="text-2xl font-medium tracking-wide text-[#15b89a] mb-6">
                {mode === 'signin' ? 'Sign in' : 'Create Account'}
              </h1>

              {/* Error Banner */}
              {error && (
                <div className="mb-5 flex items-start gap-2.5 p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-xs animate-shake">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
                  <div className="flex-1 leading-relaxed">{error}</div>
                  <button
                    onClick={clearError}
                    className="text-red-400 hover:text-red-200 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {mode === 'signup' && (
                  <div>
                    <label className="block text-xs font-normal text-slate-300 mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Operator Name"
                      className="w-full bg-[#f1f6f5] text-slate-900 placeholder:text-slate-400 rounded-lg py-2.5 px-3.5 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-[#15b89a] transition-all"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-normal text-slate-300 mb-1.5">
                    {mode === 'signin' ? 'Username' : 'Email Address'}
                  </label>
                  <input
                    type="email"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="example@gmail.com"
                    autoComplete="username"
                    className="w-full bg-[#f1f6f5] text-slate-900 placeholder:text-slate-400 rounded-lg py-2.5 px-3.5 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-[#15b89a] transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-normal text-slate-300 mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••••••"
                      autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                      className="w-full bg-[#f1f6f5] text-slate-900 placeholder:text-slate-400 rounded-lg py-2.5 pl-3.5 pr-10 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-[#15b89a] transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-800 transition-colors p-1"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Forgot Password Link */}
                {mode === 'signin' && (
                  <div className="flex justify-end pt-0.5">
                    <button
                      type="button"
                      onClick={() => setShowForgotModal(true)}
                      className="text-[11px] text-slate-400 hover:text-[#15b89a] transition-colors"
                    >
                      Forgot Password?
                    </button>
                  </div>
                )}

                {/* Login Button */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full mt-2 bg-[#1ea885] hover:bg-[#1bb891] active:scale-[0.99] text-white py-2.5 rounded-lg font-medium text-sm transition-all duration-200 shadow-md shadow-[#1ea885]/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Authenticating...</span>
                    </>
                  ) : (
                    <span>{mode === 'signin' ? 'Login' : 'Create Account'}</span>
                  )}
                </button>
              </form>

              {/* Bottom Toggle */}
              <div className="mt-8 text-center text-xs text-slate-400">
                {mode === 'signin' ? (
                  <>
                    Dont have an Account?{' '}
                    <button
                      type="button"
                      onClick={toggleMode}
                      className="text-[#19c39e] font-medium hover:underline transition-all ml-1 cursor-pointer"
                    >
                      Sign up
                    </button>
                  </>
                ) : (
                  <>
                    Already have an Account?{' '}
                    <button
                      type="button"
                      onClick={toggleMode}
                      className="text-[#19c39e] font-medium hover:underline transition-all ml-1 cursor-pointer"
                    >
                      Sign in
                    </button>
                  </>
                )}
              </div>

            </div>
          </div>

        </div>

      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-[#0c1618] border border-[#183d3f] rounded-2xl p-6 shadow-2xl text-slate-200">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#153234]">
              <div className="flex items-center gap-2 text-[#19c39e] font-medium">
                <ShieldAlert className="w-5 h-5" />
                <span>Password Recovery Protocol</span>
              </div>
              <button
                onClick={() => setShowForgotModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed mb-4">
              For security compliance in surveillance operations, password resets require authorization.
            </p>
            <div className="bg-[#071314] rounded-lg p-3 border border-[#163032] text-xs font-mono text-slate-400 space-y-1 mb-5">
              <div>Default Superadmin: <span className="text-[#19c39e]">cctv@gmail.com</span></div>
              <div>Master Passcode: <span className="text-[#19c39e]">123456789</span></div>
            </div>
            <button
              onClick={() => setShowForgotModal(false)}
              className="w-full bg-[#1ea885] hover:bg-[#1bb891] text-white py-2 rounded-lg text-xs font-medium"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

