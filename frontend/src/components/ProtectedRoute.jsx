import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    // Redirect to their default dashboard based on their role
    if (user?.role === 'mechanic') return <Navigate to="/mechanic" replace />;
    if (user?.role === 'admin') return <Navigate to="/admin" replace />;
    return <Navigate to="/customer" replace />;
  }

  return children;
};
