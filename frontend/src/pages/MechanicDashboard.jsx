import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { createMechanicSocket } from '../api/websocket';
import { StatusBadge } from '../components/StatusBadge';
import {
  Wrench,
  Radio,
  Power,
  MapPin,
  Check,
  X,
  Navigation,
  Star,
  CheckCircle2,
  Clock,
  Car,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCheck
} from 'lucide-react';

export const MechanicDashboard = () => {
  const { user, updateUserProfile } = useAuth();
  const [isAvailable, setIsAvailable] = useState(user?.mechanic_profile?.is_available ?? true);
  const [currentLat, setCurrentLat] = useState(user?.mechanic_profile?.current_lat ?? 18.5204);
  const [currentLng, setCurrentLng] = useState(user?.mechanic_profile?.current_lng ?? 73.8567);

  const [incomingJobs, setIncomingJobs] = useState([]);
  const [activeJob, setActiveJob] = useState(null);
  const [historyJobs, setHistoryJobs] = useState([]);

  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [bannerNotice, setBannerNotice] = useState(null);
  const socketRef = useRef(null);

  // Load initial data
  const fetchData = async () => {
    try {
      const [incomingRes, activeRes, historyRes] = await Promise.all([
        apiClient.get('/mechanic/jobs/incoming'),
        apiClient.get('/mechanic/jobs/active'),
        apiClient.get('/mechanic/jobs/history'),
      ]);
      setIncomingJobs(incomingRes.data);
      setActiveJob(activeRes.data);
      setHistoryJobs(historyRes.data);
    } catch (err) {
      console.error('Error fetching mechanic dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchData();

    // Setup Mechanic WebSocket
    if (user?.id) {
      const socket = createMechanicSocket(
        user.id,
        (data) => {
          console.log('[Mechanic WS Message]:', data);
          if (data.type === 'NEW_JOB') {
            setIncomingJobs((prev) => {
              if (prev.some((j) => j.booking_id === data.booking_id)) return prev;
              return [data, ...prev];
            });
            setBannerNotice(`⚡ New Job Alert: ${data.category} (${data.distance_km} km away)`);
          } else if (data.type === 'JOB_TAKEN') {
            setIncomingJobs((prev) => prev.filter((j) => j.booking_id !== data.booking_id));
            setBannerNotice(`Job #${data.booking_id.slice(0, 8)} was accepted by another mechanic.`);
          }
        },
        () => setWsConnected(true),
        () => setWsConnected(false)
      );

      socketRef.current = socket;

      return () => {
        if (socketRef.current) socketRef.current.close();
      };
    }
  }, [user?.id]);

  // Toggle Online / Offline
  const handleToggleAvailability = async () => {
    const nextState = !isAvailable;
    setIsAvailable(nextState);
    try {
      const res = await apiClient.patch('/mechanic/availability', { is_available: nextState });
      updateUserProfile(res.data);
    } catch (err) {
      setIsAvailable(!nextState);
      alert('Failed to update availability status');
    }
  };

  // Update Location
  const handleUpdateLocation = async (lat, lng) => {
    setCurrentLat(lat);
    setCurrentLng(lng);
    try {
      const res = await apiClient.patch('/mechanic/location', {
        current_lat: parseFloat(lat),
        current_lng: parseFloat(lng),
      });
      updateUserProfile(res.data);
      fetchData(); // Refresh nearby jobs
    } catch (err) {
      alert('Failed to update coordinates');
    }
  };

  const handleUseGPS = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = parseFloat(pos.coords.latitude.toFixed(4));
          const lng = parseFloat(pos.coords.longitude.toFixed(4));
          handleUpdateLocation(lat, lng);
        },
        (err) => alert('Could not retrieve GPS location: ' + err.message)
      );
    }
  };

  // Accept Job
  const handleAcceptJob = async (bookingId) => {
    setLoading(true);
    try {
      const res = await apiClient.post(`/bookings/${bookingId}/accept`);
      setIncomingJobs((prev) => prev.filter((j) => j.booking_id !== bookingId));
      setActiveJob(res.data);
      setBannerNotice('🎉 Job Accepted! You can now start journey to customer location.');
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Failed to accept job';
      alert(msg);
      // Remove from list if already taken
      setIncomingJobs((prev) => prev.filter((j) => j.booking_id !== bookingId));
    } finally {
      setLoading(false);
    }
  };

  // Reject Job
  const handleRejectJob = async (bookingId) => {
    try {
      await apiClient.post(`/bookings/${bookingId}/reject`);
      setIncomingJobs((prev) => prev.filter((j) => j.booking_id !== bookingId));
    } catch (err) {
      console.error('Error rejecting job:', err);
    }
  };

  // Update Status: EN_ROUTE -> IN_PROGRESS -> COMPLETED
  const handleUpdateStatus = async (nextStatus) => {
    if (!activeJob) return;
    setLoading(true);
    try {
      const res = await apiClient.patch(`/bookings/${activeJob.id}/status`, {
        status: nextStatus,
      });

      if (nextStatus === 'COMPLETED') {
        setActiveJob(null);
        setBannerNotice('✅ Job completed successfully! Great job.');
        fetchData();
      } else {
        setActiveJob(res.data);
      }
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  // Cancel Job (triggers rebroadcast)
  const handleCancelActiveJob = async () => {
    if (!window.confirm('Cancel this job? It will immediately rebroadcast to other nearby technicians.')) return;
    setLoading(true);
    try {
      await apiClient.patch(`/bookings/${activeJob.id}/status`, {
        status: 'CANCELLED_BY_MECHANIC',
        note: 'Cancelled by technician',
      });
      setActiveJob(null);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to cancel job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner & Online Toggle */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Technician Console</span>
            <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-[11px] font-semibold">
              <Radio className={`w-3 h-3 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
              <span className={wsConnected ? 'text-emerald-400' : 'text-slate-500'}>
                {wsConnected ? 'Live Broadcast Channel Connected' : 'Connecting...'}
              </span>
            </div>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">{user?.name}</h1>
          <div className="flex items-center space-x-4 mt-2 text-xs text-slate-400">
            <span className="flex items-center space-x-1 font-semibold text-amber-400">
              <Star className="w-3.5 h-3.5 fill-amber-400" />
              <span>{user?.mechanic_profile?.rating_avg?.toFixed(1) || '5.0'} Avg Rating</span>
            </span>
            <span>•</span>
            <span className="text-emerald-400 font-semibold">
              {user?.mechanic_profile?.jobs_completed ?? 0} Jobs Completed
            </span>
            <span>•</span>
            <span>Radius: {user?.mechanic_profile?.service_radius_km} km</span>
          </div>
        </div>

        {/* Online / Offline Switch */}
        <div className="flex items-center space-x-4 bg-slate-950/80 border border-slate-800 p-3 rounded-2xl">
          <div className="text-right">
            <span className="text-xs text-slate-400 block">Duty Status</span>
            <span className={`text-sm font-bold ${isAvailable ? 'text-emerald-400' : 'text-slate-500'}`}>
              {isAvailable ? 'Online (Accepting Jobs)' : 'Offline'}
            </span>
          </div>
          <button
            onClick={handleToggleAvailability}
            className={`p-3 rounded-xl font-bold transition-all flex items-center space-x-2 ${
              isAvailable
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-400'
            }`}
          >
            <Power className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Banner Notice */}
      {bannerNotice && (
        <div className="p-4 rounded-2xl bg-indigo-950/80 border border-indigo-700 text-indigo-200 text-sm flex items-center justify-between shadow-xl">
          <span>{bannerNotice}</span>
          <button onClick={() => setBannerNotice(null)} className="p-1 text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Location Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3 text-xs text-slate-300">
          <MapPin className="w-4 h-4 text-indigo-400" />
          <span>
            Current GPS Base: <strong className="text-white">({currentLat?.toFixed(4)}, {currentLng?.toFixed(4)})</strong>
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleUpdateLocation(18.5204, 73.8567)}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
          >
            Pune City Center
          </button>
          <button
            onClick={handleUseGPS}
            className="px-3 py-1.5 rounded-xl bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-800 text-xs font-semibold text-emerald-300 flex items-center space-x-1 transition-colors"
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Update via GPS</span>
          </button>
        </div>
      </div>

      {/* ACTIVE JOB SECTION */}
      {activeJob && (
        <div className="bg-gradient-to-br from-indigo-950/50 via-slate-900 to-slate-900 border-2 border-indigo-500/50 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4 border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 block mb-1">
                Active Assigned Job
              </span>
              <h2 className="text-2xl font-black text-white">{activeJob.category?.name}</h2>
            </div>
            <StatusBadge status={activeJob.status} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Customer Details</span>
              <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 space-y-2 text-sm text-slate-300">
                <div className="font-bold text-white text-base">{activeJob.customer?.name}</div>
                <div className="text-xs text-slate-400">Phone: {activeJob.customer?.phone}</div>
                <div className="text-xs text-indigo-400 flex items-center space-x-1">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>Customer Coords: {activeJob.customer_lat.toFixed(4)}, {activeJob.customer_lng.toFixed(4)}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Issue Description</span>
              <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 text-sm text-slate-200 leading-relaxed">
                {activeJob.description}
              </div>
            </div>
          </div>

          {/* Workflow Action Stepper Buttons */}
          <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <button
              onClick={handleCancelActiveJob}
              disabled={loading}
              className="px-4 py-2.5 rounded-xl bg-rose-950/40 hover:bg-rose-900/50 border border-rose-800 text-rose-300 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Cancel & Rebroadcast</span>
            </button>

            <div className="flex items-center space-x-3">
              {activeJob.status === 'ACCEPTED' && (
                <button
                  onClick={() => handleUpdateStatus('EN_ROUTE')}
                  disabled={loading}
                  className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-sm shadow-lg shadow-amber-500/20 flex items-center space-x-2 transition-all"
                >
                  <Car className="w-4 h-4" />
                  <span>Start Journey (EN_ROUTE)</span>
                </button>
              )}

              {activeJob.status === 'EN_ROUTE' && (
                <button
                  onClick={() => handleUpdateStatus('IN_PROGRESS')}
                  disabled={loading}
                  className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-sm shadow-lg shadow-purple-600/30 flex items-center space-x-2 transition-all"
                >
                  <Play className="w-4 h-4" />
                  <span>Arrived & Start Work (IN_PROGRESS)</span>
                </button>
              )}

              {activeJob.status === 'IN_PROGRESS' && (
                <button
                  onClick={() => handleUpdateStatus('COMPLETED')}
                  disabled={loading}
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-extrabold text-sm shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all"
                >
                  <CheckCheck className="w-4 h-4" />
                  <span>Mark Job as Completed</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* INCOMING JOBS RADAR SECTION */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <span>Incoming Nearby Requests</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
              {incomingJobs.length}
            </span>
          </h2>
          <button
            onClick={fetchData}
            className="text-xs text-indigo-400 hover:underline font-semibold"
          >
            Refresh Radar
          </button>
        </div>

        {!isAvailable ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center text-slate-400 text-sm">
            <Power className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="font-semibold text-slate-300">You are currently Offline</p>
            <p className="text-xs text-slate-500 mt-1">Switch to Online above to receive nearby broadcast requests.</p>
          </div>
        ) : incomingJobs.length === 0 ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center text-slate-400 text-sm">
            <Radio className="w-10 h-10 text-indigo-500/50 mx-auto mb-2 animate-pulse" />
            <p className="font-semibold text-slate-300">Scanning for Repair Requests in Your Area...</p>
            <p className="text-xs text-slate-500 mt-1">
              New customer requests within {user?.mechanic_profile?.service_radius_km} km will appear here instantly.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {incomingJobs.map((job) => (
              <div
                key={job.booking_id}
                className="bg-slate-900 border-2 border-indigo-600/40 rounded-3xl p-6 shadow-2xl flex flex-col justify-between space-y-4 hover:border-indigo-500 transition-all animate-pulse-ring"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-black uppercase tracking-wider text-emerald-400">
                      {job.category || job.category_name}
                    </span>
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800">
                      📍 {job.distance_km} km away
                    </span>
                  </div>

                  <p className="text-sm font-semibold text-white mt-2 mb-3 leading-relaxed">
                    {job.description}
                  </p>

                  <div className="flex items-center space-x-3 text-xs text-slate-400">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{new Date(job.created_at).toLocaleTimeString()}</span>
                    </span>
                    <span>•</span>
                    <span>Lat: {job.customer_lat?.toFixed(4)}, Lng: {job.customer_lng?.toFixed(4)}</span>
                  </div>
                </div>

                {/* Accept & Reject Buttons */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800">
                  <button
                    onClick={() => handleRejectJob(job.booking_id)}
                    className="py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors flex items-center justify-center space-x-1"
                  >
                    <X className="w-4 h-4" />
                    <span>Pass / Reject</span>
                  </button>

                  <button
                    onClick={() => handleAcceptJob(job.booking_id)}
                    disabled={loading}
                    className="py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center space-x-1 disabled:opacity-50"
                  >
                    <Check className="w-4 h-4" />
                    <span>Accept Job</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* COMPLETED JOBS HISTORY */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Completed Jobs History</h2>
        {historyJobs.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6 text-center text-slate-500 text-sm">
            No completed jobs yet.
          </div>
        ) : (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl divide-y divide-slate-800 overflow-hidden shadow-xl">
            {historyJobs.map((j) => (
              <div key={j.id} className="p-4 sm:p-6 flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-3 mb-1">
                    <span className="font-bold text-white">{j.category?.name}</span>
                    <StatusBadge status={j.status} />
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-1">{j.description}</p>
                  <span className="text-[11px] text-slate-500 block mt-1">
                    Customer: {j.customer?.name} • {new Date(j.updated_at).toLocaleDateString()}
                  </span>
                </div>

                {j.review && (
                  <div className="text-right">
                    <div className="flex items-center space-x-1 justify-end">
                      {[...Array(j.review.rating)].map((_, i) => (
                        <Star key={i} className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    {j.review.comment && (
                      <span className="text-[11px] text-slate-400 italic">"{j.review.comment}"</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
