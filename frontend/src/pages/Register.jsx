import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { Wrench, User, Hammer, ArrowRight, Check } from 'lucide-react';

export const Register = () => {
  const [role, setRole] = useState('customer'); // 'customer' | 'mechanic'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');

  // Mechanic specific fields
  const [categories, setCategories] = useState([]);
  const [selectedCatIds, setSelectedCatIds] = useState([]);
  const [serviceRadiusKm, setServiceRadiusKm] = useState(10.0);
  const [currentLat, setCurrentLat] = useState(18.5204);
  const [currentLng, setCurrentLng] = useState(73.8567);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { register } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get('/categories')
      .then((res) => {
        setCategories(res.data);
        if (res.data.length > 0 && selectedCatIds.length === 0) {
          setSelectedCatIds([res.data[0].id]);
        }
      })
      .catch((err) => console.error('Failed to load categories:', err));
  }, []);

  const toggleCategory = (id) => {
    setSelectedCatIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleUsePuneCoordinates = () => {
    setCurrentLat(18.5204);
    setCurrentLng(73.8567);
  };

  const handleUseGPSLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCurrentLat(parseFloat(pos.coords.latitude.toFixed(4)));
          setCurrentLng(parseFloat(pos.coords.longitude.toFixed(4)));
        },
        (err) => alert('Could not get GPS location: ' + err.message)
      );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (role === 'mechanic' && selectedCatIds.length === 0) {
      setError('Please select at least one service category.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        name: name.trim(),
        email: email.trim().toLowerCase(),
        phone: phone.trim(),
        password,
        role,
      };

      if (role === 'mechanic') {
        payload.category_ids = selectedCatIds;
        payload.service_radius_km = parseFloat(serviceRadiusKm);
        payload.current_lat = parseFloat(currentLat);
        payload.current_lng = parseFloat(currentLng);
      }

      await register(payload);
      navigate(role === 'mechanic' ? '/mechanic' : '/customer');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 py-8">
      <div className="max-w-lg w-full">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-emerald-400 items-center justify-center shadow-xl shadow-indigo-500/20 mb-3">
            <Wrench className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Create your Account</h2>
          <p className="text-sm text-slate-400 mt-1">Join FixItNow as a Customer or Technician</p>
        </div>

        {/* Role Selector Tabs */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <button
            type="button"
            onClick={() => setRole('customer')}
            className={`p-3 rounded-xl border font-semibold text-sm flex items-center justify-center space-x-2 transition-all ${
              role === 'customer'
                ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg shadow-indigo-500/20 ring-2 ring-indigo-500/30'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <User className="w-4 h-4" />
            <span>I need Repairs (Customer)</span>
          </button>
          <button
            type="button"
            onClick={() => setRole('mechanic')}
            className={`p-3 rounded-xl border font-semibold text-sm flex items-center justify-center space-x-2 transition-all ${
              role === 'mechanic'
                ? 'bg-emerald-600/20 border-emerald-500 text-white shadow-lg shadow-emerald-500/20 ring-2 ring-emerald-500/30'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <Hammer className="w-4 h-4" />
            <span>I'm a Mechanic (Partner)</span>
          </button>
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
                Full Name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Rahul Sharma"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="rahul@example.com"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Phone Number
                </label>
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+919800000001"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
              </div>
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

            {/* Mechanic Fields */}
            {role === 'mechanic' && (
              <div className="pt-4 border-t border-slate-800 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Service Categories Provided (Select all that apply)
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {categories.map((cat) => {
                      const isSelected = selectedCatIds.includes(cat.id);
                      return (
                        <button
                          key={cat.id}
                          type="button"
                          onClick={() => toggleCategory(cat.id)}
                          className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-between transition-all ${
                            isSelected
                              ? 'bg-emerald-950/60 border-emerald-500 text-emerald-300'
                              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                          }`}
                        >
                          <span className="truncate">{cat.name}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 ml-1" />}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Service Radius (km)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="100"
                    value={serviceRadiusKm}
                    onChange={(e) => setServiceRadiusKm(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Current Location (GPS Coordinates)
                    </label>
                    <div className="space-x-2">
                      <button
                        type="button"
                        onClick={handleUsePuneCoordinates}
                        className="text-[11px] text-indigo-400 hover:underline"
                      >
                        Use Pune Demo
                      </button>
                      <button
                        type="button"
                        onClick={handleUseGPSLocation}
                        className="text-[11px] text-emerald-400 hover:underline"
                      >
                        GPS
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="number"
                      step="0.0001"
                      required
                      value={currentLat}
                      onChange={(e) => setCurrentLat(e.target.value)}
                      placeholder="Latitude"
                      className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs"
                    />
                    <input
                      type="number"
                      step="0.0001"
                      required
                      value={currentLng}
                      onChange={(e) => setCurrentLng(e.target.value)}
                      placeholder="Longitude"
                      className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs"
                    />
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-emerald-600 hover:from-indigo-500 hover:to-emerald-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 mt-4"
            >
              <span>{loading ? 'Creating account...' : 'Complete Registration'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-400 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 font-semibold hover:text-indigo-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};
