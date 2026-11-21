export type AnalysisMode = 'github_repo' | 'github_pr' | 'manual_diff';
export type AnalysisStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed';
export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RiskCategory = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type BlastRadius = 'LOCALIZED' | 'MODULE_LEVEL' | 'CROSS_MODULE' | 'APPLICATION_WIDE';
export type AdvisoryRecommendation = 'APPROVE' | 'REQUEST_CHANGES' | 'NEEDS_HUMAN_REVIEW';

export type FindingCategory =
  | 'BUG_LOGIC'
  | 'SECURITY'
  | 'REGRESSION'
  | 'EDGE_CASE'
  | 'TESTING_GAP'
  | 'PERFORMANCE'
  | 'CODE_QUALITY';

export interface ChangedFile {
  file_path: string;
  status: string;
  additions: number;
  deletions: number;
  old_path?: string;
  diff_hunks?: string;
}

export interface CodeUnderstandingOutput {
  change_summary: string;
  purpose: string;
  modified_components: string[];
  functional_impact: string;
  architectural_impact: string;
  potentially_affected_modules: string[];
  behavioral_changes: string[];
  changed_interfaces: string[];
}

export interface BugFinding {
  title: string;
  file_path: string;
  line_start: number;
  line_end: number;
  evidence: string;
  explanation: string;
  severity: Severity;
  confidence: number;
  potential_impact: string;
  recommended_correction: string;
}

export interface SecurityFinding {
  vulnerability_title: string;
  file_path: string;
  exact_line: number;
  code_evidence: string;
  cwe?: string;
  explanation: string;
  attack_scenario: string;
  potential_impact: string;
  severity: Severity;
  confidence: number;
  remediation: string;
}

export interface UnifiedFinding {
  id: string;
  finding_title: string;
  category: FindingCategory;
  severity: Severity;
  confidence: number;
  file_reference?: string;
  function_reference?: string;
  line_start?: number;
  line_end?: number;
  exact_evidence: string;
  explanation: string;
  potential_impact: string;
  recommended_fix: string;
  related_test_cases: string[];
  source_agent: string;
  is_ai_generated: boolean;
}

export interface ImpactItem {
  modified_symbol: string;
  symbol_type: string;
  file_path: string;
  direct_callers: string[];
  indirect_callers: string[];
  dependent_modules: string[];
  affected_apis: string[];
  impact_type: string;
  verified: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  severity?: string;
  status: string;
  details?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  relationship: string;
  verified: boolean;
}

export interface ImpactGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface TestRecommendation {
  test_name: string;
  objective: string;
  input_data: string;
  expected_output: string;
  reason: string;
  related_file: string;
  related_function?: string;
  priority: Severity;
}

export interface TestExecutionResult {
  tests_recommended: number;
  tests_found: number;
  tests_executed: number;
  tests_passed: number;
  tests_failed: number;
  tests_not_executed: number;
  output_log?: string;
}

export interface RegressionRisk {
  component: string;
  change_type: string;
  callers_count: number;
  breaking: boolean;
  description: string;
  mitigation: string;
}

export interface ReviewComment {
  file_path: string;
  line_number: number;
  problem: string;
  evidence: string;
  suggested_improvement: string;
}

export interface FixPatch {
  issue_title: string;
  file_path: string;
  explanation: string;
  unified_diff: string;
  why_it_helps: string;
}

export interface RiskContributor {
  factor: string;
  impact_weight: number;
  description: string;
}

export interface RiskAssessment {
  overall_score: number;
  risk_category: RiskCategory;
  blast_radius: BlastRadius;
  blast_radius_explanation: string;
  advisory_recommendation: AdvisoryRecommendation;
  contributors: RiskContributor[];
  score_explanation: string;
  recommendations_to_reduce_risk: string[];
  human_review_checklist: string[];
}

export interface AnalysisReport {
  session_id: string;
  mode: AnalysisMode;
  repo_url?: string;
  pr_url?: string;
  pr_number?: number;
  pr_title?: string;
  base_ref?: string;
  head_ref?: string;
  created_at: string;
  duration_seconds: number;

  executive_summary: string;
  change_summary?: string;
  risk_justification?: string;
  affected_components?: string[];
  languages_detected: string[];
  frameworks_detected: string[];
  total_files_changed: number;
  total_additions: number;
  total_deletions: number;
  changed_files: ChangedFile[];

  unified_findings: UnifiedFinding[];
  code_understanding?: CodeUnderstandingOutput;
  bug_findings: BugFinding[];
  security_findings: SecurityFinding[];
  impact_items: ImpactItem[];
  impact_graph: ImpactGraph;
  regression_risks: RegressionRisk[];
  test_recommendations: TestRecommendation[];
  test_execution: TestExecutionResult;
  review_comments: ReviewComment[];
  suggested_fixes: FixPatch[];
  risk_assessment: RiskAssessment;
}

export interface ProgressEvent {
  session_id: string;
  step_id: string;
  step_name: string;
  agent_name?: string;
  status: string;
  message: string;
  percent: number;
  timestamp: string;
  data?: Record<string, any>;
}

export interface DashboardStats {
  total_analyses: number;
  critical_findings: number;
  high_risk_changes: number;
  security_vulnerabilities: number;
  average_risk_score: number;
  recent_analyses: Array<{
    id: string;
    created_at: string;
    mode: string;
    repo_url?: string;
    pr_url?: string;
    pr_title?: string;
    status: string;
    overall_score?: number;
    risk_category?: string;
    blast_radius?: string;
    advisory_recommendation?: string;
    total_files_changed: number;
    duration_seconds: number;
  }>;
  trends: Array<{
    session_id: string;
    date: string;
    score: number;
    category: string;
  }>;
}
