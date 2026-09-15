import React from 'react';
import { 
  Bot, 
  Terminal, 
  BarChart3, 
  FileCode2, 
  Award, 
  Cpu, 
  Sparkles, 
  ShieldCheck, 
  Activity 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, healthData }) {
  const navItems = [
    { id: 'playground', label: 'Live Support & Battle', icon: Terminal },
    { id: 'dashboard', label: 'Evaluation Analytics', icon: BarChart3 },
    { id: 'prompts', label: 'Prompt Inspector', icon: FileCode2 },
    { id: 'benchmarks', label: '20-Query Benchmark', icon: ShieldCheck },
    { id: 'jury', label: 'Jury Presentation Mode', icon: Award, highlight: true }
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-[#0B0F19]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo & Badges */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  PromptDesk <span className="text-cyan-400 font-extrabold">AI</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-widest rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  ShopEase Support
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Prompt Engineering & Evaluation Benchmark
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? item.highlight
                        ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-orange-500/25'
                        : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                      : item.highlight
                      ? 'text-amber-400 hover:bg-amber-500/10 border border-amber-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? (item.highlight ? 'text-white' : 'text-cyan-400') : ''}`} />
                  <span className="hidden md:inline">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Status / Model Pill */}
          <div className="hidden lg:flex items-center space-x-3 pl-4 border-l border-slate-800">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-slate-400 font-mono">
                {healthData?.model || 'gemini-3.6-flash'}
              </span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
}
