import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';

import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { CustomerDashboard } from './pages/CustomerDashboard';
import { CreateBooking } from './pages/CreateBooking';
import { BookingDetails } from './pages/BookingDetails';
import { MechanicDashboard } from './pages/MechanicDashboard';
import { AdminDashboard } from './pages/AdminDashboard';

const RootRedirect = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role === 'mechanic') return <Navigate to="/mechanic" replace />;
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  return <Navigate to="/customer" replace />;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
          <Navbar />
          <main className="flex-1">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Customer Routes */}
              <Route
                path="/customer"
                element={
                  <ProtectedRoute allowedRoles={['customer']}>
                    <CustomerDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/bookings/new"
                element={
                  <ProtectedRoute allowedRoles={['customer']}>
                    <CreateBooking />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/bookings/:id"
                element={
                  <ProtectedRoute allowedRoles={['customer', 'mechanic', 'admin']}>
                    <BookingDetails />
                  </ProtectedRoute>
                }
              />

              {/* Mechanic Routes */}
              <Route
                path="/mechanic"
                element={
                  <ProtectedRoute allowedRoles={['mechanic']}>
                    <MechanicDashboard />
                  </ProtectedRoute>
                }
              />

              {/* Admin Routes */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute allowedRoles={['admin']}>
                    <AdminDashboard />
                  </ProtectedRoute>
                }
              />

              {/* Root */}
              <Route path="/" element={<RootRedirect />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
