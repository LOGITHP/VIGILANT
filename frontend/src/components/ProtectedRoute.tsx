import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, fallback }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#061313] flex flex-col items-center justify-center text-slate-300">
        <div className="relative mb-4">
          <div className="w-14 h-14 rounded-full border-2 border-vigilant-border border-t-vigilant-teal animate-spin" />
          <Shield className="w-6 h-6 text-vigilant-teal absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="font-mono text-sm tracking-widest text-vigilant-muted">
          INITIALIZING SECURITY SESSION...
        </p>
      </div>
    );
  }

  if (!user) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
