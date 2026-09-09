import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Wrench, MapPin, Navigation, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';

export const CreateBooking = () => {
  const [categories, setCategories] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [lat, setLat] = useState(18.5314); // Pune Shivajinagar default demo location
  const [lng, setLng] = useState(73.8446);
  const [scheduledAt, setScheduledAt] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get('/categories')
      .then((res) => {
        setCategories(res.data);
        if (res.data.length > 0) {
          setSelectedCategoryId(res.data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load categories:', err));
  }, []);

  const handleUsePuneDemoLocation = () => {
    setLat(18.5314);
    setLng(73.8446);
  };

  const handleUseGPSLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(parseFloat(pos.coords.latitude.toFixed(4)));
          setLng(parseFloat(pos.coords.longitude.toFixed(4)));
        },
        (err) => alert('Could not get GPS location: ' + err.message)
      );
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!selectedCategoryId) {
      setError('Please select a repair category.');
      return;
    }
    if (description.trim().length < 5) {
      setError('Please provide a detailed description of the appliance issue.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        category_id: selectedCategoryId,
        description: description.trim(),
        customer_lat: parseFloat(lat),
        customer_lng: parseFloat(lng),
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : undefined,
      };

      const res = await apiClient.post('/bookings', payload);
      navigate(`/bookings/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to create booking.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Request an Appliance Repair</h1>
        <p className="text-sm text-slate-400 mt-1">
          Tell us about the issue and we'll instantly broadcast to qualified nearby technicians.
        </p>
      </div>

      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-md">
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-950/50 border border-rose-800 text-rose-300 flex items-center space-x-3 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Step 1: Category Selection */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
              1. Select Repair Category
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {categories.map((cat) => {
                const isSelected = selectedCategoryId === cat.id;
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setSelectedCategoryId(cat.id)}
                    className={`p-4 rounded-2xl border text-left flex flex-col justify-between transition-all duration-200 ${
                      isSelected
                        ? 'bg-indigo-600/20 border-indigo-500 ring-2 ring-indigo-500/40 text-white shadow-lg shadow-indigo-600/20'
                        : 'bg-slate-950/70 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full mb-2">
                      <Wrench className={`w-5 h-5 ${isSelected ? 'text-indigo-400' : 'text-slate-500'}`} />
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                    </div>
                    <span className="font-semibold text-sm block">{cat.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Step 2: Description */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
              2. Describe the Issue
            </label>
            <textarea
              rows={4}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="E.g., Ceiling fan is vibrating and making a squeaking sound when turned on speed 3..."
              className="w-full px-4 py-3 rounded-2xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm resize-none"
            />
          </div>

          {/* Step 3: Location Coordinates */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <MapPin className="w-4 h-4 text-indigo-400" />
                <span>3. Service Location Coordinates</span>
              </label>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleUsePuneDemoLocation}
                  className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-950/60 border border-indigo-800 text-indigo-300 hover:bg-indigo-900 transition-colors"
                >
                  ⚡ Pune Demo Pin
                </button>
                <button
                  type="button"
                  onClick={handleUseGPSLocation}
                  className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 hover:bg-emerald-900 flex items-center space-x-1 transition-colors"
                >
                  <Navigation className="w-3 h-3" />
                  <span>Use My GPS</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[11px] text-slate-400 block mb-1">Latitude</span>
                <input
                  type="number"
                  step="0.0001"
                  required
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                />
              </div>
              <div>
                <span className="text-[11px] text-slate-400 block mb-1">Longitude</span>
                <input
                  type="number"
                  step="0.0001"
                  required
                  value={lng}
                  onChange={(e) => setLng(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-600 hover:from-indigo-500 hover:to-emerald-500 text-white font-bold text-base shadow-xl shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 mt-6"
          >
            <span>{loading ? 'Creating Request & Broadcasting...' : 'Find Nearby Mechanics Now'}</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
