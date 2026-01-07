import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc, onSnapshot } from 'firebase/firestore';
import { Shield, Zap, Activity, Cpu, Lock, Terminal, Globe, User, Crosshair, Twitter, DollarSign, AlertTriangle } from 'lucide-react';

const firebaseConfig = JSON.parse(__firebase_config);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'mex-war-system';
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

export default function App() {
  const [user, setUser] = useState(null);
  const [telegramId, setTelegramId] = useState('');
  const [wallet, setWallet] = useState('');
  const [status, setStatus] = useState('UNAUTHORIZED');
  const [logs, setLogs] = useState(['[SYSTEM] OS_BOOT_SEQUENCE_COMPLETE', '[NET] CONNECTING_TO_SOL_MAINNET...']);
  const [prices, setPrices] = useState({ eth: '2652.97', sol: '140.80' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      await signInAnonymously(auth);
    };
    initAuth();
    onAuthStateChanged(auth, setUser);
    
    const timer = setInterval(() => {
      setPrices({
        eth: (2650 + Math.random() * 5).toFixed(2),
        sol: (140 + Math.random() * 2).toFixed(2)
      });
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const addLog = (msg) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 50)]);

  const handleSubscription = async () => {
    if (!telegramId || !wallet) {
      addLog("ERROR: MISSING_OPERATOR_CREDENTIALS");
      return;
    }
    setLoading(true);
    try {
      const userRef = doc(db, 'artifacts', appId, 'public', 'data', 'verified_users', telegramId);
      await setDoc(userRef, {
        telegramId,
        wallet,
        status: 'ACTIVE',
        subscription: 'PREMIUM',
        expiry: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        nodes: Math.floor(Math.random() * 5) + 1,
        last_action: 'NODE_ACTIVATION'
      });
      setStatus('ACTIVE');
      addLog(`SUCCESS: NODE_${telegramId}_ACTIVATED // SUBSCRIPTION_VERIFIED`);
    } catch (err) {
      addLog(`CRITICAL_ERROR: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#00f2ff] font-mono p-2 md:p-6 overflow-x-hidden">
      {/* Top Bar */}
      <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center border-b border-[#00f2ff]/20 pb-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Shield className="w-10 h-10 text-[#00f2ff] animate-pulse" />
            <div className="absolute inset-0 bg-[#00f2ff]/20 blur-xl rounded-full"></div>
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter italic">ICE_GODS // MONOLITH_V2</h1>
            <p className="text-[10px] text-cyan-700 tracking-[0.3em]">SOVEREIGN_COMMAND_AND_CONTROL</p>
          </div>
        </div>
        <div className="flex gap-8">
          <div className="text-right">
            <p className="text-[10px] text-zinc-500 uppercase">Solana_Mainnet</p>
            <p className="text-white font-bold">${prices.sol} <span className="text-green-500 text-[10px]">+2.4%</span></p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-zinc-500 uppercase">Ethereum_Network</p>
            <p className="text-white font-bold">${prices.eth} <span className="text-red-500 text-[10px]">-0.8%</span></p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Control Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-[#0a0a0a] border border-[#00f2ff]/30 p-6 rounded-sm shadow-[0_0_20px_rgba(0,242,255,0.05)]">
            <h3 className="flex items-center gap-2 text-sm font-bold mb-6 border-l-2 border-[#00f2ff] pl-2">
              <User className="w-4 h-4" /> OPERATOR_INITIALIZATION
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-[10px] text-zinc-500 mb-1 block">TELEGRAM_ID</label>
                <input 
                  value={telegramId}
                  onChange={(e) => setTelegramId(e.target.value)}
                  className="w-full bg-black border border-white/10 p-3 text-sm focus:border-[#00f2ff]/50 outline-none transition-all"
                  placeholder="e.g. 6453658778"
                />
              </div>
              <div>
                <label className="text-[10px] text-zinc-500 mb-1 block">SOL_WALLET_ADDRESS</label>
                <input 
                  value={wallet}
                  onChange={(e) => setWallet(e.target.value)}
                  className="w-full bg-black border border-white/10 p-3 text-sm focus:border-[#00f2ff]/50 outline-none transition-all"
                  placeholder="0x... or Solana Address"
                />
              </div>

              <div className="pt-4">
                <button 
                  onClick={handleSubscription}
                  disabled={loading}
                  className="w-full bg-[#00f2ff] text-black font-black py-4 flex items-center justify-center gap-2 hover:bg-white transition-all active:scale-95 shadow-[0_0_30px_rgba(0,242,255,0.2)]"
                >
                  <DollarSign className="w-5 h-5" />
                  {loading ? 'PROCESSING_PAYMENT...' : 'ACTIVATE_NODE (0.5 SOL)'}
                </button>
                <p className="text-[9px] text-zinc-600 mt-2 text-center uppercase tracking-widest">Lifetime Access // encrypted bridge</p>
              </div>
            </div>
          </div>

          <div className="bg-[#0a0a0a] border border-red-900/30 p-4 rounded-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-red-500 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> THREAT_LEVEL
              </span>
              <span className="text-[10px] bg-red-500/10 px-2 py-1 text-red-500">ELEVATED</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-black p-2 border border-white/5">
                <p className="text-zinc-500">SYNC</p>
                <p className="text-white">ENCRYPTED</p>
              </div>
              <div className="bg-black p-2 border border-white/5">
                <p className="text-zinc-500">NODES</p>
                <p className="text-white">12,401 ACTIVE</p>
              </div>
            </div>
          </div>
        </div>

        {/* Center Terminal */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="bg-[#050505] border border-[#00f2ff]/20 rounded-sm flex-1 flex flex-col min-h-[500px]">
            <div className="bg-[#00f2ff]/10 p-3 border-b border-[#00f2ff]/20 flex justify-between items-center">
              <span className="text-xs font-bold flex items-center gap-2 italic">
                <Terminal className="w-4 h-4" /> COMMAND_STREAM_V2.0
              </span>
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              </div>
            </div>
            <div className="p-4 flex-1 overflow-y-auto font-mono text-[11px] space-y-1">
              {logs.map((log, i) => (
                <div key={i} className={`p-1 ${log.includes('SUCCESS') ? 'bg-green-500/5 text-green-400' : log.includes('ERROR') ? 'bg-red-500/5 text-red-500' : ''}`}>
                  <span className="opacity-40">{`>>`}</span> {log}
                </div>
              ))}
              <div className="animate-pulse text-[#00f2ff]">_</div>
            </div>
          </div>
        </div>

        {/* Right Action Panel */}
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-[#0a0a0a] border border-white/10 p-4 rounded-sm">
            <h3 className="text-[10px] font-bold text-zinc-500 mb-4 tracking-widest uppercase">Quick_Strike_Assets</h3>
            <div className="space-y-2">
              <button className="w-full bg-zinc-900 border border-white/5 p-3 text-xs flex justify-between hover:border-[#00f2ff] transition-all">
                <span className="flex items-center gap-2"><Crosshair className="w-4 h-4"/> SNIPER_BOT</span>
                <span className="text-green-500">ONLINE</span>
              </button>
              <button className="w-full bg-zinc-900 border border-white/5 p-3 text-xs flex justify-between hover:border-[#00f2ff] transition-all">
                <span className="flex items-center gap-2"><Twitter className="w-4 h-4"/> X_RAIDER</span>
                <span className="text-green-500">READY</span>
              </button>
              <button className="w-full bg-zinc-900 border border-white/5 p-3 text-xs flex justify-between hover:border-[#00f2ff] transition-all">
                <span className="flex items-center gap-2"><Zap className="w-4 h-4"/> FLASH_LOAN</span>
                <span className="text-red-500">LOCKED</span>
              </button>
            </div>
          </div>

          <div className="p-6 border-2 border-dashed border-[#00f2ff]/10 flex flex-col items-center justify-center text-center">
            <Cpu className="w-12 h-12 mb-4 opacity-20" />
            <p className="text-[10px] text-zinc-600">WAITING_FOR_MARKETING_PUSH</p>
            <p className="text-[9px] text-zinc-800 mt-1 italic">"Zero marketing, pure tech."</p>
          </div>
        </div>
      </div>
    </div>
  );
}


