import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { Shield, Users, Calendar, AlertTriangle, RefreshCw, X, Check } from 'lucide-react';

export const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('bookings'); // 'bookings' | 'users'
  const [bookings, setBookings] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [forceAction, setForceAction] = useState('expire');
  const [forceReason, setForceReason] = useState('');
  const [forceLoading, setForceLoading] = useState(false);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/admin/bookings');
      setBookings(res.data);
    } catch (err) {
      console.error('Error fetching admin bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/admin/users');
      setUsers(res.data);
    } catch (err) {
      console.error('Error fetching admin users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'bookings') fetchBookings();
    else fetchUsers();
  }, [activeTab]);

  const handleForceResolve = async (e) => {
    e.preventDefault();
    if (!selectedBooking) return;
    setForceLoading(true);
    try {
      await apiClient.post(`/admin/bookings/${selectedBooking.id}/force-resolve`, {
        action: forceAction,
        reason: forceReason.trim() || 'Admin manual resolution',
      });
      setSelectedBooking(null);
      setForceReason('');
      fetchBookings();
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Force resolve failed');
    } finally {
      setForceLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-1">
            <Shield className="w-4 h-4" />
            <span>Administrator Control Center</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">System Overview</h1>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800">
          <button
            onClick={() => setActiveTab('bookings')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
              activeTab === 'bookings'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Bookings ({bookings.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
              activeTab === 'users'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Users ({users.length})</span>
          </button>
        </div>
      </div>

      {/* BOOKINGS VIEW */}
      {activeTab === 'bookings' && (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
          <div className="p-4 sm:p-6 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">All System Bookings</h2>
            <button
              onClick={fetchBookings}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">ID / Created</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Customer</th>
                  <th className="px-6 py-3.5">Technician</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200">
                {bookings.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-mono font-bold text-indigo-400">#{b.id.slice(0, 8)}</span>
                      <span className="block text-[10px] text-slate-500 mt-0.5">
                        {new Date(b.created_at).toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-white">{b.category?.name}</td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-white">{b.customer?.name}</span>
                      <span className="block text-[10px] text-slate-400">{b.customer?.phone}</span>
                    </td>
                    <td className="px-6 py-4">
                      {b.accepted_mechanic ? (
                        <div>
                          <span className="font-medium text-white">{b.accepted_mechanic.name}</span>
                          <span className="block text-[10px] text-slate-400">{b.accepted_mechanic.phone}</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={b.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedBooking(b)}
                        className="px-3 py-1.5 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 font-semibold hover:bg-amber-500/30 transition-colors"
                      >
                        Force Resolve
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* USERS VIEW */}
      {activeTab === 'users' && (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
          <div className="p-4 sm:p-6 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Registered Users</h2>
            <button
              onClick={fetchUsers}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Name</th>
                  <th className="px-6 py-3.5">Role</th>
                  <th className="px-6 py-3.5">Contact</th>
                  <th className="px-6 py-3.5">Profile Info</th>
                  <th className="px-6 py-3.5">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-bold text-white">{u.name}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                          u.role === 'admin'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : u.role === 'mechanic'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="block text-slate-300">{u.email}</span>
                      <span className="block text-[11px] text-slate-500">{u.phone}</span>
                    </td>
                    <td className="px-6 py-4">
                      {u.mechanic_profile ? (
                        <div className="space-y-0.5 text-[11px] text-slate-400">
                          <span>Radius: {u.mechanic_profile.service_radius_km} km</span> •{' '}
                          <span>Rating: {u.mechanic_profile.rating_avg.toFixed(1)} ★</span> •{' '}
                          <span className={u.mechanic_profile.is_available ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>
                            {u.mechanic_profile.is_available ? 'Online' : 'Offline'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* FORCE RESOLVE MODAL */}
      {selectedBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedBooking(null)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2 text-amber-400 font-bold mb-2 text-sm">
              <AlertTriangle className="w-5 h-5" />
              <span>Administrative Override</span>
            </div>

            <h3 className="text-xl font-black text-white">
              Force-Resolve Booking #{selectedBooking.id.slice(0, 8)}
            </h3>
            <p className="text-xs text-slate-400 mt-1 mb-6">
              Current Status: <strong className="text-indigo-300">{selectedBooking.status}</strong>
            </p>

            <form onSubmit={handleForceResolve} className="space-y-5">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                  Select Resolution Action
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'expire', label: 'Expire Request' },
                    { id: 'cancel_customer', label: 'Cancel (Customer)' },
                    { id: 'rebroadcast', label: 'Rebroadcast Job' },
                    { id: 'complete', label: 'Force Complete' },
                  ].map((act) => (
                    <button
                      key={act.id}
                      type="button"
                      onClick={() => setForceAction(act.id)}
                      className={`p-3 rounded-xl border text-xs font-bold text-left transition-all ${
                        forceAction === act.id
                          ? 'bg-amber-500/20 border-amber-500 text-amber-300 ring-2 ring-amber-500/30'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {act.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                  Audit Reason (Required)
                </label>
                <textarea
                  rows={3}
                  required
                  value={forceReason}
                  onChange={(e) => setForceReason(e.target.value)}
                  placeholder="Explain why this administrative resolution is being applied..."
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={forceLoading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50 text-sm"
              >
                {forceLoading ? 'Applying Resolution...' : 'Confirm Administrative Resolution'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
