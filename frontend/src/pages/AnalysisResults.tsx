import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  Bug, 
  Share2, 
  TestTube, 
  FileText, 
  Code, 
  Download, 
  Layers, 
  AlertTriangle, 
  CheckCircle, 
  Check, 
  ChevronRight, 
  ChevronDown,
  GitBranch, 
  Zap, 
  Cpu, 
  ArrowUpRight,
  Info,
  ShieldCheck,
  AlertOctagon,
  Activity
} from 'lucide-react';
import { api } from '../api';
import { AnalysisReport, UnifiedFinding } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { DiffViewer } from '../components/DiffViewer';
import { ImpactGraph } from '../components/ImpactGraph';
import { ObservabilityView } from '../components/ObservabilityView';

export const AnalysisResults: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedFindings, setExpandedFindings] = useState<Record<string, boolean>>({});

  const [activeTab, setActiveTab] = useState<
    'findings' | 'summary' | 'changes' | 'risk' | 'bugs' | 'security' | 'impact' | 'blast' | 'regression' | 'tests' | 'fixes' | 'observability'
  >('findings');

  useEffect(() => {
    if (!sessionId) return;
    api.getReport(sessionId)
      .then((data) => {
        setReport(data);
        // Auto-expand high/critical findings by default
        const initialExpanded: Record<string, boolean> = {};
        if (data.unified_findings) {
          data.unified_findings.forEach((f: UnifiedFinding) => {
            if (f.severity === 'CRITICAL' || f.severity === 'HIGH') {
              initialExpanded[f.id] = true;
            }
          });
        }
        setExpandedFindings(initialExpanded);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const toggleFinding = (id: string) => {
    setExpandedFindings((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading analysis report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-2xl mx-auto my-12 p-6 glass-panel rounded-2xl border border-red-500/30 text-center space-y-4">
        <ShieldAlert className="w-10 h-10 text-red-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Report Unavailable</h2>
        <p className="text-xs text-slate-300">{error || 'Unable to retrieve analysis session.'}</p>
        <Link to="/history" className="inline-block text-xs text-blue-400 hover:underline">
          Return to History &rarr;
        </Link>
      </div>
    );
  }

  const { risk_assessment } = report;
  const isHighOrCritical = risk_assessment.risk_category === 'CRITICAL' || risk_assessment.risk_category === 'HIGH';
  const totalFindings = report.unified_findings?.length ?? (report.bug_findings.length + report.security_findings.length);

  const tabs = [
    { id: 'findings', label: 'Prioritized Findings', icon: AlertOctagon, count: totalFindings },
    { id: 'summary', label: 'Executive Summary', icon: FileText, count: null },
    { id: 'changes', label: 'Diff Viewer', icon: Code, count: report.total_files_changed },
    { id: 'risk', label: 'Risk Breakdown', icon: AlertTriangle, count: `${risk_assessment.overall_score}/100` },
    { id: 'bugs', label: 'Bug & Logic', icon: Bug, count: report.bug_findings.length },
    { id: 'security', label: 'Security Review', icon: ShieldAlert, count: report.security_findings.length },
    { id: 'impact', label: 'Dependency Graph', icon: Share2, count: report.impact_items.length },
    { id: 'blast', label: 'Blast Radius', icon: Zap, count: risk_assessment.blast_radius },
    { id: 'regression', label: 'Regressions', icon: Layers, count: report.regression_risks.length },
    { id: 'tests', label: 'Recommended Tests', icon: TestTube, count: report.test_recommendations.length },
    { id: 'fixes', label: 'Suggested Patches', icon: Check, count: report.suggested_fixes.length },
    { 
      id: 'observability', 
      label: 'Trace & Observability', 
      icon: Activity, 
      count: report.observability ? `${report.observability.parallel_speedup_factor.toFixed(1)}x` : null 
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Human in the loop Developer Assistance Banner */}
      <div className="px-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            <b>Developer Advisory System:</b> ChangeLens analyzes risk and detects potential issues. All findings and suggested patches must be reviewed and approved by a developer.
          </span>
        </div>
        <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
          No Auto-Merge
        </span>
      </div>

      {/* Top Advisory Banner */}
      <div className={`p-5 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg ${
        risk_assessment.advisory_recommendation === 'APPROVE'
          ? 'bg-emerald-950/20 border-emerald-500/30 shadow-emerald-950/20'
          : risk_assessment.advisory_recommendation === 'REQUEST_CHANGES'
          ? 'bg-red-950/25 border-red-500/40 shadow-red-950/20'
          : 'bg-amber-950/20 border-amber-500/30 shadow-amber-950/20'
      }`}>
        <div className="flex items-center gap-4">
          <div className="text-3xl font-extrabold tracking-tight">
            <span className={isHighOrCritical ? 'text-red-400' : 'text-emerald-400'}>
              {risk_assessment.overall_score}
            </span>
            <span className="text-xs text-slate-500 font-normal"> / 100</span>
          </div>

          <div className="h-10 w-[1px] bg-slate-800 hidden sm:block" />

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Advisory Decision:</span>
              <RiskBadge level={risk_assessment.advisory_recommendation} size="md" />
              <RiskBadge level={risk_assessment.risk_category} size="md" />
              <span className="text-xs font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-800/80">
                Blast: {risk_assessment.blast_radius}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl line-clamp-2">
              {report.risk_justification || risk_assessment.score_explanation}
            </p>
          </div>
        </div>

        {/* Action Buttons: PDF & JSON Exports */}
        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          <a
            href={api.getExportPdfUrl(report.session_id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </a>
          <a
            href={api.getExportJsonUrl(report.session_id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>JSON</span>
          </a>
        </div>
      </div>

      {/* Target Metadata Bar */}
      <div className="glass-panel px-4 py-2.5 rounded-xl border border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-semibold text-slate-200">Target:</span>
          <span className="font-mono text-blue-400">
            {report.pr_title || report.pr_url || report.repo_url || 'Manual Code Comparison'}
          </span>
          {report.base_ref && (
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              {report.base_ref} &rarr; {report.head_ref || 'HEAD'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 font-mono text-[11px]">
          <span>Duration: {report.duration_seconds}s</span>
          <span>Languages: {report.languages_detected?.join(', ') || 'Auto'}</span>
          <span>Files: {report.total_files_changed} (+{report.total_additions} / -{report.total_deletions})</span>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-slate-800 text-xs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                  isActive ? 'bg-blue-500/20 text-blue-300' : 'bg-slate-800 text-slate-400'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT PANELS */}
      <div className="mt-4">
        {/* 1. CONSOLIDATED & PRIORITIZED FINDINGS */}
        {activeTab === 'findings' && (
          <div className="space-y-4">
            {(!report.unified_findings || report.unified_findings.length === 0) ? (
              <div className="glass-panel p-8 text-center rounded-xl text-slate-400">
                <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                <div className="font-semibold text-white">No Issues Detected</div>
                <p className="text-xs text-slate-400 mt-1">
                  The specialist agents verified the code modification without detecting logical bugs, security flaws, or breaking regressions.
                </p>
              </div>
            ) : (
              report.unified_findings.map((finding) => {
                const isCritOrHigh = finding.severity === 'CRITICAL' || finding.severity === 'HIGH';
                const isExpanded = !!expandedFindings[finding.id];
                return (
                  <div
                    key={finding.id}
                    className={`glass-panel p-5 rounded-xl border transition-all ${
                      finding.severity === 'CRITICAL'
                        ? 'border-red-500/50 bg-red-950/10'
                        : finding.severity === 'HIGH'
                        ? 'border-amber-500/40 bg-amber-950/10'
                        : 'border-slate-800 bg-slate-900/30'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between gap-4 cursor-pointer" onClick={() => toggleFinding(finding.id)}>
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5">
                          {finding.severity === 'CRITICAL' ? (
                            <ShieldAlert className="w-5 h-5 text-red-400" />
                          ) : finding.severity === 'HIGH' ? (
                            <AlertTriangle className="w-5 h-5 text-amber-400" />
                          ) : (
                            <Bug className="w-5 h-5 text-blue-400" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs font-bold text-slate-400">{finding.id}</span>
                            <h3 className="text-sm font-bold text-white">{finding.finding_title}</h3>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono uppercase">
                              {finding.category}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 mt-1 leading-relaxed">{finding.explanation}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-slate-400 font-mono hidden sm:inline">
                          Confidence: {Math.round(finding.confidence * 100)}%
                        </span>
                        <RiskBadge level={finding.severity} size="sm" />
                        <button
                          type="button"
                          className="p-1 rounded hover:bg-slate-800 text-slate-400"
                          onClick={(e) => { e.stopPropagation(); toggleFinding(finding.id); }}
                        >
                          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Expandable Details */}
                    {isExpanded && (
                      <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-3">
                        {/* Evidence */}
                        <div>
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
                            <span>Code Evidence</span>
                            <span className="font-mono text-slate-500">
                              {finding.file_reference ? `${finding.file_reference}${finding.line_start ? `: Line ${finding.line_start}` : ''}` : 'Snippet'}
                            </span>
                          </div>
                          <pre className="bg-[#080d1a] p-3 rounded-lg border border-slate-800/90 font-mono text-xs text-amber-200 overflow-x-auto whitespace-pre leading-relaxed">
                            {finding.exact_evidence}
                          </pre>
                        </div>

                        {/* Impact & Fix Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                            <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block mb-1">
                              Potential Impact
                            </span>
                            <p className="text-slate-200">{finding.potential_impact}</p>
                          </div>

                          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                            <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[10px] block mb-1">
                              Recommended Fix
                            </span>
                            <p className="text-emerald-200">{finding.recommended_fix}</p>
                          </div>
                        </div>

                        {/* Related Test Cases */}
                        {finding.related_test_cases && finding.related_test_cases.length > 0 && (
                          <div className="text-xs">
                            <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block mb-1">
                              Related Verification Tests
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {finding.related_test_cases.map((t, idx) => (
                                <span key={idx} className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 font-mono text-[11px] border border-blue-500/20">
                                  {t}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* 2. EXECUTIVE SUMMARY */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                Executive Summary
              </h2>
              <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
                {report.executive_summary}
              </div>

              {report.change_summary && (
                <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-300 space-y-1">
                  <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
                    Change Summary
                  </span>
                  <p>{report.change_summary}</p>
                </div>
              )}

              {/* Pre-merge checklist */}
              <div className="mt-6">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Pre-Merge Human Review Checklist
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {risk_assessment.human_review_checklist.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-xs text-slate-300">
                      <div className="w-4 h-4 rounded border border-slate-600 flex items-center justify-center shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Inferred Purpose & Architectural Impact */}
            {report.code_understanding && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Functional Impact</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">{report.code_understanding.functional_impact}</p>
                </div>
                <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Architectural Impact</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">{report.code_understanding.architectural_impact}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 3. DIFF VIEWER */}
        {activeTab === 'changes' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="glass-panel p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400">Total Files Changed</span>
                <div className="text-xl font-bold text-white mt-1">{report.total_files_changed}</div>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400">Lines Added</span>
                <div className="text-xl font-bold text-emerald-400 mt-1">+{report.total_additions}</div>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400">Lines Removed</span>
                <div className="text-xl font-bold text-red-400 mt-1">-{report.total_deletions}</div>
              </div>
            </div>

            <DiffViewer
              files={report.changed_files}
              bugFindings={report.bug_findings}
              securityFindings={report.security_findings}
            />
          </div>
        )}

        {/* 4. RISK BREAKDOWN */}
        {activeTab === 'risk' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white">Transparent Risk Score Breakdown</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Calculated from verified AST call-graph relationships, reachable callers, OWASP CWE severity, and test coverage.
                  </p>
                </div>
                <RiskBadge level={risk_assessment.risk_category} size="lg" />
              </div>

              <div className="space-y-3 mt-4">
                {risk_assessment.contributors.map((contrib, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-slate-200">{contrib.factor}</div>
                      <p className="text-xs text-slate-400 mt-0.5">{contrib.description}</p>
                    </div>
                    <span className="text-xs font-mono font-bold text-red-400 px-2 py-1 rounded bg-red-500/10">
                      +{contrib.impact_weight} pts
                    </span>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-800">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Actionable Recommendations to Reduce Risk
                </h3>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {risk_assessment.recommendations_to_reduce_risk.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold">&bull;</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* 5. BUG & LOGIC */}
        {activeTab === 'bugs' && (
          <div className="space-y-4">
            {report.bug_findings.length === 0 ? (
              <div className="glass-panel p-8 text-center rounded-xl text-slate-400">
                <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                No logical bugs or unhandled boundary conditions identified.
              </div>
            ) : (
              report.bug_findings.map((bug, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <Bug className="w-5 h-5 text-amber-400 shrink-0" />
                      <h3 className="text-sm font-bold text-white">{bug.title}</h3>
                    </div>
                    <RiskBadge level={bug.severity} size="sm" />
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{bug.explanation}</p>
                  <div className="bg-[#0a0f1d] p-3 rounded-lg border border-slate-800/80 font-mono text-xs text-amber-200">
                    <div className="text-[10px] text-slate-500 mb-1">
                      {bug.file_path} (Lines {bug.line_start}-{bug.line_end})
                    </div>
                    {bug.evidence}
                  </div>
                  <div className="text-xs text-slate-300">
                    <b className="text-emerald-400">Recommended Correction:</b> {bug.recommended_correction}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* 6. SECURITY */}
        {activeTab === 'security' && (
          <div className="space-y-4">
            {report.security_findings.length === 0 ? (
              <div className="glass-panel p-8 text-center rounded-xl text-slate-400">
                <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                No contextual security vulnerabilities detected.
              </div>
            ) : (
              report.security_findings.map((sec, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-xl border border-red-500/30 space-y-3 bg-red-950/5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
                      <div>
                        <h3 className="text-sm font-bold text-white">{sec.vulnerability_title}</h3>
                        {sec.cwe && <span className="text-[10px] font-mono text-red-300">{sec.cwe}</span>}
                      </div>
                    </div>
                    <RiskBadge level={sec.severity} size="sm" />
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{sec.explanation}</p>
                  <div className="bg-[#0a0f1d] p-3 rounded-lg border border-slate-800 font-mono text-xs text-red-200">
                    <div className="text-[10px] text-slate-500 mb-1">
                      {sec.file_path}: Line {sec.exact_line}
                    </div>
                    {sec.code_evidence}
                  </div>
                  <div className="text-xs space-y-1">
                    <div><b className="text-slate-400">Attack Scenario:</b> <span className="text-slate-300">{sec.attack_scenario}</span></div>
                    <div><b className="text-emerald-400">Remediation:</b> <span className="text-emerald-200">{sec.remediation}</span></div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* 7. DEPENDENCY GRAPH */}
        {activeTab === 'impact' && (
          <div className="space-y-4">
            <ImpactGraph graph={report.impact_graph} />
          </div>
        )}

        {/* 8. BLAST RADIUS */}
        {activeTab === 'blast' && (
          <div className="space-y-4">
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-400" />
                    Blast Radius Classification
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Measures reachability of changes across modules and callers.
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  {risk_assessment.blast_radius}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-sm text-slate-200">
                {risk_assessment.blast_radius_explanation}
              </div>
            </div>
          </div>
        )}

        {/* 9. REGRESSIONS */}
        {activeTab === 'regression' && (
          <div className="space-y-4">
            {report.regression_risks.length === 0 ? (
              <div className="glass-panel p-8 text-center rounded-xl text-slate-400">
                <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                No breaking interface changes or backward compatibility regressions detected.
              </div>
            ) : (
              report.regression_risks.map((reg, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-white font-mono">{reg.component}</div>
                    <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 uppercase font-mono">
                      {reg.change_type}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{reg.description}</p>
                  <div className="text-xs text-emerald-300"><b>Mitigation:</b> {reg.mitigation}</div>
                </div>
              ))
            )}
          </div>
        )}

        {/* 10. RECOMMENDED TESTS */}
        {activeTab === 'tests' && (
          <div className="space-y-4">
            <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between text-xs font-mono">
              <span>Tests Recommended: <b>{report.test_recommendations.length}</b></span>
              <span>Tests Found: <b>{report.test_execution.tests_found}</b></span>
              <span className="text-slate-400">{report.test_execution.output_log}</span>
            </div>

            <div className="space-y-3">
              {report.test_recommendations.map((t, idx) => (
                <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-semibold text-white">{t.test_name}</span>
                    <RiskBadge level={t.priority} size="sm" />
                  </div>
                  <p className="text-xs text-slate-300">{t.objective}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono bg-[#090d16] p-2.5 rounded-lg border border-slate-800">
                    <div><span className="text-slate-500">Input:</span> {t.input_data}</div>
                    <div><span className="text-emerald-400">Expected:</span> {t.expected_output}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 11. SUGGESTED PATCHES & COMMENTS */}
        {activeTab === 'fixes' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-bold text-white mb-3">AI-Generated Unified Diff Fix Patches</h3>
              {report.suggested_fixes.length === 0 ? (
                <div className="glass-panel p-6 text-center rounded-xl text-slate-400 text-xs">
                  No automated patches required for clean modifications.
                </div>
              ) : (
                <div className="space-y-4">
                  {report.suggested_fixes.map((patch, idx) => (
                    <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-sm text-white">{patch.issue_title}</h4>
                        <span className="text-xs font-mono text-slate-400">{patch.file_path}</span>
                      </div>
                      <p className="text-xs text-slate-300">{patch.explanation}</p>
                      <pre className="bg-[#090d16] p-3 rounded-xl border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre leading-relaxed">
                        {patch.unified_diff}
                      </pre>
                      <div className="text-xs text-slate-400">
                        <b className="text-blue-400">Why it helps:</b> {patch.why_it_helps}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {report.review_comments.length > 0 && (
              <div className="pt-4 border-t border-slate-800">
                <h3 className="text-sm font-bold text-white mb-3">Suggested Inline Review Comments</h3>
                <div className="space-y-3">
                  {report.review_comments.map((comm, idx) => (
                    <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800 text-xs space-y-1.5">
                      <div className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
                        <span>{comm.file_path}: Line {comm.line_number}</span>
                      </div>
                      <div className="font-semibold text-white">{comm.problem}</div>
                      <p className="text-slate-300">{comm.suggested_improvement}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab: Observability & Agent Performance Waterfall */}
        {activeTab === 'observability' && (
          <ObservabilityView report={report.observability} sessionId={report.session_id} />
        )}
      </div>
    </div>
  );
};
