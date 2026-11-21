import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import { AnalysisReport } from '../types';
import { DiffViewer } from '../components/DiffViewer';
import { ArrowLeft, FileCode, ShieldAlert } from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';

export const CodeExplorer: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;
    api.getReport(sessionId)
      .then((data) => setReport(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-xl mx-auto my-12 text-center text-slate-400">
        Session not found. <Link to="/history" className="text-blue-400">Back to History</Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link
            to={`/report/${sessionId}`}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">Repository Code Explorer</h1>
              <RiskBadge level={report.risk_assessment.risk_category} size="sm" />
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              {report.pr_title || report.repo_url || 'Manual Code Comparison'} · {report.changed_files.length} changed files
            </p>
          </div>
        </div>

        <Link
          to={`/report/${sessionId}`}
          className="text-xs text-blue-400 hover:text-blue-300 font-medium"
        >
          View Full Risk Assessment &rarr;
        </Link>
      </div>

      {/* Main Diff Viewer Component */}
      <DiffViewer
        files={report.changed_files}
        bugFindings={report.bug_findings}
        securityFindings={report.security_findings}
      />
    </div>
  );
};
