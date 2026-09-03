'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { User, UserRole } from '@/types';
import { api } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  isInspector: boolean;
  isSupervisor: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedUserData = localStorage.getItem('user_data');

    if (savedToken) {
      setToken(savedToken);
      if (savedUserData) {
        try {
          setUser(JSON.parse(savedUserData));
        } catch {
          // ignore corrupted json
        }
      }
      // Re-validate against backend
      api.getMe()
        .then((userData) => {
          setUser(userData);
          localStorage.setItem('user_data', JSON.stringify(userData));
        })
        .catch(() => {
          logout();
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, pass: string) => {
    setLoading(true);
    try {
      const { access_token } = await api.login(email, pass);
      localStorage.setItem('access_token', access_token);
      setToken(access_token);

      const userData = await api.getMe();
      localStorage.setItem('user_data', JSON.stringify(userData));
      setUser(userData);

      // Role-based routing
      if (userData.role === 'INSPECTOR') {
        router.push('/inspections');
      } else {
        router.push('/analytics');
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    setUser(null);
    setToken(null);
    router.push('/login');
  };

  const isInspector = user?.role === 'INSPECTOR';
  const isSupervisor = user?.role === 'SUPERVISOR' || user?.role === 'ADMIN';
  const isAdmin = user?.role === 'ADMIN';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isInspector,
        isSupervisor,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

