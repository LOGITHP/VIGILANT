import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Shield } from 'lucide-react';

const MainRouter: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#061213] flex flex-col items-center justify-center text-slate-300 select-none">
        <div className="relative mb-4">
          <div className="w-14 h-14 rounded-full border-2 border-[#16383b] border-t-[#15b89a] animate-spin" />
          <Shield className="w-6 h-6 text-[#15b89a] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="font-mono text-xs tracking-widest text-slate-400">
          INITIALIZING VIGILANT PLATFORM...
        </p>
      </div>
    );
  }

  return user ? <Dashboard /> : <Login />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainRouter />
    </AuthProvider>
  );
};

export default App;
