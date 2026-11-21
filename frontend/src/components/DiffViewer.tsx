import React, { useState } from 'react';
import { FileCode, ShieldAlert, Bug, Check, ChevronRight } from 'lucide-react';
import { ChangedFile, BugFinding, SecurityFinding } from '../types';

interface DiffViewerProps {
  files: ChangedFile[];
  bugFindings?: BugFinding[];
  securityFindings?: SecurityFinding[];
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  files,
  bugFindings = [],
  securityFindings = [],
}) => {
  const [selectedFileIdx, setSelectedFileIdx] = useState(0);

  if (!files || files.length === 0) {
    return (
      <div className="glass-panel p-8 text-center rounded-xl text-slate-400">
        No code changes detected in this analysis.
      </div>
    );
  }

  const currentFile = files[selectedFileIdx] || files[0];
  const hunks = currentFile.diff_hunks || '';

  // Filter inline findings for current file
  const fileBugs = bugFindings.filter(
    (b) => b.file_path.toLowerCase().includes(currentFile.file_path.toLowerCase()) ||
           currentFile.file_path.toLowerCase().includes(b.file_path.toLowerCase())
  );
  const fileSecurity = securityFindings.filter(
    (s) => s.file_path.toLowerCase().includes(currentFile.file_path.toLowerCase()) ||
           currentFile.file_path.toLowerCase().includes(s.file_path.toLowerCase())
  );

  // Parse lines for rendering
  let currentOldLine = 1;
  let currentNewLine = 1;

  const parsedLines = hunks.split('\n').map((line, idx) => {
    let type: 'header' | 'add' | 'del' | 'context' = 'context';
    let oldNum: number | null = null;
    let newNum: number | null = null;

    if (line.startsWith('@@')) {
      type = 'header';
      const match = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (match) {
        currentOldLine = parseInt(match[1], 10);
        currentNewLine = parseInt(match[2], 10);
      }
    } else if (line.startsWith('+') && !line.startsWith('+++')) {
      type = 'add';
      newNum = currentNewLine++;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      type = 'del';
      oldNum = currentOldLine++;
    } else {
      type = 'context';
      oldNum = currentOldLine++;
      newNum = currentNewLine++;
    }

    return {
      id: idx,
      raw: line,
      type,
      oldNum,
      newNum,
      bugs: newNum ? fileBugs.filter((b) => b.line_start <= newNum! && b.line_end >= newNum!) : [],
      security: newNum ? fileSecurity.filter((s) => s.exact_line === newNum) : []
    };
  });

  return (
    <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
      {/* File Selector Bar */}
      <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <FileCode className="w-5 h-5 text-blue-400" />
          <select
            value={selectedFileIdx}
            onChange={(e) => setSelectedFileIdx(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
          >
            {files.map((f, idx) => (
              <option key={f.file_path} value={idx}>
                {f.file_path} (+{f.additions} / -{f.deletions})
              </option>
            ))}
          </select>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase font-mono">
            {currentFile.status}
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="text-emerald-400 font-semibold">+{currentFile.additions} lines</span>
          <span className="text-red-400 font-semibold">-{currentFile.deletions} lines</span>
          {(fileBugs.length > 0 || fileSecurity.length > 0) && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 font-sans">
              <ShieldAlert className="w-3.5 h-3.5" />
              {fileBugs.length + fileSecurity.length} findings in this file
            </span>
          )}
        </div>
      </div>

      {/* Diff Code View */}
      <div className="overflow-x-auto max-h-[620px] font-mono text-xs leading-relaxed bg-[#0b101b]">
        <table className="w-full border-collapse">
          <tbody>
            {parsedLines.map((row) => (
              <React.Fragment key={row.id}>
                <tr
                  className={`border-b border-slate-900/40 transition-colors ${
                    row.type === 'add'
                      ? 'bg-emerald-950/25 text-emerald-200'
                      : row.type === 'del'
                      ? 'bg-red-950/25 text-red-200'
                      : row.type === 'header'
                      ? 'bg-blue-950/30 text-blue-300 font-bold'
                      : 'hover:bg-slate-900/40 text-slate-300'
                  }`}
                >
                  {/* Old line num */}
                  <td className="w-12 py-0.5 px-2 text-right select-none text-slate-600 border-r border-slate-800/60">
                    {row.oldNum || ''}
                  </td>
                  {/* New line num */}
                  <td className="w-12 py-0.5 px-2 text-right select-none text-slate-600 border-r border-slate-800/60">
                    {row.newNum || ''}
                  </td>
                  {/* Code Line */}
                  <td className="py-0.5 px-4 whitespace-pre">
                    {row.raw}
                  </td>
                </tr>

                {/* Inline Bug Findings Callout */}
                {row.bugs.map((b, bIdx) => (
                  <tr key={`bug-${bIdx}`} className="bg-amber-950/40 border-l-4 border-l-amber-500 text-amber-200 text-xs">
                    <td colSpan={2} className="py-2 px-3 text-center">
                      <Bug className="w-4 h-4 text-amber-400 mx-auto" />
                    </td>
                    <td className="py-2 px-4">
                      <div className="font-sans font-semibold text-amber-300">{b.title} ({b.severity})</div>
                      <p className="font-sans text-slate-300 text-[11px] mt-0.5">{b.explanation}</p>
                      <div className="font-sans text-xs text-amber-200/90 mt-1">
                        <b>Suggested Fix:</b> {b.recommended_correction}
                      </div>
                    </td>
                  </tr>
                ))}

                {/* Inline Security Findings Callout */}
                {row.security.map((s, sIdx) => (
                  <tr key={`sec-${sIdx}`} className="bg-red-950/50 border-l-4 border-l-red-500 text-red-200 text-xs">
                    <td colSpan={2} className="py-2 px-3 text-center">
                      <ShieldAlert className="w-4 h-4 text-red-400 mx-auto" />
                    </td>
                    <td className="py-2 px-4">
                      <div className="font-sans font-semibold text-red-300 flex items-center gap-2">
                        <span>{s.vulnerability_title} [{s.severity}]</span>
                        {s.cwe && <span className="text-[10px] bg-red-900/60 px-1.5 py-0.5 rounded">{s.cwe}</span>}
                      </div>
                      <p className="font-sans text-slate-200 text-[11px] mt-0.5">{s.explanation}</p>
                      <div className="font-sans text-xs text-emerald-300 mt-1">
                        <b>Remediation:</b> {s.remediation}
                      </div>
                    </td>
                  </tr>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
