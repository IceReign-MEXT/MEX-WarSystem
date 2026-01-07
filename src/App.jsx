import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, doc, setDoc } from 'firebase/firestore';
import { Shield, Zap, Activity, Search, CheckCircle, Lock, ChevronRight, Crosshair, Cpu, Clock, Copy } from 'lucide-react';

const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export default function App() {
  const [telegramId, setTelegramId] = useState('');
  const [wallet, setWallet] = useState('');
  const [step, setStep] = useState(1); // 1: Input, 2: Payment, 3: Success
  const [loading, setLoading] = useState(false);
  const [scannedTokens, setScannedTokens] = useState([]);

  const SOL_ADDRESS = "YOUR_SOLANA_WALLET_HERE"; // REPLACE WITH YOUR ACTUAL WALLET

  useEffect(() => {
    const tokens = [
      { name: 'SOL_PEPE', gain: '+450%', chain: 'SOL' },
      { name: 'ETH_DOGE', gain: '+120%', chain: 'ETH' },
      { name: 'FROST_COIN', gain: '+890%', chain: 'SOL' },
      { name: 'SHADOW_SNIPE', gain: '+1100%', chain: 'SOL' }
    ];
    const interval = setInterval(() => {
      const base = tokens[Math.floor(Math.random() * tokens.length)];
      const newToken = { ...base, name: base.name + '_' + Math.floor(Math.random() * 99), gain: '+' + (Math.random() * 1200).toFixed(0) + '%', time: 'JUST NOW' };
      setScannedTokens(prev => [newToken, ...prev.slice(0, 5)]);
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  const handleInitiate = () => {
    if (!telegramId || !wallet) return;
    setStep(2);
  };

  const handleVerify = async () => {
    setLoading(true);
    // In production, you'd call a Helius or Alchemy API here to check the chain
    // For now, we simulate a 3-second security scan
    setTimeout(async () => {
      try {
        const userRef = doc(db, 'artifacts', 'mex-war-system', 'public', 'data', 'verified_users', telegramId);
        await setDoc(userRef, {
          telegramId,
          wallet,
          status: 'ACTIVE',
          subscription: 'PREMIUM',
          activatedAt: new Date().toISOString()
        });
        setStep(3);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 3000);
  };

  const copyToClipboard = (text) => {
    const el = document.createElement('textarea');
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
  };

  return (
    <div className="min-h-screen bg-[#020202] text-[#00f2ff] font-mono selection:bg-[#00f2ff] selection:text-black">
      {/* Top Ticker */}
      <div className="w-full bg-[#00f2ff] text-black text-[10px] font-black py-1 flex justify-center gap-8 overflow-hidden uppercase italic">
        <span className="flex items-center gap-1"><Activity className="w-3 h-3"/> SCANNER: ACTIVE</span>
        <span>TPS: 2,841</span>
        <span className="animate-pulse text-red-600">● LIVE_CHAIN_VERIFICATION_ENABLED</span>
      </div>

      <div className="max-w-7xl mx-auto p-4 md:p-10 grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left: Live Activity (The Proof) */}
        <div className="lg:col-span-7 space-y-8">
          <div className="flex items-center gap-5">
            <Shield className="w-14 h-14 text-white animate-pulse" />
            <div>
              <h1 className="text-4xl font-black text-white italic tracking-tighter uppercase">Monolith_V2</h1>
              <p className="text-[10px] tracking-[0.3em] text-[#00f2ff]/60 uppercase italic">Sovereign Sniper Interface</p>
            </div>
          </div>

          <div className="bg-zinc-900/20 border border-[#00f2ff]/20 rounded-2xl overflow-hidden backdrop-blur-md">
            <div className="bg-[#00f2ff]/10 p-4 border-b border-[#00f2ff]/20 flex justify-between items-center">
              <span className="text-xs font-black tracking-widest flex items-center gap-2"><Search className="w-4 h-4"/> LIVE_TARGETS</span>
              <span className="text-[9px] text-green-400 animate-pulse">MONITORING_MAINNET</span>
            </div>
            <div className="p-3 space-y-2">
              {scannedTokens.map((t, i) => (
                <div key={i} className="flex justify-between items-center p-3 bg-black/40 border border-white/5 rounded-xl">
                  <div className="flex items-center gap-4">
                    <div className="text-[8px] font-bold px-2 py-1 rounded border border-[#00f2ff]/30">{t.chain}</div>
                    <span className="text-xs font-bold text-white">{t.name}</span>
                  </div>
                  <span className="text-xs font-black text-green-400">{t.gain}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: The Payment/Activation Gate */}
        <div className="lg:col-span-5">
          <div className="bg-zinc-950 border-2 border-[#00f2ff]/30 p-8 rounded-[2rem] shadow-[0_0_100px_rgba(0,242,255,0.05)]">
            
            {step === 1 && (
              <div className="space-y-6">
                <h3 className="text-2xl font-black text-white italic uppercase tracking-tighter">1. Link Node</h3>
                <div className="space-y-4">
                  <input value={telegramId} onChange={(e) => setTelegramId(e.target.value)} placeholder="Telegram ID (e.g. 6453658778)" className="w-full bg-black border border-white/10 p-4 rounded-xl text-white outline-none focus:border-[#00f2ff] text-sm" />
                  <input value={wallet} onChange={(e) => setWallet(e.target.value)} placeholder="Your Trading Wallet" className="w-full bg-black border border-white/10 p-4 rounded-xl text-white outline-none focus:border-[#00f2ff] text-sm font-mono" />
                </div>
                <button onClick={handleInitiate} className="w-full bg-[#00f2ff] text-black font-black py-5 rounded-2xl hover:bg-white transition-all uppercase italic text-sm">Next Step</button>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-black text-white italic uppercase">2. Secure License</h3>
                  <Clock className="w-5 h-5 text-yellow-500 animate-spin" />
                </div>
                
                <div className="bg-[#00f2ff]/5 p-5 rounded-xl border border-[#00f2ff]/20">
                  <p className="text-[10px] text-zinc-500 mb-2 uppercase">Send Payment To:</p>
                  <div className="flex items-center gap-2 bg-black p-3 rounded border border-white/5 mb-3">
                    <span className="text-[10px] font-mono text-white truncate">{SOL_ADDRESS}</span>
                    <button onClick={() => copyToClipboard(SOL_ADDRESS)} className="text-[#00f2ff]"><Copy className="w-4 h-4"/></button>
                  </div>
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-zinc-400 uppercase">Amount:</span>
                    <span className="text-white">0.5 SOL</span>
                  </div>
                </div>

                <div className="text-[10px] text-zinc-500 leading-relaxed bg-black/50 p-3 rounded">
                  ⚠️ Note: Send only SOL to this address. The Monolith will scan the ledger for your wallet's signature once you click verify.
                </div>

                <button onClick={handleVerify} disabled={loading} className="w-full bg-white text-black font-black py-5 rounded-2xl hover:bg-[#00f2ff] transition-all uppercase italic text-sm">
                  {loading ? 'Scanning Blockchain...' : 'Verify Transaction'}
                </button>
                <button onClick={() => setStep(1)} className="w-full text-[10px] text-zinc-700 uppercase">Go Back</button>
              </div>
            )}

            {step === 3 && (
              <div className="py-16 text-center space-y-6">
                <CheckCircle className="w-20 h-20 text-green-500 mx-auto animate-bounce" />
                <h4 className="text-2xl font-black text-white italic tracking-tighter">SOVEREIGNTY_ESTABLISHED</h4>
                <p className="text-xs text-zinc-500">Transaction confirmed. Your Node ID is now active on the network.</p>
                <button className="w-full bg-[#00f2ff] text-black font-bold py-4 rounded-xl uppercase">Open Bot Terminal</button>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}


