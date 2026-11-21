import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, AlertCircle } from 'lucide-react';
import { RiskCategory, Severity, AdvisoryRecommendation } from '../types';

interface RiskBadgeProps {
  level: RiskCategory | Severity | AdvisoryRecommendation | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, size = 'md', showIcon = true }) => {
  const normalized = String(level).toUpperCase();

  let colorClasses = 'bg-slate-800/80 text-slate-300 border-slate-700';
  let Icon = AlertCircle;

  if (normalized === 'CRITICAL' || normalized === 'REQUEST_CHANGES') {
    colorClasses = 'bg-red-500/10 text-red-400 border-red-500/30';
    Icon = ShieldAlert;
  } else if (normalized === 'HIGH') {
    colorClasses = 'bg-orange-500/10 text-orange-400 border-orange-500/30';
    Icon = AlertTriangle;
  } else if (normalized === 'MEDIUM' || normalized === 'NEEDS_HUMAN_REVIEW') {
    colorClasses = 'bg-amber-500/10 text-amber-300 border-amber-500/30';
    Icon = AlertTriangle;
  } else if (normalized === 'LOW' || normalized === 'APPROVE') {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    Icon = ShieldCheck;
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-semibold'
  }[size];

  return (
    <span className={`inline-flex items-center rounded-full border ${colorClasses} ${sizeClasses}`}>
      {showIcon && <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />}
      <span>{normalized.replace(/_/g, ' ')}</span>
    </span>
  );
};
