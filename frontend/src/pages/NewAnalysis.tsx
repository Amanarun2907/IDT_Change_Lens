import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  GitBranch, 
  GitPullRequest, 
  Code, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  Lock, 
  Sliders, 
  Sparkles,
  FileText,
  ShieldAlert,
  Bug,
  HelpCircle
} from 'lucide-react';
import { api } from '../api';

export const NewAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get('mode') || 'manual';

  const [activeTab, setActiveTab] = useState<'repo' | 'pr' | 'manual'>(
    initialMode === 'pr' ? 'pr' : initialMode === 'repo' ? 'repo' : 'manual'
  );

  // Form States - Mode A (Repo)
  const [repoUrl, setRepoUrl] = useState('');
  const [baseBranch, setBaseBranch] = useState('main');
  const [targetBranch, setTargetBranch] = useState('');
  const [branches, setBranches] = useState<string[]>(['main', 'master']);
  const [repoValidated, setRepoValidated] = useState(false);

  // Form States - Mode B (PR)
  const [prUrl, setPrUrl] = useState('');

  // Form States - Mode C (Manual)
  const [manualInputMode, setManualInputMode] = useState<'snippets' | 'diff'>('snippets');
  const [language, setLanguage] = useState('python');
  const [filename, setFilename] = useState('payment_service.py');

  const [originalCode, setOriginalCode] = useState(
`def calculate_payment(amount: float, discount: float = 0.0) -> float:
    """Calculates final payment with discount applied."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return amount * (1.0 - discount)`
  );

  const [updatedCode, setUpdatedCode] = useState(
`def calculate_payment(amount: float, discount: float = 0.0, currency: str = "USD") -> float:
    """Calculates final payment with discount applied."""
    # Bug: removed amount validation, allows negative transactions
    # Security risk: API key embedded for test payment gateway
    GATEWAY_KEY = "sk-test-live-9923841103"
    return amount * (1.0 - discount)`
  );

  const [rawDiff, setRawDiff] = useState(
`--- a/payment_service.py
+++ b/payment_service.py
@@ -1,5 +1,6 @@
-def calculate_payment(amount: float, discount: float = 0.0) -> float:
+def calculate_payment(amount: float, discount: float = 0.0, currency: str = "USD") -> float:
     """Calculates final payment with discount applied."""
-    if amount <= 0:
-        raise ValueError("Amount must be positive")
+    GATEWAY_KEY = "sk-test-live-9923841103"
     return amount * (1.0 - discount)`
  );

  // Common Options
  const [githubToken, setGithubToken] = useState('');
  const [analysisDepth, setAnalysisDepth] = useState('comprehensive');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preset Template Loader
  const loadScenario = (type: 'harmless' | 'bug' | 'security' | 'edge') => {
    setManualInputMode('snippets');
    if (type === 'harmless') {
      setFilename('utils.py');
      setLanguage('python');
      setOriginalCode(
`# Version 1.0 Utility functions
def format_greeting(name: str) -> str:
    return f"Hello, {name}!"`
      );
      setUpdatedCode(
`# Version 1.1 Documentation & type formatting
def format_greeting(name: str) -> str:
    """Formats a user friendly greeting string."""
    return f"Hello, {name.strip()}!"`
      );
    } else if (type === 'bug') {
      setFilename('cart_service.py');
      setLanguage('python');
      setOriginalCode(
`def apply_discount(items: list, discount_percent: float) -> float:
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid discount range")
    total = sum(i['price'] for i in items)
    return total * (1.0 - discount_percent / 100.0)`
      );
      setUpdatedCode(
`def apply_discount(items: list, discount_percent: float) -> float:
    # Logic Bug: removed bounds check, allows discount > 100% (negative invoice)
    # Off-by-one: skips last item in cart
    total = sum(items[i]['price'] for i in range(len(items) - 1))
    return total * (1.0 - discount_percent / 100.0)`
      );
    } else if (type === 'security') {
      setFilename('auth_controller.py');
      setLanguage('python');
      setOriginalCode(
`def get_user_by_id(db_conn, user_id: int):
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()`
      );
      setUpdatedCode(
`def get_user_by_id(db_conn, user_id: str):
    # Critical Security Vulnerability: Hardcoded API secret + SQL Injection
    ADMIN_TOKEN = "sk-prod-9948210384918204"
    cursor = db_conn.cursor()
    # Unsafe raw string formatting allows SQL injection
    cursor.execute(f"SELECT id, username, email FROM users WHERE id = '{user_id}'")
    return cursor.fetchone()`
      );
    } else if (type === 'edge') {
      setFilename('metrics_calculator.py');
      setLanguage('python');
      setOriginalCode(
`def calculate_average_throughput(total_bytes: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    return total_bytes / elapsed_seconds`
      );
      setUpdatedCode(
`def calculate_average_throughput(total_bytes: int, elapsed_seconds: float) -> float:
    # Edge case flaw: removed zero-check causing ZeroDivisionError
    # Missing null guard: crashes if total_bytes is None
    return total_bytes / elapsed_seconds`
      );
    }
  };

  const handleValidateRepo = async () => {
    if (!repoUrl.trim()) return;
    try {
      setError(null);
      const res = await api.validateGitHubUrl(repoUrl, githubToken);
      setRepoValidated(true);
      if (res.default_branch) setBaseBranch(res.default_branch);
      try {
        const bRes = await api.getBranches(repoUrl, githubToken);
        if (bRes.branches && bRes.branches.length > 0) {
          setBranches(bRes.branches);
        }
      } catch (bErr) {
        // ignore branch fetch failure
      }
    } catch (err: any) {
      setRepoValidated(false);
      setError(err.message || 'Invalid GitHub repository URL');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let sessionId = '';
      if (activeTab === 'repo') {
        if (!repoUrl.trim()) throw new Error('Please enter a GitHub repository URL');
        const res = await api.analyzeRepo({
          repo_url: repoUrl.trim(),
          base_branch: baseBranch,
          target_branch: targetBranch.trim() || undefined,
          analysis_depth: analysisDepth,
          github_token: githubToken.trim() || undefined,
        });
        sessionId = res.session_id;
      } else if (activeTab === 'pr') {
        if (!prUrl.trim()) throw new Error('Please enter a Pull Request URL');
        const res = await api.analyzePR({
          pr_url: prUrl.trim(),
          analysis_depth: analysisDepth,
          github_token: githubToken.trim() || undefined,
        });
        sessionId = res.session_id;
      } else {
        if (manualInputMode === 'diff') {
          if (!rawDiff.trim()) throw new Error('Please provide a unified Git diff string');
          const res = await api.analyzeManual({
            raw_diff: rawDiff.trim(),
            language,
            filename: filename.trim() || 'snippet.py',
          });
          sessionId = res.session_id;
        } else {
          if (!originalCode.trim() || !updatedCode.trim()) {
            throw new Error('Please provide both original and updated code snippets');
          }
          const res = await api.analyzeManual({
            original_code: originalCode,
            updated_code: updatedCode,
            language,
            filename: filename.trim() || 'snippet.py',
          });
          sessionId = res.session_id;
        }
      }

      navigate(`/live/${sessionId}`);
    } catch (err: any) {
      setError(err.message || 'Analysis initiation failed');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <span>Start Code Change Analysis</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
            Agentic AI 2.0
          </span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit code modifications or Git diffs to trigger our multi-agent review pipeline: Code Comprehension, Bug & Logic, Security, and Impact Testing.
        </p>
      </div>

      {/* Mode Selector Tabs */}
      <div className="grid grid-cols-3 gap-2 p-1.5 rounded-xl bg-slate-900 border border-slate-800">
        <button
          type="button"
          onClick={() => { setActiveTab('manual'); setError(null); }}
          className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
            activeTab === 'manual'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Code className="w-4 h-4" />
          <span>Manual Code / Diff</span>
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('pr'); setError(null); }}
          className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
            activeTab === 'pr'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <GitPullRequest className="w-4 h-4" />
          <span>GitHub Pull Request</span>
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('repo'); setError(null); }}
          className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
            activeTab === 'repo'
              ? 'bg-cyan-600 text-white shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>GitHub Repo</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/30 flex items-start gap-3 text-red-300 text-sm">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Validation Error</div>
            <p className="text-xs text-red-200/90 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        {/* TAB 1: MANUAL CODE OR RAW DIFF */}
        {activeTab === 'manual' && (
          <div className="space-y-4">
            {/* Quick Demo Scenarios Bar */}
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Quick Load Demo Scenarios:
                </span>
                <span className="text-[11px] text-slate-500">Click to test real AI detection</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => loadScenario('harmless')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-emerald-300 border border-emerald-500/20 flex items-center gap-1"
                >
                  <FileText className="w-3 h-3 text-emerald-400" />
                  Harmless Change
                </button>
                <button
                  type="button"
                  onClick={() => loadScenario('bug')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-amber-300 border border-amber-500/20 flex items-center gap-1"
                >
                  <Bug className="w-3 h-3 text-amber-400" />
                  Logic Bug
                </button>
                <button
                  type="button"
                  onClick={() => loadScenario('security')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-red-300 border border-red-500/20 flex items-center gap-1"
                >
                  <ShieldAlert className="w-3 h-3 text-red-400" />
                  Security Vulnerability
                </button>
                <button
                  type="button"
                  onClick={() => loadScenario('edge')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-cyan-300 border border-cyan-500/20 flex items-center gap-1"
                >
                  <HelpCircle className="w-3 h-3 text-cyan-400" />
                  Edge Case / Zero-Div
                </button>
              </div>
            </div>

            {/* Sub-mode selector: Before & After vs Raw Diff */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setManualInputMode('snippets')}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    manualInputMode === 'snippets'
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Side-by-Side (Before & After)
                </button>
                <button
                  type="button"
                  onClick={() => setManualInputMode('diff')}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    manualInputMode === 'diff'
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Unified Git Diff
                </button>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Language:</span>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100"
                  >
                    <option value="python">Python</option>
                    <option value="typescript">TypeScript</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="go">Go</option>
                    <option value="rust">Rust</option>
                  </select>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">File:</span>
                  <input
                    type="text"
                    value={filename}
                    onChange={(e) => setFilename(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100 font-mono w-36"
                  />
                </div>
              </div>
            </div>

            {manualInputMode === 'snippets' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
                    <span>Original Code (Before)</span>
                    <span className="text-[10px] text-slate-500 font-mono">Reference</span>
                  </label>
                  <textarea
                    rows={11}
                    value={originalCode}
                    onChange={(e) => setOriginalCode(e.target.value)}
                    className="w-full bg-[#0a0f1d] border border-slate-800 rounded-xl p-3 text-xs text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
                    <span>Updated Code (After)</span>
                    <span className="text-[10px] text-emerald-400 font-mono">Modified</span>
                  </label>
                  <textarea
                    rows={11}
                    value={updatedCode}
                    onChange={(e) => setUpdatedCode(e.target.value)}
                    className="w-full bg-[#0a0f1d] border border-slate-800 rounded-xl p-3 text-xs text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Unified Git Diff
                </label>
                <textarea
                  rows={13}
                  value={rawDiff}
                  onChange={(e) => setRawDiff(e.target.value)}
                  placeholder="Paste git diff output or unified diff..."
                  className="w-full bg-[#0a0f1d] border border-slate-800 rounded-xl p-3 text-xs text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
                />
              </div>
            )}
          </div>
        )}

        {/* TAB 2: GITHUB PULL REQUEST */}
        {activeTab === 'pr' && (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                GitHub Pull Request URL
              </label>
              <input
                type="url"
                placeholder="https://github.com/owner/repository/pull/15"
                value={prUrl}
                onChange={(e) => setPrUrl(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
              />
              <p className="text-xs text-slate-400 mt-1">
                ChangeLens retrieves modified files, diff hunks, and commits via GitHub API to generate pre-merge advisory decisions with suggested inline review comments.
              </p>
            </div>
          </div>
        )}

        {/* TAB 3: GITHUB REPOSITORY */}
        {activeTab === 'repo' && (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                GitHub Repository URL
              </label>
              <div className="flex gap-2">
                <input
                  type="url"
                  placeholder="https://github.com/owner/repository"
                  value={repoUrl}
                  onChange={(e) => { setRepoUrl(e.target.value); setRepoValidated(false); }}
                  onBlur={handleValidateRepo}
                  required
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
                />
                <button
                  type="button"
                  onClick={handleValidateRepo}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-semibold"
                >
                  Validate
                </button>
              </div>
              {repoValidated && (
                <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Repository validated successfully
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Base Branch (Reference)
                </label>
                <select
                  value={baseBranch}
                  onChange={(e) => setBaseBranch(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
                >
                  {branches.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Target Branch / Comparison Commit (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. feat/new-auth or HEAD~1"
                  value={targetBranch}
                  onChange={(e) => setTargetBranch(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Advanced Options Drawer */}
        <div className="pt-4 border-t border-slate-800/80">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" />
                GitHub Token (Optional)
              </label>
              <input
                type="password"
                placeholder="ghp_... for private repos or rate limit elevation"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5" />
                Analysis Depth
              </label>
              <select
                value={analysisDepth}
                onChange={(e) => setAnalysisDepth(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="standard">Standard (Modified lines & immediate callers)</option>
                <option value="comprehensive">Comprehensive (Full multi-agent AST call-graph & security scan)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Submit Action */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-[11px] text-slate-500">
            Advisory system: all AI findings & suggested fixes require human developer review.
          </span>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Initializing Agents...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Launch Agentic Review</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
