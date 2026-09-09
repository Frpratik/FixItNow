import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('fixitnow_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('fixitnow_access_token'));
  const [loading, setLoading] = useState(false);

  const saveAuthData = (data) => {
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('fixitnow_access_token', data.access_token);
    localStorage.setItem('fixitnow_refresh_token', data.refresh_token);
    localStorage.setItem('fixitnow_user', JSON.stringify(data.user));
  };

  const login = async (username, password) => {
    setLoading(true);
    try {
      const res = await apiClient.post('/auth/login', { username, password });
      saveAuthData(res.data);
      return res.data.user;
    } finally {
      setLoading(false);
    }
  };

  const register = async (payload) => {
    setLoading(true);
    try {
      const res = await apiClient.post('/auth/register', payload);
      // Auto login after registration
      return await login(payload.email, payload.password);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('fixitnow_access_token');
    localStorage.removeItem('fixitnow_refresh_token');
    localStorage.removeItem('fixitnow_user');
  };

  const updateUserProfile = (updatedProfile) => {
    if (user) {
      const newUser = { ...user, mechanic_profile: updatedProfile };
      setUser(newUser);
      localStorage.setItem('fixitnow_user', JSON.stringify(newUser));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        loading,
        login,
        register,
        logout,
        updateUserProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
