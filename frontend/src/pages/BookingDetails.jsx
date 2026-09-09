import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { createCustomerBookingSocket } from '../api/websocket';
import { StatusBadge } from '../components/StatusBadge';
import { BookingTimeline } from '../components/BookingTimeline';
import { ReviewModal } from '../components/ReviewModal';
import {
  Wrench,
  MapPin,
  Calendar,
  User,
  Phone,
  Star,
  Clock,
  Ban,
  ArrowLeft,
  Radio,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export const BookingDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const socketRef = useRef(null);

  const fetchBooking = async () => {
    try {
      const res = await apiClient.get(`/bookings/${id}`);
      setBooking(res.data);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load booking');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooking();

    // Connect to real-time WebSocket for this booking
    const socket = createCustomerBookingSocket(
      id,
      (data) => {
        console.log('[Customer WS Message received]:', data);
        if (data.type === 'BOOKING_STATUS' || data.type === 'BOOKING_ACCEPTED') {
          // Re-fetch full booking state to synchronize relations and history
          fetchBooking();
        }
      },
      () => setWsConnected(true),
      () => setWsConnected(false)
    );

    socketRef.current = socket;

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [id]);

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) return;
    try {
      await apiClient.post(`/bookings/${id}/cancel`);
      fetchBooking();
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to cancel booking');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400">Loading booking status...</p>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h2 className="text-xl font-bold text-white mb-2">Could Not Load Booking</h2>
        <p className="text-slate-400 mb-6">{error || 'Booking not found'}</p>
        <button
          onClick={() => navigate('/customer')}
          className="px-6 py-2.5 rounded-xl bg-slate-800 text-white font-semibold hover:bg-slate-700 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const canCancel = ['REQUESTED', 'BROADCASTING'].includes(booking.status);
  const isCompleted = booking.status === 'COMPLETED';
  const hasReview = !!booking.review;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Navigation & WS Status */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/customer')}
          className="flex items-center space-x-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center space-x-2 text-xs font-semibold px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
          <Radio className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
          <span className={wsConnected ? 'text-emerald-400' : 'text-slate-500'}>
            {wsConnected ? 'Live Updates Active' : 'Connecting to Live Updates...'}
          </span>
        </div>
      </div>

      {/* Main Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-8 backdrop-blur-md">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                {booking.category?.name}
              </span>
              <StatusBadge status={booking.status} />
            </div>
            <h1 className="text-2xl font-black text-white">Booking #{booking.id.slice(0, 8)}</h1>
          </div>

          <div className="flex items-center space-x-3">
            {canCancel && (
              <button
                onClick={handleCancel}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-rose-950/50 hover:bg-rose-900/50 border border-rose-800 text-rose-300 text-xs font-semibold transition-colors"
              >
                <Ban className="w-4 h-4" />
                <span>Cancel Request</span>
              </button>
            )}

            {isCompleted && !hasReview && (
              <button
                onClick={() => setShowReviewModal(true)}
                className="flex items-center space-x-1.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition-all hover:scale-105"
              >
                <Star className="w-4 h-4 fill-slate-950" />
                <span>Leave Review</span>
              </button>
            )}
          </div>
        </div>

        {/* Live Stepper Timeline */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-6">
          <BookingTimeline status={booking.status} />
        </div>

        {/* Live Broadcasting Pulse Banner if searching */}
        {booking.status === 'BROADCASTING' && (
          <div className="p-4 rounded-2xl bg-indigo-950/40 border border-indigo-800/60 flex items-center space-x-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/30 flex items-center justify-center flex-shrink-0 animate-pulse">
              <Radio className="w-5 h-5 text-indigo-400 animate-spin" />
            </div>
            <div>
              <span className="text-sm font-bold text-white block">Broadcasting to Nearby Technicians</span>
              <span className="text-xs text-indigo-300">
                Evaluating distances and sending job alerts to available mechanics within 10 km.
              </span>
            </div>
          </div>
        )}

        {/* Assigned Mechanic Card */}
        {booking.accepted_mechanic && (
          <div className="bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-950 border border-indigo-900/50 rounded-2xl p-6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-4 flex items-center space-x-1.5">
              <User className="w-4 h-4" />
              <span>Assigned Technician</span>
            </h3>

            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-emerald-500 flex items-center justify-center text-white font-extrabold text-xl shadow-lg shadow-indigo-600/30">
                  {booking.accepted_mechanic.name.charAt(0)}
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">{booking.accepted_mechanic.name}</h4>
                  <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                    <span className="flex items-center space-x-1">
                      <Phone className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{booking.accepted_mechanic.phone}</span>
                    </span>
                    {booking.accepted_mechanic.rating_avg !== null && (
                      <span className="flex items-center space-x-1 font-semibold text-amber-400">
                        <Star className="w-3.5 h-3.5 fill-amber-400" />
                        <span>{booking.accepted_mechanic.rating_avg.toFixed(1)}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="px-4 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
                Status:{' '}
                <span className="font-bold text-emerald-400 capitalize">
                  {booking.status.replace('_', ' ').toLowerCase()}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Issue Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Problem Description
            </h3>
            <p className="text-sm text-slate-200 bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 leading-relaxed">
              {booking.description}
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Service Coordinates
              </h3>
              <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 flex items-center space-x-3 text-sm text-slate-300">
                <MapPin className="w-5 h-5 text-indigo-400 flex-shrink-0" />
                <span>
                  Lat: {booking.customer_lat.toFixed(4)}, Lng: {booking.customer_lng.toFixed(4)}
                </span>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Timeline Audit Trail
              </h3>
              <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-2 max-h-40 overflow-y-auto">
                {booking.status_history?.map((h) => (
                  <div key={h.id} className="text-xs flex items-center justify-between text-slate-400 border-b border-slate-800/40 pb-1.5 last:border-0">
                    <span className="font-semibold text-slate-300">{h.status}</span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(h.changed_at).toLocaleTimeString()} {h.note ? `• ${h.note}` : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Review summary if already submitted */}
        {hasReview && (
          <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-800/40">
            <div className="flex items-center space-x-2 mb-1">
              <div className="flex">
                {[...Array(booking.review.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                ))}
              </div>
              <span className="text-xs font-bold text-amber-300">Your Review</span>
            </div>
            {booking.review.comment && (
              <p className="text-xs text-slate-300 mt-1 italic">"{booking.review.comment}"</p>
            )}
          </div>
        )}
      </div>

      {/* Review Modal */}
      <ReviewModal
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        bookingId={booking.id}
        mechanicName={booking.accepted_mechanic?.name}
        onSuccess={() => fetchBooking()}
      />
    </div>
  );
};
