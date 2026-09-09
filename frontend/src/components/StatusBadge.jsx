import React from 'react';

const STATUS_STYLES = {
  REQUESTED: 'bg-slate-800 text-slate-300 border-slate-700',
  BROADCASTING: 'bg-indigo-950/80 text-indigo-300 border-indigo-700/60 animate-pulse',
  ACCEPTED: 'bg-blue-950/80 text-blue-300 border-blue-700/60',
  EN_ROUTE: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
  IN_PROGRESS: 'bg-purple-950/80 text-purple-300 border-purple-700/60',
  COMPLETED: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
  CANCELLED_BY_CUSTOMER: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
  CANCELLED_BY_MECHANIC: 'bg-orange-950/80 text-orange-300 border-orange-700/60',
  EXPIRED: 'bg-zinc-800/80 text-zinc-400 border-zinc-700',
};

const STATUS_LABELS = {
  REQUESTED: 'Requested',
  BROADCASTING: 'Searching Mechanics...',
  ACCEPTED: 'Mechanic Assigned',
  EN_ROUTE: 'Mechanic En Route',
  IN_PROGRESS: 'Repair In Progress',
  COMPLETED: 'Completed',
  CANCELLED_BY_CUSTOMER: 'Cancelled by Customer',
  CANCELLED_BY_MECHANIC: 'Cancelled by Mechanic',
  EXPIRED: 'Request Expired',
};

export const StatusBadge = ({ status, className = '' }) => {
  const style = STATUS_STYLES[status] || 'bg-slate-800 text-slate-300 border-slate-700';
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${style} ${className}`}
    >
      {status === 'BROADCASTING' && (
        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mr-1.5 animate-ping" />
      )}
      {status === 'IN_PROGRESS' && (
        <span className="w-1.5 h-1.5 rounded-full bg-purple-400 mr-1.5 animate-pulse" />
      )}
      {status === 'COMPLETED' && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5" />
      )}
      {label}
    </span>
  );
};
