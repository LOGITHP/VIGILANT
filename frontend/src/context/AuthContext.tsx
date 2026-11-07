import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginCredentials, RegisterCredentials, AuthContextType } from '../types/auth';
import { authApi, tokenStorage } from '../services/api';
import axios from 'axios';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(tokenStorage.getUser());
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      const token = tokenStorage.getAccessToken();
      if (token) {
        try {
          const freshUser = await authApi.getMe();
          setUser(freshUser);
        } catch {
          tokenStorage.clear();
          setUser(null);
        }
      }
      setLoading(false);
    };

    const handleExpired = () => {
      setUser(null);
      setError('Your security session has expired. Please sign in again.');
    };

    window.addEventListener('vigilant_auth_expired', handleExpired);
    initAuth();

    return () => {
      window.removeEventListener('vigilant_auth_expired', handleExpired);
    };
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(credentials);
      tokenStorage.setTokens(data);
      setUser(data.user);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Connection failed. Please ensure the VIGILANT service is running.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    setLoading(true);
    setError(null);
    try {
      await authApi.register(credentials);
      // Automatically login after successful registration
      await login({
        username: credentials.email,
        password: credentials.password
      });
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Registration failed. Please verify your details.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authApi.logout();
    } catch (e) {
      console.warn('Logout error ignored:', e);
    } finally {
      tokenStorage.clear();
      setUser(null);
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

