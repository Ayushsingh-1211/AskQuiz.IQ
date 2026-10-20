import { useState, useEffect } from 'react';
import { api, clearToken } from '../api/client';
import { User } from '../api/types';

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(localStorage.getItem('askquiz_token'));
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('askquiz_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = async (email: string, pass: string) => {
    const res = await api.login(email, pass);
    setTokenState(res.access_token);
    setUser(res.user);
    localStorage.setItem('askquiz_user', JSON.stringify(res.user));
    return res;
  };

  const logout = () => {
    clearToken();
    localStorage.removeItem('askquiz_user');
    setTokenState(null);
    setUser(null);
  };

  return { token, user, login, logout, isAuthenticated: !!token };
}
