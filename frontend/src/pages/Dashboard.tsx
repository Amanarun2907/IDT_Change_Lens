import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  GitBranch, 
  GitPullRequest, 
  Code, 
  AlertTriangle, 
  ShieldAlert, 
  TrendingUp, 
  CheckCircle, 
  Activity, 
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { api } from '../api';
import { DashboardStats } from '../types';
import { MetricCard } from '../components/MetricCard';
import { RiskBadge } from '../components/RiskBadge';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Welcome & Quick Launch */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Change Intelligence Overview
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time repository risk assessment, downstream impact tracing, and blast radius analytics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadStats}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-xs text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link
            to="/new"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/25 transition-all"
          >
            New Analysis
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Analyses"
          value={stats?.total_analyses ?? 0}
          subtitle="Processed via Multi-Agent pipeline"
          icon={Activity}
          variant="brand"
        />
        <MetricCard
          title="Critical Findings"
          value={stats?.critical_findings ?? 0}
          subtitle="Severe vulnerabilities & blockers"
          icon={ShieldAlert}
          variant="danger"
        />
        <MetricCard
          title="High-Risk Changes"
          value={stats?.high_risk_changes ?? 0}
          subtitle="Score > 55 or breaking API"
          icon={AlertTriangle}
          variant="warning"
        />
        <MetricCard
          title="Security Issues"
          value={stats?.security_vulnerabilities ?? 0}
          subtitle="OWASP & CWE detections"
          icon={ShieldAlert}
          variant="danger"
        />
        <MetricCard
          title="Avg Risk Score"
          value={`${stats?.average_risk_score ?? 0} / 100`}
          subtitle="Evidence-weighted index"
          icon={TrendingUp}
          variant="default"
        />
      </div>

      {/* Mode Quick Launch Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/new?mode=repo"
          className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-blue-500/40 transition-all group"
        >
          <div className="p-3 w-fit rounded-lg bg-blue-500/10 text-blue-400 group-hover:scale-110 transition-transform">
            <GitBranch className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white mt-4 group-hover:text-blue-400 transition-colors">
            Mode A: GitHub Repository
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Clone or inspect public/private repos, select branches or commits, and analyze deep downstream call-graphs.
          </p>
        </Link>

        <Link
          to="/new?mode=pr"
          className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-indigo-500/40 transition-all group"
        >
          <div className="p-3 w-fit rounded-lg bg-indigo-500/10 text-indigo-400 group-hover:scale-110 transition-transform">
            <GitPullRequest className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white mt-4 group-hover:text-indigo-400 transition-colors">
            Mode B: Pull Request Review
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Paste a GitHub PR URL to generate pre-merge advisory decisions (APPROVE / REQUEST CHANGES) and GitHub review comments.
          </p>
        </Link>

        <Link
          to="/new?mode=manual"
          className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-cyan-500/40 transition-all group"
        >
          <div className="p-3 w-fit rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:scale-110 transition-transform">
            <Code className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white mt-4 group-hover:text-cyan-400 transition-colors">
            Mode C: Manual Code Comparison
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Paste original and updated code snippets to immediately generate structured diffs and run the specialist agents.
          </p>
        </Link>
      </div>

      {/* Trend Chart & Recent Analyses Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Trend Chart */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200">Risk Score Trends</h3>
            <span className="text-xs text-slate-500">Recent Sessions</span>
          </div>
          {stats?.trends && stats.trends.length > 0 ? (
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.trends}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="session_id" stroke="#475569" fontSize={10} />
                  <YAxis domain={[0, 100]} stroke="#475569" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: '#60a5fa' }}
                  />
                  <Area type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#scoreGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-56 flex items-center justify-center text-xs text-slate-500 italic">
              Run analyses to populate trends.
            </div>
          )}
        </div>

        {/* Recent Analyses Table */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200">Recent Analyses</h3>
            <Link to="/history" className="text-xs text-blue-400 hover:text-blue-300 font-medium">
              View All History &rarr;
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">Target</th>
                  <th className="py-2 px-3">Mode</th>
                  <th className="py-2 px-3">Risk Score</th>
                  <th className="py-2 px-3">Blast Radius</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {stats?.recent_analyses && stats.recent_analyses.length > 0 ? (
                  stats.recent_analyses.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3 font-sans font-medium text-slate-200 max-w-[200px] truncate">
                        {item.pr_title || item.pr_url || item.repo_url || `Snippet #${item.id.slice(0, 8)}`}
                      </td>
                      <td className="py-2.5 px-3 uppercase text-[10px] text-slate-400">
                        {item.mode.replace('_', ' ')}
                      </td>
                      <td className="py-2.5 px-3">
                        {item.overall_score !== undefined && item.overall_score !== null ? (
                          <RiskBadge level={item.risk_category || 'LOW'} size="sm" />
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-300">
                        {item.blast_radius || 'LOCALIZED'}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-sans ${
                          item.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                          item.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'
                        }`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Link
                          to={item.status === 'completed' ? `/report/${item.id}` : `/live/${item.id}`}
                          className="text-blue-400 hover:text-blue-300 font-sans text-xs font-medium"
                        >
                          View &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 italic">
                      No analyses recorded yet. Start your first analysis above!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
