import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { PlusCircle, Clock, Calendar, ArrowRight, RefreshCw, AlertCircle } from 'lucide-react';

export const CustomerDashboard = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBookings = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/bookings/mine');
      setBookings(res.data);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load bookings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const activeBookings = bookings.filter(
    (b) => !['COMPLETED', 'CANCELLED_BY_CUSTOMER', 'CANCELLED_BY_MECHANIC', 'EXPIRED'].includes(b.status)
  );
  const pastBookings = bookings.filter(
    (b) => ['COMPLETED', 'CANCELLED_BY_CUSTOMER', 'CANCELLED_BY_MECHANIC', 'EXPIRED'].includes(b.status)
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 bg-gradient-to-r from-indigo-950/60 to-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Customer Dashboard</h1>
          <p className="text-slate-400 mt-1">Book on-demand electrical repairs and track technician progress in real-time.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchBookings}
            className="p-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <Link
            to="/bookings/new"
            className="flex items-center space-x-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-emerald-600 hover:from-indigo-500 hover:to-emerald-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
          >
            <PlusCircle className="w-5 h-5" />
            <span>Book New Repair</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Bookings Section */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center space-x-2">
          <span>Active Bookings</span>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-900/60 text-indigo-300 border border-indigo-700/50">
            {activeBookings.length}
          </span>
        </h2>

        {activeBookings.length === 0 ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center">
            <Clock className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-300 font-semibold">No active repair requests</p>
            <p className="text-xs text-slate-500 mt-1">Need something fixed? Create a repair request now.</p>
            <Link
              to="/bookings/new"
              className="inline-flex items-center space-x-2 mt-4 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500 transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Request Repair</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activeBookings.map((b) => (
              <Link
                key={b.id}
                to={`/bookings/${b.id}`}
                className="group bg-slate-900/90 hover:bg-slate-850 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 shadow-xl transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                      {b.category?.name || 'Repair Service'}
                    </span>
                    <StatusBadge status={b.status} />
                  </div>

                  <p className="text-sm font-medium text-slate-200 line-clamp-2 mb-4">
                    {b.description}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(b.created_at).toLocaleDateString()}</span>
                  </span>
                  <span className="flex items-center space-x-1 font-semibold text-indigo-400 group-hover:translate-x-1 transition-transform">
                    <span>Track Status</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Booking History Section */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Past Bookings</h2>
        {pastBookings.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6 text-center text-slate-500 text-sm">
            No past bookings recorded yet.
          </div>
        ) : (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="divide-y divide-slate-800">
              {pastBookings.map((b) => (
                <div key={b.id} className="p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-800/40 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-3">
                      <span className="font-bold text-white text-base">{b.category?.name}</span>
                      <StatusBadge status={b.status} />
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">{b.description}</p>
                    <span className="text-[11px] text-slate-500 block">
                      Created on {new Date(b.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="flex items-center space-x-4">
                    {b.accepted_mechanic && (
                      <div className="text-right hidden sm:block">
                        <span className="text-xs text-slate-400 block">Technician</span>
                        <span className="text-xs font-semibold text-slate-200">{b.accepted_mechanic.name}</span>
                      </div>
                    )}
                    <Link
                      to={`/bookings/${b.id}`}
                      className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
