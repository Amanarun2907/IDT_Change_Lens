import React, { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Key, Cpu, CheckCircle2, AlertCircle, RefreshCw, Shield, Sparkles } from 'lucide-react';
import { api } from '../api';

export const Settings: React.FC = () => {
  const [provider, setProvider] = useState('gemini');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('gemini-2.5-flash');
  const [githubToken, setGithubToken] = useState('');
  const [settingsData, setSettingsData] = useState<any>(null);

  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const providerModels: Record<string, string[]> = {
    gemini: ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.5-pro'],
    groq: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'deepseek-r1-distill-llama-70b', 'qwen-qwq-32b'],
    openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
    custom: ['custom-model']
  };

  useEffect(() => {
    api.getSettings().then((data) => {
      setSettingsData(data);
      if (data.llm_provider) setProvider(data.llm_provider);
      if (data.default_model) setModel(data.default_model);
    }).catch(console.error);
  }, []);

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    const models = providerModels[newProvider] || [];
    if (models.length > 0) {
      setModel(models[0]);
    }
  };

  const handleTestLLM = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testLLM();
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ status: 'error', detail: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await api.updateSettings({
        llm_provider: provider,
        llm_api_key: apiKey.trim() || undefined,
        llm_model: model,
        default_model: model,
        github_token: githubToken.trim() || undefined,
      });
      setMessage('Platform settings updated successfully.');
      const data = await api.getSettings();
      setSettingsData(data);
      setApiKey('');
      setGithubToken('');
    } catch (err: any) {
      setMessage('Failed to update settings: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-blue-400" />
          ChangeLens Settings & AI Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure model inference providers (Gemini, Groq, OpenAI), API credentials, and GitHub tokens.
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-500/30 text-blue-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Model & Connectivity Test Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 flex-wrap gap-2">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-400" />
              LLM Engine Connectivity Status
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              ChangeLens supports multi-provider agentic inference with automated retry and JSON schema validation.
            </p>
          </div>

          <button
            type="button"
            onClick={handleTestLLM}
            disabled={testing}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
            <span>Test Connection</span>
          </button>
        </div>

        <div className="text-xs space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Configured Provider:</span>
            <span className="font-mono text-cyan-400 uppercase font-semibold">
              {settingsData?.llm_provider || provider}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Active Model:</span>
            <span className="font-mono text-blue-400">{settingsData?.default_model || model}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">API Key Status:</span>
            <span className="font-mono text-slate-200">
              {settingsData?.api_key_masked || (settingsData?.api_key_configured ? 'Active' : 'Not configured')}
            </span>
            {settingsData?.api_key_configured && (
              <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 font-mono">
                CONFIGURED
              </span>
            )}
          </div>
        </div>

        {testResult && (
          <div className={`p-4 rounded-xl text-xs space-y-1.5 ${
            testResult.status === 'ok'
              ? 'bg-emerald-950/30 border border-emerald-500/30 text-emerald-200'
              : 'bg-red-950/30 border border-red-500/30 text-red-200'
          }`}>
            <div className="font-bold flex items-center gap-2">
              {testResult.status === 'ok' ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  API Connectivity Verified ({testResult.provider || provider})
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  API Test Check Failed
                </>
              )}
            </div>
            {testResult.available_models && (
              <p className="text-[11px] font-mono text-slate-300">
                Accessible models: {testResult.available_models.slice(0, 5).join(', ')}...
              </p>
            )}
            {testResult.detail && <p className="text-xs">{testResult.detail}</p>}
          </div>
        )}
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleSave} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Key className="w-5 h-5 text-indigo-400" />
          Update LLM Provider & Credentials
        </h2>

        {/* Provider Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            LLM Provider
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {['gemini', 'groq', 'openai', 'custom'].map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => handleProviderChange(p)}
                className={`py-2 px-3 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all border ${
                  provider === p
                    ? 'bg-blue-600/20 text-blue-400 border-blue-500/50 shadow-sm'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {p === 'gemini' ? 'Google Gemini' : p}
              </button>
            ))}
          </div>
        </div>

        {/* Model Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Reasoning Model
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
          >
            {(providerModels[provider] || ['custom-model']).map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            {provider === 'gemini' ? 'Google Gemini API Key' : provider === 'groq' ? 'Groq API Key' : 'API Key'}
          </label>
          <input
            type="password"
            placeholder={
              provider === 'gemini' ? 'Enter AIza... key' :
              provider === 'groq' ? 'Enter gsk_... key' :
              'Enter API Key or leave blank to keep current'
            }
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            API keys are stored securely in backend environment variables and never exposed to the frontend or git.
          </p>
        </div>

        {/* GitHub PAT */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            GitHub Personal Access Token (Optional)
          </label>
          <input
            type="password"
            placeholder="ghp_... for private repos or rate limit elevation"
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
          />
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all shadow-md"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
};
