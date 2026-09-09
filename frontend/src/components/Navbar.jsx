import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Wrench, LogOut, User as UserIcon, PlusCircle, Shield, Activity } from 'lucide-react';

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <Wrench className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent">
                FixItNow
              </span>
              <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold -mt-1">
                Appliance Repairs
              </span>
            </div>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {user?.role === 'customer' && (
                  <>
                    <Link
                      to="/customer"
                      className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
                    >
                      My Bookings
                    </Link>
                    <Link
                      to="/bookings/new"
                      className="flex items-center space-x-1 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-md shadow-indigo-600/30 transition-all hover:scale-[1.02]"
                    >
                      <PlusCircle className="w-4 h-4" />
                      <span>Book Repair</span>
                    </Link>
                  </>
                )}

                {user?.role === 'mechanic' && (
                  <Link
                    to="/mechanic"
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors"
                  >
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <span>Mechanic Console</span>
                  </Link>
                )}

                {user?.role === 'admin' && (
                  <Link
                    to="/admin"
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 text-sm font-medium transition-colors"
                  >
                    <Shield className="w-4 h-4" />
                    <span>Admin Panel</span>
                  </Link>
                )}

                <div className="flex items-center space-x-3 pl-4 border-l border-slate-800">
                  <div className="flex flex-col text-right">
                    <span className="text-sm font-medium text-slate-200">{user?.name}</span>
                    <span className="text-xs text-indigo-400 capitalize">{user?.role}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Sign Out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-md shadow-indigo-600/30 transition-all hover:scale-[1.02]"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
