import React, { useState } from 'react';
import { Star, X } from 'lucide-react';
import { apiClient } from '../api/client';

export const ReviewModal = ({ bookingId, mechanicName, isOpen, onClose, onSuccess }) => {
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiClient.post(`/bookings/${bookingId}/review`, {
        rating,
        comment: comment.trim() || undefined,
      });
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to submit review');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-white mb-1">Rate Your Service</h3>
        <p className="text-sm text-slate-400 mb-6">
          How was your experience with <span className="text-indigo-400 font-semibold">{mechanicName || 'the mechanic'}</span>?
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Star Selector */}
          <div className="flex justify-center items-center space-x-2 py-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                type="button"
                key={star}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                className="p-1 focus:outline-none transition-transform hover:scale-125"
              >
                <Star
                  className={`w-8 h-8 ${
                    (hoverRating || rating) >= star
                      ? 'fill-amber-400 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]'
                      : 'text-slate-700'
                  } transition-colors`}
                />
              </button>
            ))}
          </div>

          {/* Comment */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Comment (Optional)
            </label>
            <textarea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Tell us what went well or how we can improve..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm resize-none"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-emerald-600 hover:from-indigo-500 hover:to-emerald-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Rating & Review'}
          </button>
        </form>
      </div>
    </div>
  );
};
