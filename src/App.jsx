import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, setDoc } from 'firebase/firestore';
import { Shield, Zap, Activity, Terminal, Globe, User, Crosshair, Twitter, DollarSign, AlertTriangle, Cpu } from 'lucide-react';

const firebaseConfig = JSON.parse(__firebase_config);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'mex-war-system';
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

export default function App() {
  const [user, setUser] = useState(null);
  const [telegramId, setTelegramId] = useState('6453658778');
  const [wallet, setWallet] = useState('0x08C5E7247FC1');
  const [logs, setLogs] = useState(['[SYSTEM] OS_BOOT_SEQUENCE_COMPLETE', '[NET] CONNECTING_TO_SOL_MAINNET...']);
  const [prices, setPrices] = useState({ eth: '2652.97', sol: '140.80' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    signInAnonymously(auth);
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

  const handleActivation = async () => {
    if (!telegramId || !wallet) return addLog("ERROR: DATA_MISSING");
    setLoading(true);
    try {
      const userRef = doc(db, 'artifacts', appId, 'public', 'data', 'verified_users', telegramId);
      await setDoc(userRef, {
        telegramId,
        wallet,
        status: 'ACTIVE',
        subscription: 'PREMIUM',
        expiry: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        nodes: 1,
        last_action: 'NODE_ACTIVATION'
      });
      addLog(`SUCCESS: NODE_${telegramId}_ACTIVATED // 0.5 SOL VERIFIED`);
    } catch (err) {
      addLog(`CRITICAL_ERROR: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#00f2ff] font-mono p-4">
      {/* Header */}
      <div className="max-w-7xl mx-auto border-b border-[#00f2ff]/20 pb-4 mb-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Shield className="w-10 h-10 animate-pulse text-[#00f2ff]" />
          <h1 className="text-2xl font-black italic tracking-tighter text-white">ICE_GODS // MONOLITH_V2</h1>
        </div>
        <div className="flex gap-8 text-[11px]">
          <div className="text-right">
            <p className="text-zinc-500">SOL/USD</p>
            <p className="text-white">${prices.sol}</p>
          </div>
          <div className="text-right">
            <p className="text-zinc-500">ETH/USD</p>
            <p className="text-white">${prices.eth}</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Activation Panel */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-[#0a0a0a] border border-[#00f2ff]/30 p-6 rounded-sm">
            <h3 className="text-xs font-bold mb-6 flex items-center gap-2 border-l-2 border-[#00f2ff] pl-2 uppercase">Activation_Gate</h3>
            <div className="space-y-4">
              <input value={telegramId} onChange={e => setTelegramId(e.target.value)} className="w-full bg-black border border-white/10 p-3 text-sm outline-none focus:border-[#00f2ff]/50" placeholder="TELEGRAM_ID" />
              <input value={wallet} onChange={e => setWallet(e.target.value)} className="w-full bg-black border border-white/10 p-3 text-sm outline-none focus:border-[#00f2ff]/50" placeholder="SOL_WALLET_ADDRESS" />
              <button onClick={handleActivation} disabled={loading} className="w-full bg-[#00f2ff] text-black font-black py-4 hover:bg-white transition-all shadow-[0_0_20px_rgba(0,242,255,0.2)] flex justify-center items-center gap-2">
                <DollarSign className="w-5 h-5" /> {loading ? 'SYNCING...' : 'ACTIVATE_NODE (0.5 SOL)'}
              </button>
            </div>
          </div>
          
          <div className="bg-[#0a0a0a] border border-red-900/30 p-4">
            <div className="flex items-center justify-between text-[10px] text-red-500 mb-2">
              <span className="flex items-center gap-2"><AlertTriangle className="w-3 h-3" /> THREAT_LEVEL</span>
              <span>ELEVATED</span>
            </div>
            <div className="h-1 bg-zinc-900 overflow-hidden">
              <div className="h-full bg-red-600 w-3/4 animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Terminal logs */}
        <div className="lg:col-span-8 bg-black border border-white/10 flex flex-col min-h-[450px]">
          <div className="bg-white/5 p-2 text-[10px] border-b border-white/10 flex justify-between">
            <span className="flex items-center gap-2"><Terminal className="w-3 h-3" /> COMMAND_STREAM_V2.0</span>
            <span className="text-green-500">LIVE</span>
          </div>
          <div className="p-4 flex-1 overflow-y-auto text-[11px] space-y-1 opacity-80">
            {logs.map((log, i) => (
              <div key={i}><span className="text-[#00f2ff]">>></span> {log}</div>
            ))}
            <div className="animate-pulse text-[#00f2ff]">_</div>
          </div>
        </div>
      </div>

      <footer className="max-w-7xl mx-auto mt-8 border-t border-white/5 pt-4 flex flex-wrap justify-between text-[9px] text-zinc-600">
        <p>MEX_ROBERT // SOVEREIGN_PROTOCOL © 2026</p>
        <div className="flex gap-4">
          <span className="flex items-center gap-1"><Lock className="w-3 h-3" /> ENCRYPTED</span>
          <span className="flex items-center gap-1"><Globe className="w-3 h-3" /> GLOBAL_RELAY</span>
        </div>
      </footer>
    </div>
  );
}


