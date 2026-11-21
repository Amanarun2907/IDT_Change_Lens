import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'danger' | 'warning' | 'success' | 'brand';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
}) => {
  const borderClasses = {
    default: 'hover:border-slate-700',
    danger: 'hover:border-red-500/40',
    warning: 'hover:border-amber-500/40',
    success: 'hover:border-emerald-500/40',
    brand: 'hover:border-blue-500/40',
  }[variant];

  const iconBgClasses = {
    default: 'bg-slate-800 text-slate-300',
    danger: 'bg-red-500/10 text-red-400',
    warning: 'bg-amber-500/10 text-amber-400',
    success: 'bg-emerald-500/10 text-emerald-400',
    brand: 'bg-blue-500/10 text-blue-400',
  }[variant];

  return (
    <div className={`glass-panel p-5 rounded-xl transition-all duration-200 ${borderClasses}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-lg ${iconBgClasses}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-white">{value}</div>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};
