import React, { useState, useEffect } from 'react';
import { Shield, Zap, Activity, Lock, Terminal, BarChart3, Globe, Cpu, ChevronRight, Database, Coins } from 'lucide-react';

const App = () => {
  const [logs, setLogs] = useState([]);
  const [prices, setPrices] = useState({ eth: 2654.20, sol: 142.45 });
  const [vaults, setVaults] = useState({ eth: 1.80099, sol: 335.55 });
  
  const WALLET_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F";
  const WALLET_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy";

  useEffect(() => {
    const interval = setInterval(() => {
      const events = [
        "SOLANA_RPC_SYNC: OPTIMAL",
        "ETH_MEMPOOL_SCAN: 0.02ms",
        "WHALE_DETECTED: 5000 SOL -> RAYDIUM",
        "FRONT_RUN_PROTCOL: ACTIVE",
        "54_NODES_SYNCHRONIZED",
        "ICE_GODS_GATEWAY: SECURE",
        "LIQUIDITY_SNIPE: DETECTED_ON_CHAIN"
      ];
      const newLog = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        text: events[Math.floor(Math.random() * events.length)]
      };
      setLogs(prev => [newLog, ...prev].slice(0, 12));
      setPrices(p => ({ 
        eth: p.eth + (Math.random() - 0.5) * 4, 
        sol: p.sol + (Math.random() - 0.5) * 2 
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const totalUSD = (vaults.eth * prices.eth) + (vaults.sol * prices.sol);

  return (
    <div className="min-h-screen bg-black text-cyan-400 font-mono p-4 md:p-10 selection:bg-cyan-500 selection:text-black">
      {/* HUD HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start mb-10 border-b border-cyan-900/40 pb-6">
        <div>
          <h1 className="text-5xl font-black italic tracking-tighter text-white flex items-center gap-3">
            <Shield className="w-10 h-10 text-cyan-500" /> MONOLITH_V21
          </h1>
          <p className="text-[10px] tracking-[0.6em] text-cyan-900 font-bold mt-2 uppercase">Dual-Chain Autonomous Sovereignty</p>
        </div>
        <div className="flex gap-8 mt-4 md:mt-0">
          <div className="text-right">
            <p className="text-[8px] text-zinc-600">ETH_INDEX</p>
            <p className="text-white font-bold">${prices.eth.toFixed(2)}</p>
          </div>
          <div className="text-right border-l border-zinc-800 pl-8">
            <p className="text-[8px] text-zinc-600">SOL_INDEX</p>
            <p className="text-white font-bold">${prices.sol.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* MAIN STATS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-zinc-950 border border-cyan-900/20 p-8 rounded-[2rem] shadow-2xl">
          <p className="text-[9px] text-zinc-500 uppercase mb-2">Total_Vault_Valuation</p>
          <p className="text-4xl font-black text-green-500">${totalUSD.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
        </div>
        <div className="bg-zinc-950 border border-cyan-900/20 p-8 rounded-[2rem]">
          <p className="text-[9px] text-zinc-500 uppercase mb-2">Dual_Reserves</p>
          <div className="flex justify-between items-end">
            <p className="text-xl font-bold text-white">{vaults.eth} ETH</p>
            <p className="text-xl font-bold text-white">{vaults.sol} SOL</p>
          </div>
        </div>
        <div className="bg-cyan-500 p-8 rounded-[2rem] flex flex-col justify-center">
          <p className="text-[9px] text-black uppercase font-bold mb-1">Active_Nodes</p>
          <p className="text-4xl font-black text-black italic">54_POWER_NODES</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[400px]">
        {/* SURVEILLANCE */}
        <div className="lg:col-span-2 bg-zinc-900/10 border border-cyan-900/20 rounded-[3rem] p-8 flex flex-col">
          <h3 className="text-xs font-bold mb-6 flex items-center gap-2 text-zinc-500 uppercase tracking-widest">
            <Terminal className="w-4 h-4" /> Live_Mempool_Capture
          </h3>
          <div className="flex-grow space-y-2 overflow-hidden opacity-80">
            {logs.map(log => (
              <div key={log.id} className="text-[10px] flex gap-4">
                <span className="text-zinc-800">[{log.time}]</span>
                <span className="text-cyan-600">SYS_INT_00:</span>
                <span className="text-zinc-400">{log.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ACTIVATION GATE */}
        <div className="bg-zinc-950 border-2 border-cyan-500 rounded-[3rem] p-10 flex flex-col justify-between shadow-[0_0_50px_rgba(6,182,212,0.1)]">
          <div>
            <div className="bg-cyan-500/10 text-cyan-500 w-fit px-3 py-1 rounded-full text-[8px] font-black mb-6 uppercase">Paid_Access_Only</div>
            <h2 className="text-3xl font-black text-white italic tracking-tighter leading-none mb-4">ACTIVATE YOUR NODE</h2>
            <p className="text-[10px] text-zinc-500 leading-relaxed mb-6">Enter the Multitude. Gain sniper advantage, whale detection, and autonomous raid capabilities on ETH & SOL.</p>
          </div>
          
          <div className="space-y-3">
            <div className="bg-black p-4 rounded-xl border border-white/5">
              <p className="text-[8px] text-zinc-600 mb-1 uppercase tracking-widest">SOLANA_VAULT</p>
              <p className="text-[9px] text-white break-all font-bold">{WALLET_SOL}</p>
            </div>
            <div className="bg-black p-4 rounded-xl border border-white/5">
              <p className="text-[8px] text-zinc-600 mb-1 uppercase tracking-widest">ETH_VAULT</p>
              <p className="text-[9px] text-white break-all font-bold">{WALLET_ETH}</p>
            </div>
            <button className="w-full bg-cyan-500 text-black font-black py-4 rounded-xl hover:scale-95 transition-transform">
              COPY ACTIVATION ADDRESS
            </button>
          </div>
        </div>
      </div>

      <footer className="mt-12 flex justify-between items-center text-[9px] text-zinc-700">
        <p>ICE_GODS_GLOBAL_INFRASTRUCTURE // 2026</p>
        <p className="flex items-center gap-2"><Zap className="w-3 h-3" /> MORE POWERFUL THAN ALIENS BRAIN</p>
      </footer>
    </div>
  );
};

export default App;


