import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowRight, AlertCircle, Layers } from 'lucide-react';
import { LiveTimeline } from '../components/LiveTimeline';
import { ProgressEvent } from '../types';
import { api } from '../api';

export const LiveProgress: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();

  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [percent, setPercent] = useState<number>(10);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    let isMounted = true;
    const eventSource = new EventSource(`/api/analysis/${sessionId}/stream`);

    eventSource.onmessage = (e) => {
      if (!isMounted) return;
      try {
        const data: ProgressEvent = JSON.parse(e.data);
        setEvents((prev) => {
          // Avoid duplicate messages
          const exists = prev.some(
            (p) => p.step_id === data.step_id && p.message === data.message && p.percent === data.percent
          );
          return exists ? prev : [...prev, data];
        });

        if (data.percent) {
          setPercent(data.percent);
        }
        if (data.status === 'completed' && data.percent === 100) {
          setIsCompleted(true);
          eventSource.close();
        } else if (data.status === 'failed') {
          setError(data.message || 'Analysis failed.');
          eventSource.close();
        }
      } catch (err) {
        console.error('Error parsing SSE event', err);
      }
    };

    // Backup polling check: if stream disconnects or completes
    const pollInterval = setInterval(async () => {
      if (!isMounted || isCompleted) return;
      try {
        const rep = await api.getReport(sessionId);
        if (rep && isMounted) {
          setPercent(100);
          setIsCompleted(true);
          eventSource.close();
          clearInterval(pollInterval);
        }
      } catch (err) {
        // Still processing
      }
    }, 2500);

    return () => {
      isMounted = false;
      eventSource.close();
      clearInterval(pollInterval);
    };
  }, [sessionId, isCompleted]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Live Multi-Agent Analysis</h1>
            <span className="px-2 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
              {sessionId?.slice(0, 8)}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Specialist AI agents are investigating code modifications, calculating dependency blast radius, and assessing regressions.
          </p>
        </div>

        {isCompleted && (
          <Link
            to={`/report/${sessionId}`}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-500/25 transition-all hover:scale-105"
          >
            <span>View Full Report</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Analysis Failure</div>
            <p className="text-xs text-red-200/90 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Real-time Timeline Component */}
      <LiveTimeline events={events} currentPercent={percent} />

      {isCompleted && (
        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 text-center space-y-4">
          <div className="inline-flex p-3 rounded-full bg-emerald-500/20 text-emerald-400">
            <Layers className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Analysis Pipeline Completed</h3>
            <p className="text-xs text-slate-300 max-w-lg mx-auto mt-1">
              Code understanding, bug analysis, contextual security review, dependency call-graph extraction, and transparent risk scoring have finished.
            </p>
          </div>
          <Link
            to={`/report/${sessionId}`}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/20 transition-all hover:scale-105"
          >
            <span>Open Executive Change Report</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
};
