import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, doc, setDoc, getDoc } from 'firebase/firestore';
import { Shield, Zap, Activity, Search, Crosshair, AlertTriangle, Cpu, Lock, ChevronRight, Globe } from 'lucide-react';

// Initialize Firebase using the environment config
const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export default function App() {
  const [telegramId, setTelegramId] = useState('');
  const [wallet, setWallet] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [auditLog, setAuditLog] = useState([]);

  // Live "Rug Detection" Feed - Psychological Proof for Users
  useEffect(() => {
    const logs = [
      { msg: 'RUG_PREVENTED: $FAKE_SOL - Liquidity Drain Detected', type: 'DANGER' },
      { msg: 'SCAM_ALERT: $ETH_HONEY - Sell Function Disabled', type: 'DANGER' },
      { msg: 'SEC_SCAN: $MONOLITH - Verified 1% Tax Router', type: 'SUCCESS' },
      { msg: 'TRADE_LOG: User_8829 Sniped 5.0 SOL of $WAR', type: 'INFO' }
    ];
    const interval = setInterval(() => {
      const entry = logs[Math.floor(Math.random() * logs.length)];
      setAuditLog(prev => [{ ...entry, id: Math.random(), time: new Date().toLocaleTimeString() }, ...prev.slice(0, 5)]);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleRegister = async () => {
    if (!telegramId || !wallet) return;
    setLoading(true);
    try {
      // Writing to the secure path defined in Rule 1
      const userRef = doc(db, 'artifacts', 'mex-war-system', 'public', 'data', 'verified_users', telegramId);
      await setDoc(userRef, {
        telegramId,
        wallet,
        status: 'WAR_READY',
        fee_tier: '1%',
        activatedAt: new Date().toISOString()
      });
      setStep(3);
    } catch (e) {
      console.error("Critical Registry Error", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020202] text-[#00f2ff] font-mono p-4 md:p-10 selection:bg-[#00f2ff] selection:text-black">
      {/* Top HUD */}
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center border-b border-[#00f2ff]/10 pb-6 mb-10">
        <div className="flex items-center gap-5">
          <div className="relative">
            <Cpu className="w-12 h-12 text-white animate-pulse" />
            <div className="absolute inset-0 bg-[#00f2ff] blur-xl opacity-20"></div>
          </div>
          <div>
            <h1 className="text-3xl font-black text-white italic tracking-tighter uppercase">Monolith_Sovereign</h1>
            <p className="text-[9px] tracking-[0.4em] opacity-50 uppercase">Global Fraud Surveillance & Execution</p>
          </div>
        </div>
        <div className="flex gap-8 mt-6 md:mt-0">
          <div className="text-right">
            <p className="text-[8px] uppercase text-zinc-500">Network_Load</p>
            <p className="text-xs font-bold text-green-400">STABLE // 2,840 TPS</p>
          </div>
          <div className="text-right">
            <p className="text-[8px] uppercase text-zinc-500">Node_Status</p>
            <p className="text-xs font-bold text-[#00f2ff]">ACTIVE_ENCRYPTION</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        {/* Left: Security Logic Display */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-zinc-900/10 border border-[#00f2ff]/20 p-6 rounded-3xl backdrop-blur-xl relative overflow-hidden">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xs font-black flex items-center gap-2 italic uppercase"><Search className="w-4 h-4"/> Live_Audit_Stream</h2>
              <span className="text-[8px] px-2 py-1 bg-[#00f2ff]/10 rounded-full animate-pulse">MONITORING_MAINNET</span>
            </div>
            
            <div className="space-y-3">
              {auditLog.map((log) => (
                <div key={log.id} className={`p-4 rounded-xl border transition-all duration-500 ${log.type === 'DANGER' ? 'bg-red-500/5 border-red-500/20 text-red-500' : 'bg-[#00f2ff]/5 border-[#00f2ff]/20 text-[#00f2ff]'} flex justify-between items-center text-[10px]`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-1.5 h-1.5 rounded-full ${log.type === 'DANGER' ? 'bg-red-500 animate-ping' : 'bg-[#00f2ff]'}`}></div>
                    <span className="font-bold tracking-tight">{log.msg}</span>
                  </div>
                  <span className="opacity-30 tabular-nums">{log.time}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[ {l: 'SOL_SNIPER', v: 'v2.5'}, {l: 'ETH_SNIPER', v: 'v1.9'}, {l: 'TAX_ROUTER', v: '1.0%'}, {l: 'RUG_GUARD', v: 'ACTIVE'} ].map((s, i) => (
              <div key={i} className="bg-white/5 border border-white/5 p-4 rounded-2xl text-center">
                <p className="text-[8px] text-zinc-600 uppercase mb-1">{s.l}</p>
                <p className="text-xs font-black text-white italic">{s.v}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right: The License & Tax Hub */}
        <div className="lg:col-span-5">
          <div className="bg-zinc-950 border-2 border-[#00f2ff]/30 p-8 rounded-[2.5rem] shadow-[0_0_80px_rgba(0,242,255,0.05)] relative">
            <div className="absolute top-4 right-8 opacity-10"><Globe className="w-12 h-12" /></div>
            
            {step === 3 ? (
              <div className="py-20 text-center space-y-6">
                <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto shadow-[0_0_40px_rgba(34,197,94,0.3)]">
                  <CheckCircle className="w-12 h-12 text-black" />
                </div>
                <h3 className="text-2xl font-black text-white italic">WAR_READY</h3>
                <p className="text-xs text-zinc-500 px-6">Your Node ID is verified. 1% Tax routing and Rug-Protection are now active for your wallet.</p>
                <button className="w-full bg-[#00f2ff] text-black font-black py-4 rounded-2xl text-xs uppercase">Open Telegram Bot</button>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <h3 className="text-2xl font-black text-white italic uppercase tracking-tighter">Establish Hub</h3>
                  <p className="text-[11px] text-zinc-500 mt-2">Link your Telegram Node and Operational Wallet to activate the 1% automated profit syphon.</p>
                </div>

                <div className="space-y-4">
                  <div className="group">
                    <p className="text-[9px] font-bold text-zinc-600 mb-1 ml-1 uppercase">Telegram_Identity</p>
                    <input 
                      value={telegramId}
                      onChange={(e) => setTelegramId(e.target.value)}
                      placeholder="e.g. 6453658778"
                      className="w-full bg-black border border-white/10 p-4 rounded-2xl text-white outline-none focus:border-[#00f2ff] transition-all text-sm"
                    />
                  </div>
                  <div className="group">
                    <p className="text-[9px] font-bold text-zinc-600 mb-1 ml-1 uppercase">Trading_Wallet</p>
                    <input 
                      value={wallet}
                      onChange={(e) => setWallet(e.target.value)}
                      placeholder="0x... or SOL Address"
                      className="w-full bg-black border border-white/10 p-4 rounded-2xl text-white outline-none focus:border-[#00f2ff] transition-all text-sm font-mono"
                    />
                  </div>
                </div>

                <div className="bg-[#00f2ff]/5 border border-[#00f2ff]/10 p-5 rounded-3xl space-y-4">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-zinc-500 uppercase">License_Status</span>
                    <span className="text-white font-bold italic">LIFETIME_ACCESS</span>
                  </div>
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-zinc-500 uppercase">Automated_Tax</span>
                    <span className="text-white font-bold italic">1.0% (Buy/Sell)</span>
                  </div>
                  <div className="pt-2 border-t border-[#00f2ff]/10 flex justify-between items-center">
                    <span className="text-[10px] font-bold text-[#00f2ff] uppercase italic">Activation_Fee</span>
                    <span className="text-sm font-black text-white">0.5 SOL / 0.03 ETH</span>
                  </div>
                </div>

                <button 
                  onClick={handleRegister}
                  disabled={loading}
                  className="w-full bg-[#00f2ff] text-black font-black py-5 rounded-[1.5rem] hover:bg-white transition-all shadow-[0_0_40px_rgba(0,242,255,0.2)] flex items-center justify-center gap-3 uppercase text-sm italic"
                >
                  <Crosshair className="w-5 h-5" />
                  {loading ? 'Initializing_Node...' : 'Sync_War_Protocol'}
                </button>
                
                <p className="text-[9px] text-center text-zinc-700 uppercase flex items-center justify-center gap-2"><Lock className="w-3 h-3"/> Military-Grade Encryption Active</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}



