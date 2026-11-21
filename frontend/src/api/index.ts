import { AnalysisReport, DashboardStats, ObservabilityReport } from '../types';

// Support VITE_API_URL environment variable (for Render/Netlify cross-origin deployment), default to /api
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + '/api';

export const api = {
  async analyzeRepo(data: {
    repo_url: string;
    base_branch?: string;
    target_branch?: string;
    analysis_depth?: string;
    github_token?: string;
  }): Promise<{ session_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/analysis/repo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to start repository analysis');
    }
    return res.json();
  },

  async analyzePR(data: {
    pr_url: string;
    analysis_depth?: string;
    github_token?: string;
  }): Promise<{ session_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/analysis/pr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to start PR analysis');
    }
    return res.json();
  },

  async analyzeManual(data: {
    original_code?: string;
    updated_code?: string;
    raw_diff?: string;
    language: string;
    filename?: string;
  }): Promise<{ session_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/analysis/manual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to start manual comparison');
    }
    return res.json();
  },

  async getReport(sessionId: string): Promise<AnalysisReport> {
    const res = await fetch(`${API_BASE}/analysis/${sessionId}/report`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to fetch analysis report');
    }
    return res.json();
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/history/stats`);
    if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
    return res.json();
  },

  async getHistory(limit = 20, offset = 0, status?: string, riskCategory?: string): Promise<{ total: number; items: any[] }> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.append('status', status);
    if (riskCategory) params.append('risk_category', riskCategory);

    const res = await fetch(`${API_BASE}/history?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch history');
    return res.json();
  },

  async validateGitHubUrl(url: string, token?: string) {
    const res = await fetch(`${API_BASE}/github/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, token }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Invalid GitHub URL');
    }
    return res.json();
  },

  async getBranches(repoUrl: string, token?: string): Promise<{ branches: string[] }> {
    const params = new URLSearchParams({ repo_url: repoUrl });
    if (token) params.append('token', token);
    const res = await fetch(`${API_BASE}/github/branches?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch branches');
    return res.json();
  },

  async getSettings() {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async testLLM() {
    const res = await fetch(`${API_BASE}/settings/test-llm`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to test LLM connectivity');
    return res.json();
  },

  async updateSettings(data: {
    llm_provider?: string;
    llm_api_key?: string;
    llm_model?: string;
    groq_api_key?: string;
    gemini_api_key?: string;
    openai_api_key?: string;
    github_token?: string;
    default_model?: string;
  }) {
    const res = await fetch(`${API_BASE}/settings/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  getStreamUrl(sessionId: string) {
    return `${API_BASE}/analysis/${sessionId}/stream`;
  },

  getExportPdfUrl(sessionId: string) {
    return `${API_BASE}/reports/${sessionId}/pdf`;
  },

  getExportJsonUrl(sessionId: string) {
    return `${API_BASE}/reports/${sessionId}/json`;
  },

  async getObservabilityOverview(): Promise<{
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
  }> {
    const res = await fetch(`${API_BASE}/observability/overview`);
    if (!res.ok) throw new Error('Failed to fetch observability telemetry');
    return res.json();
  },

  async getTrace(sessionId: string): Promise<ObservabilityReport> {
    const res = await fetch(`${API_BASE}/observability/trace/${sessionId}`);
    if (!res.ok) throw new Error('Failed to fetch trace data');
    return res.json();
  }
};
