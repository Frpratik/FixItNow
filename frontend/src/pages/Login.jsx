import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Wrench, ArrowRight, Shield, User, Hammer } from 'lucide-react';

export const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const loggedUser = await login(username, password);
      if (from) {
        navigate(from, { replace: true });
      } else if (loggedUser.role === 'customer') {
        navigate('/customer');
      } else if (loggedUser.role === 'mechanic') {
        navigate('/mechanic');
      } else if (loggedUser.role === 'admin') {
        navigate('/admin');
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Invalid email/phone or password.');
    }
  };

  const handleQuickLogin = async (email, pass) => {
    setUsername(email);
    setPassword(pass);
    try {
      const loggedUser = await login(email, pass);
      if (loggedUser.role === 'customer') navigate('/customer');
      else if (loggedUser.role === 'mechanic') navigate('/mechanic');
      else if (loggedUser.role === 'admin') navigate('/admin');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Quick login failed.');
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-emerald-400 items-center justify-center shadow-xl shadow-indigo-500/20 mb-4">
            <Wrench className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Welcome to FixItNow</h2>
          <p className="text-sm text-slate-400 mt-1">Sign in to your account or use a demo profile below</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Email or Phone
              </label>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="name@example.com or +919800000001"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'Signing in...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Logins */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <span className="text-xs font-semibold text-slate-400 block mb-3 text-center uppercase tracking-wider">
              ⚡ One-Click Demo Logins
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('customer1@fixitnow.local', 'Customer@123')}
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 flex flex-col items-center space-y-1 transition-all"
              >
                <User className="w-4 h-4 text-emerald-400" />
                <span>Customer</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('mechanic1@fixitnow.local', 'Mechanic@123')}
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 flex flex-col items-center space-y-1 transition-all"
              >
                <Hammer className="w-4 h-4 text-indigo-400" />
                <span>Mechanic 1</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@fixitnow.local', 'Admin@123')}
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 flex flex-col items-center space-y-1 transition-all"
              >
                <Shield className="w-4 h-4 text-amber-400" />
                <span>Admin</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-slate-400 mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-indigo-400 font-semibold hover:text-indigo-300">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
};
