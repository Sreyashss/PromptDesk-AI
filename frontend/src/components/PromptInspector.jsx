import React, { useState, useEffect } from 'react';
import { 
  FileCode2, 
  Copy, 
  Check, 
  ShieldCheck, 
  AlertTriangle, 
  Sparkles, 
  Layers, 
  GitCompare,
  CheckCircle2,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { fetchPrompts } from '../api/client';

export default function PromptInspector() {
  const [prompts, setPrompts] = useState([]);
  const [selectedKey, setSelectedKey] = useState('v4');
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchPrompts()
      .then(data => {
        setPrompts(data.prompts || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch prompts:', err);
        setIsLoading(false);
      });
  }, []);

  const activePrompt = prompts.find(p => p.key === selectedKey) || prompts[0];

  const handleCopy = () => {
    if (!activePrompt) return;
    navigator.clipboard.writeText(activePrompt.prompt_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const evolutionMilestones = [
    {
      version: 'V1: Baseline',
      technique: 'Zero-Shot Persona',
      intent: 'Simple support persona with no ground truth policies.',
      policyAwareness: 'None',
      hallucinationRate: 'High (60%+)',
      escalationHandling: 'Fails / Ignored',
      safetyStatus: 'Dangerous'
    },
    {
      version: 'V2: Policy Grounded',
      technique: 'Domain Grounding & Policy Context',
      intent: 'Injects complete ShopEase shipping, return, and electronic policies.',
      policyAwareness: 'High',
      hallucinationRate: 'Moderate (25%)',
      escalationHandling: 'Vague text advice',
      safetyStatus: 'Improved'
    },
    {
      version: 'V3: Few-Shot',
      technique: 'In-Context Demonstrations & Tagging',
      intent: 'Demonstrates standard, edge-case rejection, and [ESCALATE: ...] formatting.',
      policyAwareness: 'High',
      hallucinationRate: 'Low (10%)',
      escalationHandling: 'Structured tags',
      safetyStatus: 'Strong'
    },
    {
      version: 'V4: Hardened Guardrails',
      technique: 'Negative Constraints & Internal Self-Check',
      intent: 'Strict NEVER rules, internal self-verification, anti-jailbreak persona invariance.',
      policyAwareness: 'Authoritative',
      hallucinationRate: 'Near Zero (0%)',
      escalationHandling: 'Guaranteed tags & SLA',
      safetyStatus: 'Enterprise Grade'
    }
  ];

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="p-6 rounded-2xl glass-panel border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/60 to-indigo-950/30">
        <div className="flex items-center space-x-3">
          <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <FileCode2 className="w-5 h-5" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              System Prompt Architecture & Version Inspector
            </h2>
            <p className="text-sm text-slate-400">
              Inspect the exact system instructions, constraints, and engineering techniques powering each iteration from V1 to V4.
            </p>
          </div>
        </div>

        {/* Version Selector Tabs */}
        <div className="mt-6 flex flex-wrap gap-2 pt-4 border-t border-slate-800">
          {prompts.map((p) => {
            const isSelected = p.key === selectedKey;
            return (
              <button
                key={p.key}
                onClick={() => setSelectedKey(p.key)}
                className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center space-x-2 ${
                  isSelected
                    ? p.key === 'v4'
                      ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/25'
                      : 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/25'
                    : 'bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800'
                }`}
              >
                <span className="font-mono">{p.key.toUpperCase()}</span>
                <span>•</span>
                <span>{p.info.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {activePrompt && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Metadata, Techniques, Vulnerabilities */}
          <div className="space-y-5 lg:col-span-1">
            
            {/* Version Overview Card */}
            <div className="p-5 rounded-2xl glass-panel border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Version Metadata
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  {activePrompt.key.toUpperCase()}
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-white">
                  {activePrompt.info.name}
                </h3>
                <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                  {activePrompt.info.description}
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                  <Sparkles className="w-3.5 h-3.5 mr-1 text-cyan-400" />
                  Engineering Techniques:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {activePrompt.info.techniques?.map((tech, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 rounded-md bg-slate-900 border border-slate-800 text-[11px] font-medium text-slate-300"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                  <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-400" />
                  Known Vulnerabilities:
                </span>
                <ul className="space-y-1.5">
                  {activePrompt.info.known_vulnerabilities?.map((vuln, idx) => (
                    <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
                      <span className="text-rose-400 mt-0.5">•</span>
                      <span>{vuln}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Prompt Word & Token stats */}
            <div className="p-4 rounded-2xl glass-panel border border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Estimated Prompt Length:</span>
              <span className="font-mono text-slate-200 font-bold">
                {activePrompt.prompt_text.split(/\s+/).length} words / ~{Math.round(activePrompt.prompt_text.length / 4)} tokens
              </span>
            </div>

          </div>

          {/* Right Column: Full System Prompt Text Viewer */}
          <div className="lg:col-span-2 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                <FileCode2 className="w-4 h-4 mr-1.5 text-cyan-400" />
                Raw System Prompt Instruction
              </span>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 flex items-center space-x-1.5 transition-colors border border-slate-700"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400 font-medium">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Prompt</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 font-mono text-xs sm:text-sm text-slate-200 overflow-x-auto max-h-[600px] overflow-y-auto leading-relaxed whitespace-pre-wrap selection:bg-cyan-500 selection:text-white shadow-2xl">
              {activePrompt.prompt_text}
            </div>
          </div>

        </div>
      )}

      {/* Comparative Prompt Evolution Table */}
      <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-4">
        <div className="flex items-center space-x-2">
          <GitCompare className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-bold text-white">
            Iterative Prompt Engineering Comparison Matrix
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[11px] font-bold tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">Core Technique</th>
                <th className="px-4 py-3">Policy Grounding</th>
                <th className="px-4 py-3">Hallucination Rate</th>
                <th className="px-4 py-3">Escalation Tagging</th>
                <th className="px-4 py-3">Compliance Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {evolutionMilestones.map((m, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-bold text-white whitespace-nowrap">
                    {m.version}
                  </td>
                  <td className="px-4 py-3 text-slate-300 font-medium">
                    {m.technique}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      m.policyAwareness === 'Authoritative' ? 'bg-emerald-500/15 text-emerald-400' :
                      m.policyAwareness === 'High' ? 'bg-sky-500/15 text-sky-400' : 'bg-rose-500/15 text-rose-400'
                    }`}>
                      {m.policyAwareness}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-bold text-slate-200">
                    {m.hallucinationRate}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {m.escalationHandling}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      m.safetyStatus === 'Enterprise Grade' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                      m.safetyStatus === 'Strong' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40' :
                      m.safetyStatus === 'Improved' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                      'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    }`}>
                      {m.safetyStatus}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
