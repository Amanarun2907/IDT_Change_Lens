import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { History as HistoryIcon, Search, Filter, ArrowRight, RefreshCw, Calendar, Clock, GitBranch } from 'lucide-react';
import { api } from '../api';
import { RiskBadge } from '../components/RiskBadge';

export const History: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadHistory = async () => {
    try {
      setLoading(true);
      const res = await api.getHistory(50, 0, undefined, filterCategory || undefined);
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [filterCategory]);

  const filteredItems = items.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (item.repo_url && item.repo_url.toLowerCase().includes(q)) ||
      (item.pr_title && item.pr_title.toLowerCase().includes(q)) ||
      (item.id && item.id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <HistoryIcon className="w-6 h-6 text-blue-400" />
            Analysis History
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Revisit historical repository investigations, multi-agent verdicts, and audit logs.
          </p>
        </div>

        <button
          onClick={loadHistory}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-xs text-slate-300 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by repo, PR, or session ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Risk Categories</option>
            <option value="CRITICAL">Critical Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Session Target</th>
                <th className="py-3 px-4">Mode</th>
                <th className="py-3 px-4">Risk Category</th>
                <th className="py-3 px-4">Blast Radius</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500 italic">
                    {loading ? 'Loading records...' : 'No historical analysis sessions found.'}
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-sans font-medium text-slate-200 max-w-xs truncate">
                      <div className="font-semibold">{item.pr_title || item.pr_url || item.repo_url || `Code Snippet #${item.id.slice(0, 8)}`}</div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">{item.id}</div>
                    </td>
                    <td className="py-3 px-4 uppercase text-[10px] text-slate-400">
                      {item.mode.replace('_', ' ')}
                    </td>
                    <td className="py-3 px-4">
                      {item.overall_score !== null && item.overall_score !== undefined ? (
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-300">{item.overall_score}</span>
                          <RiskBadge level={item.risk_category || 'LOW'} size="sm" />
                        </div>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-300">
                      {item.blast_radius || 'LOCALIZED'}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {item.duration_seconds ? `${item.duration_seconds}s` : '-'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      <Link
                        to={item.status === 'completed' ? `/report/${item.id}` : `/live/${item.id}`}
                        className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium"
                      >
                        <span>View</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
