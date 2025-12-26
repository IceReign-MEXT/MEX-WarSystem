import React, { useState, useEffect } from 'react';
import { Shield, Zap, Activity, Terminal, Lock } from 'lucide-react';

const App = () => {
  return (
    <div className="min-h-screen bg-black text-cyan-500 font-mono p-4 md:p-10 selection:bg-cyan-900">
      <div className="max-w-6xl mx-auto border border-cyan-900 bg-gray-900/20 rounded-lg overflow-hidden backdrop-blur-md">
        
        {/* Header with your Logo */}
        <header className="border-b border-cyan-900 p-6 flex justify-between items-center bg-black/50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 text-cyan-400">
              {/* CYBER SKULL LOGO */}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a5 5 0 0 0-5 5v3a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V7a5 5 0 0 0-5-5z" />
                <path d="M6 15v-2a6 6 0 1 1 12 0v2" />
                <rect x="6" y="15" width="12" height="5" rx="1" />
                <path d="M9 18h.01M15 18h.01" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tighter uppercase italic">Ice Gods Empire</h1>
              <p className="text-[10px] opacity-50 tracking-[0.3em]">REVENUE STREAMING ACTIVE</p>
            </div>
          </div>
          <div className="text-right hidden sm:block">
            <span className="text-[10px] block opacity-50">JWT_ID: T6H7...</span>
            <span className="text-green-500 text-xs animate-pulse">● SECURE NODE</span>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 border-b border-cyan-900">
          <StatBox label="Total Supply" value="30,000,000,000" sub="IBS TOKENS" />
          <StatBox label="Maker Tax" value="1.0%" sub="PASSIVE YIELD" />
          <StatBox label="Wallet Status" value="CONNECTED" sub="0x7D7A...eda3" />
        </div>

        {/* Terminal Section */}
        <div className="p-6 bg-black/40 h-64 overflow-y-auto text-xs space-y-2">
          <p className="text-cyan-800">[03:44:01] Initializing War-System...</p>
          <p className="text-cyan-800">[03:44:02] Loading Alchemy Oracle: CONNECTED</p>
          <p className="text-cyan-400 font-bold">[03:44:05] Monitoring Contract: 30B IBS detected</p>
          <p className="text-green-400">[03:44:10] Scanning for MEV opportunities...</p>
          <div className="flex items-center gap-2">
            <span className="animate-ping w-1.5 h-1.5 bg-green-500 rounded-full"></span>
            <span className="text-green-500">Listening for frontline trades...</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatBox = ({ label, value, sub }) => (
  <div className="border border-cyan-900/50 p-4 rounded bg-cyan-950/10">
    <div className="text-[10px] opacity-40 uppercase mb-1">{label}</div>
    <div className="text-xl font-bold">{value}</div>
    <div className="text-[9px] opacity-30 mt-1">{sub}</div>
  </div>
);

export default App;


