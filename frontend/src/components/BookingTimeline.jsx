import React from 'react';
import { CheckCircle2, Clock, MapPin, Wrench, CheckCheck, AlertCircle } from 'lucide-react';

const STEPS = [
  { id: 'REQUESTED', label: 'Requested', icon: Clock },
  { id: 'BROADCASTING', label: 'Finding Mechanic', icon: MapPin },
  { id: 'ACCEPTED', label: 'Accepted', icon: CheckCircle2 },
  { id: 'EN_ROUTE', label: 'En Route', icon: MapPin },
  { id: 'IN_PROGRESS', label: 'In Progress', icon: Wrench },
  { id: 'COMPLETED', label: 'Completed', icon: CheckCheck },
];

export const BookingTimeline = ({ status }) => {
  const isCancelled = status?.startsWith('CANCELLED');
  const isExpired = status === 'EXPIRED';

  if (isCancelled || isExpired) {
    return (
      <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/40 flex items-center space-x-3 text-rose-300">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        <div>
          <span className="font-semibold block">Booking Terminated</span>
          <span className="text-xs text-rose-400">
            {isExpired ? 'Request expired because no mechanic accepted in time.' : `Cancelled: ${status}`}
          </span>
        </div>
      </div>
    );
  }

  const stepOrder = STEPS.map((s) => s.id);
  const currentIndex = stepOrder.indexOf(status);

  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between relative">
        {/* Background track line */}
        <div className="absolute top-1/2 left-0 right-0 h-1 bg-slate-800 -translate-y-1/2 z-0" />
        {/* Active progress line */}
        <div
          className="absolute top-1/2 left-0 h-1 bg-gradient-to-r from-indigo-500 to-emerald-500 -translate-y-1/2 z-0 transition-all duration-500"
          style={{
            width: `${Math.max(0, (currentIndex / (STEPS.length - 1)) * 100)}%`,
          }}
        />

        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isDone = idx < currentIndex;
          const isCurrent = idx === currentIndex;

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center group">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                  isDone
                    ? 'bg-emerald-500 border-emerald-400 text-slate-950 shadow-md shadow-emerald-500/30'
                    : isCurrent
                    ? 'bg-indigo-600 border-indigo-400 text-white ring-4 ring-indigo-500/20 shadow-lg shadow-indigo-600/40 scale-110'
                    : 'bg-slate-900 border-slate-700 text-slate-500'
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <span
                className={`text-[11px] font-semibold mt-2 text-center absolute -bottom-6 whitespace-nowrap transition-colors ${
                  isCurrent ? 'text-indigo-400 font-bold' : isDone ? 'text-emerald-400' : 'text-slate-500'
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
      <div className="h-6" /> {/* Spacer for bottom labels */}
    </div>
  );
};
