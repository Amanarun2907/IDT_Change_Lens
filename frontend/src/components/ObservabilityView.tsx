import React, { useState } from 'react';
import { 
  Activity, 
  Clock, 
  Zap, 
  DollarSign, 
  Cpu, 
  ShieldCheck, 
  Layers, 
  ChevronDown, 
  ChevronRight, 
  ExternalLink,
  Hash,
  Terminal,
  CheckCircle2,
  BarChart3,
  TrendingUp,
  FileCode2
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';
import { ObservabilityReport, TraceSpan } from '../types';

interface ObservabilityViewProps {
  report?: ObservabilityReport;
  sessionId: string;
}

export const ObservabilityView: React.FC<ObservabilityViewProps> = ({ report, sessionId }) => {
  const [expandedSpanId, setExpandedSpanId] = useState<string | null>(null);
  const [selectedAgentTab, setSelectedAgentTab] = useState<'latency' | 'tokens' | 'cost'>('latency');

  if (!report || !report.spans || report.spans.length === 0) {
    return (
      <div className="glass-panel p-8 text-center rounded-2xl border border-slate-800 space-y-3">
        <Activity className="w-10 h-10 text-slate-500 mx-auto animate-pulse" />
        <h3 className="text-base font-semibold text-white">Observability Telemetry Processing</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Detailed span waterfall, token usage, and cost audit data will appear once the multi-agent coordinator finishes tracing this session ({sessionId}).
        </p>
      </div>
    );
  }

  // Calculate timeline boundaries for the Gantt waterfall
  const startTimes = report.spans.map((s) => new Date(s.start_time_iso).getTime()).filter(Boolean);
  const minTime = startTimes.length > 0 ? Math.min(...startTimes) : 0;
  const maxWallTime = Math.max(report.total_wall_time_ms, 1);

  // Agent color mapping for visual waterfall & charts
  const getAgentColor = (name?: string) => {
    if (!name) return '#64748b';
    if (name.includes('coordinator')) return '#3b82f6';
    if (name.includes('understanding') || name.includes('change_analysis')) return '#8b5cf6';
    if (name.includes('bug')) return '#f59e0b';
    if (name.includes('security')) return '#ef4444';
    if (name.includes('testing') || name.includes('impact')) return '#06b6d4';
    if (name.includes('risk') || name.includes('report')) return '#10b981';
    return '#6366f1';
  };

  const chartData = report.agent_metrics.map((m) => ({
    name: m.agent_name.replace('agent:', '').replace('_', ' '),
    duration: Math.round(m.duration_ms),
    tokens: m.tokens,
    cost: Number((m.cost_usd * 1000).toFixed(4)), // display in millidollars or fraction
    rawCost: m.cost_usd,
    model: m.model,
    findings: m.findings_count
  }));

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner: Transparency & Anti-Black Box Philosophy */}
      <div className="p-6 rounded-2xl glass-panel border border-blue-500/30 bg-gradient-to-r from-blue-950/20 via-slate-900/60 to-indigo-950/20 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-1 rounded bg-blue-500/20 text-blue-400">
                <Activity className="w-4 h-4" />
              </span>
              <h2 className="text-lg font-bold text-white tracking-tight">
                ChangeLens Agent Observability &amp; Provenance Engine
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                OTel / Langfuse Compatible
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Every LLM invocation, intermediate reasoning step, and concurrent execution span is tracked with exact duration, token allocation, deterministic cost calculation (USD), and SHA-256 provenance hashes to eliminate black-box unpredictability.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center font-mono text-[11px] bg-slate-950/80 px-3 py-2 rounded-xl border border-slate-800 text-slate-400">
            <Hash className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-500">Trace:</span>
            <span className="text-slate-200 select-all">{report.trace_id.slice(0, 18)}...</span>
          </div>
        </div>
      </div>

      {/* Primary KPI Grid: Speedup, Cost, Wall Time, Tokens */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Wall Time & Sequential Time */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Wall-Clock Time</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white tracking-tight">
              {(report.total_wall_time_ms / 1000).toFixed(2)}s
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Sequential: <span className="line-through text-slate-500">{(report.sequential_time_ms / 1000).toFixed(2)}s</span>
            </div>
          </div>
        </div>

        {/* Parallel Concurrency Speedup */}
        <div className="glass-panel p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400 text-xs">
            <span>Concurrency Speedup</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-emerald-400 tracking-tight flex items-center gap-1.5">
              <span>{report.parallel_speedup_factor.toFixed(2)}x</span>
              <TrendingUp className="w-4 h-4" />
            </div>
            <div className="text-[11px] text-emerald-300/80 mt-0.5">
              Async multi-agent fan-out
            </div>
          </div>
        </div>

        {/* Token Consumption */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Tokens</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white tracking-tight">
              {report.total_tokens.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2">
              <span>In: {report.total_prompt_tokens.toLocaleString()}</span>
              <span>&middot;</span>
              <span>Out: {report.total_completion_tokens.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Exact Cost Evaluation */}
        <div className="glass-panel p-4 rounded-xl border border-amber-500/20 bg-amber-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-amber-400 text-xs">
            <span>Calculated Cost</span>
            <DollarSign className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-amber-300 font-mono tracking-tight">
              ${report.total_cost_usd.toFixed(6)}
            </div>
            <div className="text-[11px] text-amber-400/70 mt-0.5">
              USD (Exact blended model pricing)
            </div>
          </div>
        </div>
      </div>

      {/* Visual Gantt Waterfall Chart of Agent Spans */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              Agent Execution Waterfall (Gantt Trace)
            </h3>
            <p className="text-xs text-slate-400">
              Visualizes asynchronous agent concurrency vs sequential stages. Click any span to inspect LLM provenance and inputs.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              Plan / Orchestrate
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
              Concurrent Specialists
            </span>
          </div>
        </div>

        {/* Gantt Timeline Axis */}
        <div className="relative pt-2">
          <div className="flex justify-between text-[10px] text-slate-500 font-mono border-b border-slate-800 pb-1 mb-3">
            <span>0 ms (T-Zero)</span>
            <span>{Math.round(maxWallTime * 0.25)} ms</span>
            <span>{Math.round(maxWallTime * 0.50)} ms</span>
            <span>{Math.round(maxWallTime * 0.75)} ms</span>
            <span>{Math.round(maxWallTime)} ms (Wall-Clock End)</span>
          </div>

          {/* Span Rows */}
          <div className="space-y-2.5">
            {report.spans.map((span) => {
              const spanStart = new Date(span.start_time_iso).getTime();
              const offsetMs = Math.max(0, spanStart - minTime);
              const leftPercent = Math.min(95, Math.max(0, (offsetMs / maxWallTime) * 100));
              const widthPercent = Math.min(100 - leftPercent, Math.max(4, (span.duration_ms / maxWallTime) * 100));
              const isExpanded = expandedSpanId === span.span_id;
              const color = getAgentColor(span.agent_name || span.name);

              return (
                <div key={span.span_id} className="group">
                  {/* Row Bar */}
                  <div 
                    onClick={() => setExpandedSpanId(isExpanded ? null : span.span_id)}
                    className="p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/60 border border-slate-800/80 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2 text-xs mb-1.5">
                      <div className="flex items-center gap-2 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        )}
                        <span className="font-semibold text-white truncate font-mono text-[11px]">
                          {span.name}
                        </span>
                        {span.agent_name && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                            {span.agent_name.replace('agent:', '')}
                          </span>
                        )}
                        {span.model_name && (
                          <span className="text-[10px] text-slate-500 font-mono hidden md:inline">
                            [{span.model_name}]
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-[11px] font-mono shrink-0">
                        <span className="text-slate-300 font-bold">{Math.round(span.duration_ms)} ms</span>
                        <span className="text-purple-400 hidden sm:inline">{span.total_tokens} tok</span>
                        <span className="text-amber-400 hidden sm:inline">${span.cost_usd.toFixed(6)}</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                          span.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                        }`}>
                          {span.status}
                        </span>
                      </div>
                    </div>

                    {/* Visual Gantt Bar */}
                    <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden relative">
                      <div 
                        className="h-full rounded-full transition-all duration-300 shadow-sm"
                        style={{
                          marginLeft: `${leftPercent}%`,
                          width: `${widthPercent}%`,
                          backgroundColor: color,
                        }}
                      />
                    </div>
                  </div>

                  {/* Expanded Span Details: Provenance, Model, Snippets */}
                  {isExpanded && (
                    <div className="mt-1.5 p-4 rounded-xl bg-[#090d16] border border-slate-800/90 text-xs space-y-3 font-mono">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-slate-400">
                        <div>
                          <span className="text-slate-500">Span ID:</span>{' '}
                          <span className="text-slate-200">{span.span_id.slice(0, 12)}...</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Parent Span:</span>{' '}
                          <span className="text-slate-200">{span.parent_span_id ? span.parent_span_id.slice(0, 12) + '...' : 'None (Root)'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Tokens:</span>{' '}
                          <span className="text-purple-300">Prompt: {span.prompt_tokens} &middot; Output: {span.completion_tokens}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Provenance Hash:</span>{' '}
                          <span className="text-cyan-300">{span.provenance_hash?.slice(0, 10)}...</span>
                        </div>
                      </div>

                      {span.input_snippet && (
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Agent Input Context Snippet</div>
                          <pre className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-36">
                            {span.input_snippet}
                          </pre>
                        </div>
                      )}

                      {span.output_snippet && (
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Structured Reasoning &amp; Finding Output</div>
                          <pre className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-emerald-300/90 overflow-x-auto whitespace-pre-wrap max-h-36">
                            {span.output_snippet}
                          </pre>
                        </div>
                      )}

                      {span.error_message && (
                        <div className="p-2 rounded bg-red-950/30 border border-red-500/30 text-red-400 text-xs">
                          <b>Error:</b> {span.error_message}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Multi-Agent Performance & Cost Analytics Graphs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency by Agent Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              Specialist Agent Latency Comparison (ms)
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">Lower is faster</span>
          </div>

          <div className="h-64 w-full pt-2">
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
                  formatter={(value: any) => [`${value} ms`, 'Duration']}
                />
                <Bar dataKey="duration" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getAgentColor(entry.name)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tokens & Cost Breakdown Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-amber-400" />
              Token &amp; Cost Allocation by Agent
            </h3>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setSelectedAgentTab('tokens')}
                className={`px-2 py-0.5 rounded text-xs transition-colors ${
                  selectedAgentTab === 'tokens' ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}
              >
                Tokens
              </button>
              <button 
                onClick={() => setSelectedAgentTab('cost')}
                className={`px-2 py-0.5 rounded text-xs transition-colors ${
                  selectedAgentTab === 'cost' ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}
              >
                Cost ($)
              </button>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
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
                  formatter={(value: any) => [
                    selectedAgentTab === 'cost' ? `$${(value / 1000).toFixed(6)}` : `${value.toLocaleString()} tokens`,
                    selectedAgentTab === 'cost' ? 'Cost (USD)' : 'Tokens'
                  ]}
                />
                <Bar 
                  dataKey={selectedAgentTab === 'cost' ? 'cost' : 'tokens'} 
                  fill={selectedAgentTab === 'cost' ? '#f59e0b' : '#a855f7'} 
                  radius={[6, 6, 0, 0]} 
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Auditability & Provenance Timeline: Eliminating the Black Box */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Verifiable Provenance &amp; Audit Log
            </h3>
            <p className="text-xs text-slate-400">
              Immutable event trail verifying the origin, model provider, and reasoning chain of all generated findings.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
            {report.audit_events.length} Events Verified
          </span>
        </div>

        <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {report.audit_events.map((ev, idx) => (
            <div key={idx} className="relative group">
              <div className="absolute -left-6 top-1.5 w-2.5 h-2.5 rounded-full bg-blue-500 ring-4 ring-slate-900 group-hover:bg-emerald-400 transition-colors" />
              <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/80 hover:border-slate-700 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{ev.event}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-blue-400 font-mono">
                      {ev.agent}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                {ev.details && (
                  <p className="text-[11px] text-slate-400 font-mono leading-relaxed mt-1">
                    {ev.details}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
export default ObservabilityView;
