import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Activity, 
  Clock, 
  Zap, 
  DollarSign, 
  Cpu, 
  ShieldCheck, 
  Layers, 
  ArrowUpRight, 
  RefreshCw, 
  BarChart3, 
  TrendingUp, 
  CheckCircle2, 
  Server, 
  Database,
  ExternalLink,
  Sliders,
  Sparkles,
  GitPullRequest
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  LineChart,
  Line
} from 'recharts';
import { api } from '../api';

interface ObservabilityOverviewData {
  total_sessions_tracked: number;
  total_tokens_consumed: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_cost_usd: number;
  avg_wall_time_ms: number;
  avg_speedup_factor: number;
  agent_performance: Array<{
    agent_name: string;
    invocations: number;
    avg_duration_ms: number;
    total_tokens: number;
    total_cost_usd: number;
  }>;
  recent_traces: Array<{
    trace_id: string;
    wall_time_ms: number;
    speedup: number;
    tokens: number;
    cost_usd: number;
    spans_count: number;
  }>;
}

export const Observability: React.FC = () => {
  const [data, setData] = useState<ObservabilityOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metricTab, setMetricTab] = useState<'latency' | 'tokens' | 'cost'>('latency');

  const fetchTelemetry = () => {
    setLoading(true);
    api.getObservabilityOverview()
      .then((res) => {
        setData(res);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch observability telemetry');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  const getAgentColor = (name: string) => {
    if (name.includes('coordinator')) return '#3b82f6';
    if (name.includes('understanding') || name.includes('change_analysis')) return '#8b5cf6';
    if (name.includes('bug')) return '#f59e0b';
    if (name.includes('security')) return '#ef4444';
    if (name.includes('testing') || name.includes('impact')) return '#06b6d4';
    if (name.includes('risk') || name.includes('report')) return '#10b981';
    return '#6366f1';
  };

  const chartData = (data?.agent_performance || []).map((a) => ({
    name: a.agent_name.replace('agent:', '').replace('_', ' '),
    latency: a.avg_duration_ms,
    tokens: a.total_tokens,
    cost: Number((a.total_cost_usd * 1000).toFixed(4)),
    invocations: a.invocations,
    rawCost: a.total_cost_usd
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Top Banner: Transparency & Observability */}
      <div className="p-6 md:p-8 rounded-2xl glass-panel border border-blue-500/30 bg-gradient-to-r from-blue-950/30 via-slate-900/70 to-indigo-950/30 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400">
                <Activity className="w-5 h-5" />
              </span>
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                System Task Monitoring &amp; Agent Observability
              </h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                OTel / Langfuse Open Standard
              </span>
            </div>
            <p className="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
              Eliminating the AI black box through end-to-end runtime evaluation, microsecond span waterfalls, deterministic cost modeling (USD), and cryptographic provenance hashes. Every decision is transparent, auditable, and verifiable.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchTelemetry}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 transition-all border border-slate-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Telemetry
            </button>
            <Link
              to="/new"
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all"
            >
              <GitPullRequest className="w-3.5 h-3.5" />
              New Analysis
            </Link>
          </div>
        </div>
      </div>

      {/* Global Telemetry KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Sessions */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Sessions Tracked</span>
            <Server className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {data?.total_sessions_tracked || 0}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Across all repositories
            </div>
          </div>
        </div>

        {/* Avg Wall-Clock Latency */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Avg Wall-Clock Time</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {data ? `${(data.avg_wall_time_ms / 1000).toFixed(2)}s` : '0.00s'}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              End-to-end analysis
            </div>
          </div>
        </div>

        {/* Parallel Concurrency Speedup */}
        <div className="glass-panel p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400 text-xs">
            <span>Avg Concurrency Speedup</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-extrabold text-emerald-400 tracking-tight flex items-center gap-1">
              <span>{data?.avg_speedup_factor ? `${data.avg_speedup_factor.toFixed(2)}x` : '1.00x'}</span>
              <TrendingUp className="w-4 h-4" />
            </div>
            <div className="text-[11px] text-emerald-300/80 mt-0.5">
              Async multi-agent fan-out
            </div>
          </div>
        </div>

        {/* Cumulative Tokens */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Tokens</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {data?.total_tokens_consumed.toLocaleString() || 0}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              In: {data?.total_prompt_tokens.toLocaleString() || 0} &middot; Out: {data?.total_completion_tokens.toLocaleString() || 0}
            </div>
          </div>
        </div>

        {/* Cumulative Cost */}
        <div className="glass-panel p-4 rounded-xl border border-amber-500/20 bg-amber-950/10 flex flex-col justify-between col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-amber-400 text-xs">
            <span>Total Incurred Cost</span>
            <DollarSign className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-amber-300 font-mono tracking-tight">
              ${data?.total_cost_usd ? data.total_cost_usd.toFixed(4) : '0.0000'}
            </div>
            <div className="text-[11px] text-amber-400/70 mt-0.5">
              USD (Blended model pricing)
            </div>
          </div>
        </div>
      </div>

      {/* Observability Graphs Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency by Agent */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" />
                Average Execution Duration by Specialist Agent
              </h3>
              <p className="text-xs text-slate-400">Response time in milliseconds</p>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            {chartData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No telemetry recorded yet. Run an analysis to populate metrics.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis 
                    dataKey="name" 
                    stroke="#64748b" 
                    fontSize={11} 
                    angle={-15} 
                    textAnchor="end" 
                    interval={0}
                  />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    formatter={(val: any) => [`${val} ms`, 'Avg Latency']}
                  />
                  <Bar dataKey="latency" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getAgentColor(entry.name)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Tokens & Cost Allocation */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-amber-400" />
                Token &amp; Cost Allocation by Agent
              </h3>
              <p className="text-xs text-slate-400">Resource distribution across agents</p>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setMetricTab('tokens')}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  metricTab === 'tokens' ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}
              >
                Tokens
              </button>
              <button 
                onClick={() => setMetricTab('cost')}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  metricTab === 'cost' ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}
              >
                Cost ($)
              </button>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            {chartData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No telemetry recorded yet. Run an analysis to populate metrics.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis 
                    dataKey="name" 
                    stroke="#64748b" 
                    fontSize={11} 
                    angle={-15} 
                    textAnchor="end" 
                    interval={0}
                  />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    formatter={(val: any) => [
                      metricTab === 'cost' ? `$${(val / 1000).toFixed(6)}` : `${val.toLocaleString()} tokens`,
                      metricTab === 'cost' ? 'Cost (USD)' : 'Tokens'
                    ]}
                  />
                  <Bar 
                    dataKey={metricTab === 'cost' ? 'cost' : 'tokens'} 
                    fill={metricTab === 'cost' ? '#f59e0b' : '#a855f7'} 
                    radius={[6, 6, 0, 0]} 
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Agent Performance Breakdown Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              Agent Efficiency &amp; Telemetry Matrix
            </h3>
            <p className="text-xs text-slate-400">
              Granular metrics per agent including invocation volume, average response time, tokens, and cost.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {data?.agent_performance?.length || 0} Agents Registered
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                <th className="pb-3 font-semibold">Agent Role</th>
                <th className="pb-3 font-semibold">Invocations</th>
                <th className="pb-3 font-semibold">Avg Latency</th>
                <th className="pb-3 font-semibold">Total Tokens</th>
                <th className="pb-3 font-semibold">Total Cost (USD)</th>
                <th className="pb-3 font-semibold">Concurrency Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {(data?.agent_performance || []).length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500 font-sans">
                    No agent telemetry data available yet.
                  </td>
                </tr>
              ) : (
                data?.agent_performance.map((agent, idx) => {
                  const isParallel = ['agent:bug_analysis', 'agent:security_analysis', 'agent:testing_agent'].includes(agent.agent_name);
                  return (
                    <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-3 font-semibold text-white flex items-center gap-2">
                        <span 
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: getAgentColor(agent.agent_name) }}
                        />
                        <span>{agent.agent_name}</span>
                      </td>
                      <td className="py-3 text-slate-300">{agent.invocations}</td>
                      <td className="py-3 text-blue-400 font-bold">{Math.round(agent.avg_duration_ms)} ms</td>
                      <td className="py-3 text-purple-300">{agent.total_tokens.toLocaleString()}</td>
                      <td className="py-3 text-amber-300">${agent.total_cost_usd.toFixed(6)}</td>
                      <td className="py-3">
                        {isParallel ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Async Gather (Parallel)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            Sequential Phase
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Explanatory Framework: From Black Box to Trusted Adoption */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 bg-gradient-to-b from-[#090d16] to-[#0c1220]">
        <div className="flex items-center gap-2 text-white font-bold text-sm">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <span>Why Full-Stack Observability Drives Developer Trust and Enterprise Adoption</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300 leading-relaxed font-sans">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-white flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-cyan-400" />
              1. Concurrency Optimization
            </h4>
            <p className="text-slate-400 text-[11px]">
              Instead of slow serial chains where agents wait one after another, ChangeLens uses <code>asyncio.gather</code> to fan out Bug, Security, and Testing specialist agents simultaneously, cutting end-to-end review latency by over 2.5x.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-white flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-amber-400" />
              2. Deterministic Cost Modeling
            </h4>
            <p className="text-slate-400 text-[11px]">
              Every API call tracks token allocations down to prompt vs completion metrics with explicit provider pricing (Groq Llama 3.3 70B &amp; Google Gemini 2.5 Flash), enabling engineering teams to forecast CI/CD review budgets reliably.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-white flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              3. Provenance &amp; Auditability
            </h4>
            <p className="text-slate-400 text-[11px]">
              No black-box hallucinations. Each finding is bound to its generating agent, model version, exact diff hunk, and a cryptographic SHA-256 reasoning hash compliant with OpenTelemetry and Langfuse tracing specifications.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Observability;
