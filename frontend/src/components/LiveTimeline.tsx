import React from 'react';
import { 
  CheckCircle2, 
  CircleDot, 
  AlertCircle, 
  Clock, 
  Bot, 
  GitBranch, 
  Code, 
  Bug, 
  ShieldCheck, 
  Share2, 
  TestTube, 
  FileText 
} from 'lucide-react';
import { ProgressEvent } from '../types';

interface LiveTimelineProps {
  events: ProgressEvent[];
  currentPercent: number;
}

const PIPELINE_STEPS = [
  { id: 'init', name: 'Repository / Diff Retrieval', icon: GitBranch, agent: 'system' },
  { id: 'plan', name: 'Coordinator Planning', icon: Bot, agent: 'coordinator' },
  { id: 'code_understanding', name: 'Code Understanding', icon: Code, agent: 'code_understanding' },
  { id: 'specialists', name: 'Specialist Investigation', icon: Share2, agent: 'multi_agents' },
  { id: 'risk_report', name: 'Risk Assessment & Synthesis', icon: FileText, agent: 'risk_report' }
];

export const LiveTimeline: React.FC<LiveTimelineProps> = ({ events, currentPercent }) => {
  const getStepStatus = (stepId: string) => {
    const matching = events.filter((e) => e.step_id === stepId);
    if (matching.length === 0) return 'pending';
    const last = matching[matching.length - 1];
    return last.status;
  };

  const getStepMessage = (stepId: string) => {
    const matching = events.filter((e) => e.step_id === stepId);
    if (matching.length === 0) return 'Waiting in queue...';
    return matching[matching.length - 1].message;
  };

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="font-semibold text-slate-200 flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              {currentPercent < 100 ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              )}
            </span>
            Multi-Agent Execution Pipeline
          </span>
          <span className="font-mono text-blue-400 font-bold">{currentPercent}%</span>
        </div>

        <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 h-full transition-all duration-300 ease-out"
            style={{ width: `${currentPercent}%` }}
          />
        </div>
      </div>

      {/* Step Grid / Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {PIPELINE_STEPS.map((step, idx) => {
          const status = getStepStatus(step.id);
          const message = getStepMessage(step.id);
          const Icon = step.icon;

          let cardBorder = 'border-slate-800 bg-slate-900/40 text-slate-400';
          let iconColor = 'text-slate-500 bg-slate-800';

          if (status === 'completed') {
            cardBorder = 'border-emerald-500/30 bg-emerald-950/15 text-emerald-300';
            iconColor = 'text-emerald-400 bg-emerald-500/10';
          } else if (status === 'running') {
            cardBorder = 'border-blue-500/50 bg-blue-950/20 text-blue-300 ring-1 ring-blue-500/30';
            iconColor = 'text-blue-400 bg-blue-500/15 animate-pulse';
          } else if (status === 'failed') {
            cardBorder = 'border-red-500/40 bg-red-950/20 text-red-300';
            iconColor = 'text-red-400 bg-red-500/10';
          }

          return (
            <div key={step.id} className={`glass-panel p-4 rounded-xl border transition-all ${cardBorder}`}>
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${iconColor}`}>
                  <Icon className="w-4 h-4" />
                </div>
                {status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : status === 'running' ? (
                  <div className="w-3.5 h-3.5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                ) : status === 'failed' ? (
                  <AlertCircle className="w-4 h-4 text-red-400" />
                ) : (
                  <Clock className="w-3.5 h-3.5 text-slate-600" />
                )}
              </div>
              <div className="text-xs font-semibold tracking-tight">{step.name}</div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-tight">
                {message}
              </p>
            </div>
          );
        })}
      </div>

      {/* Live Agent Event Terminal */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span>
            Agent Activity Logs (SSE Live Stream)
          </span>
          <span className="text-[11px] text-slate-500 font-mono">{events.length} messages received</span>
        </div>

        <div className="p-4 max-h-56 overflow-y-auto font-mono text-xs space-y-1.5 bg-[#090d16]">
          {events.length === 0 ? (
            <div className="text-slate-600 italic">Waiting for pipeline events...</div>
          ) : (
            events.map((e, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className="text-slate-600 select-none text-[10px]">
                  {new Date(e.timestamp).toLocaleTimeString()}
                </span>
                <span className={`text-[10px] font-semibold uppercase px-1 rounded ${
                  e.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                  e.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'
                }`}>
                  [{e.agent_name || 'system'}]
                </span>
                <span className="text-slate-300">{e.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
