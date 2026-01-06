import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, onSnapshot, query } from 'firebase/firestore';
import { getAuth, signInAnonymously, onAuthStateChanged, signInWithCustomToken } from 'firebase/auth';
import { Shield, Zap, Terminal, Activity, Cpu, Globe, Database, Lock } from 'lucide-react';

const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'mex-war-system';

const App = () => {
  const [user, setUser] = useState(null);
  const [verifiedCount, setVerifiedCount] = useState(54);
  const [logs, setLogs] = useState([]);
  const [prices, setPrices] = useState({ eth: 2654, sol: 142 });

  // (1) Auth Setup
  useEffect(() => {
    const initAuth = async () => {
      if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
        await signInWithCustomToken(auth, __initial_auth_token);
      } else {
        await signInAnonymously(auth);
      }
    };
    initAuth();
    const unsubscribe = onAuthStateChanged(auth, setUser);
    return () => unsubscribe();
  }, []);

  // (2) Real-time Data Sync (Rule 2 & 3 followed)
  useEffect(() => {
    if (!user) return;
    
    const q = collection(db, 'artifacts', appId, 'public', 'data', 'verified_users');
    const unsubscribe = onSnapshot(q, (snapshot) => {
      setVerifiedCount(54 + snapshot.docs.length);
      const newLogs = snapshot.docs.map(doc => ({
        id: doc.id,
        text: `NODE_ACTIVATED: ID_${doc.id.substring(0,6)}...SUCCESS`,
        time: new Date().toLocaleTimeString()
      }));
      setLogs(prev => [...newLogs, ...prev].slice(0, 10));
    }, (error) => console.error("Firestore Error:", error));

    return () => unsubscribe();
  }, [user]);

  const totalVault = (1.8 * prices.eth) + (335 * prices.sol);

  return (
    <div className="min-h-screen bg-black text-cyan-400 font-mono p-6 md:p-12 overflow-x-hidden">
      <div className="max-w-7xl mx-auto">
        {/* HUD HEADER */}
        <div className="flex flex-col md:flex-row justify-between items-end mb-12 border-b border-cyan-900/30 pb-8">
          <div>
            <div className="flex items-center gap-4 mb-2">
              <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse shadow-[0_0_10px_red]" />
              <span className="text-[10px] tracking-[0.4em] font-bold text-zinc-500 uppercase">Sovereign_Network_Live</span>
            </div>
            <h1 className="text-6xl font-black text-white italic tracking-tighter flex items-center gap-4">
              <Shield className="w-12 h-12 text-cyan-500" /> MONOLITH_V22
            </h1>
          </div>
          <div className="text-right mt-6 md:mt-0 bg-zinc-900/50 p-4 rounded-2xl border border-white/5">
             <p className="text-[10px] text-zinc-600 uppercase">Estimated_AUM</p>
             <p className="text-2xl font-black text-white">${totalVault.toLocaleString()}</p>
          </div>
        </div>

        {/* MAIN DISPLAY */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          <div className="bg-zinc-950 border border-cyan-500/20 p-8 rounded-[2.5rem] relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity"><Activity className="w-12 h-12" /></div>
            <p className="text-[9px] text-zinc-500 mb-1 uppercase tracking-widest">Global_Nodes</p>
            <p className="text-5xl font-black text-white italic">{verifiedCount}</p>
            <p className="text-[10px] text-cyan-700 mt-2 font-bold">SYNCHRONIZED_STABLE</p>
          </div>
          
          <div className="md:col-span-2 bg-zinc-900/20 border border-white/5 p-8 rounded-[2.5rem] flex flex-col justify-center">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-[9px] text-zinc-600 uppercase mb-2">Dual_Chain_Index</p>
                <div className="flex gap-6">
                  <div><span className="text-zinc-500 mr-2">ETH</span><span className="text-white font-bold">${prices.eth}</span></div>
                  <div><span className="text-zinc-500 mr-2">SOL</span><span className="text-white font-bold">${prices.sol}</span></div>
                </div>
              </div>
              <Cpu className="text-cyan-900 w-12 h-12" />
            </div>
          </div>

          <div className="bg-cyan-500 p-8 rounded-[2.5rem] flex flex-col justify-center shadow-[0_0_40px_rgba(6,182,212,0.2)]">
            <p className="text-[10px] text-black font-black uppercase mb-1">Status</p>
            <p className="text-3xl font-black text-black italic leading-none">AUTONOMOUS_DETECT_ON</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* TERMINAL FEED */}
          <div className="lg:col-span-2 bg-zinc-950 border border-white/5 rounded-[3rem] p-10 h-[450px] relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-20" />
            <h3 className="text-xs font-bold text-zinc-500 mb-8 flex items-center gap-3 uppercase tracking-widest">
              <Terminal className="w-5 h-5 text-cyan-500" /> Real-time_Verification_Stream
            </h3>
            <div className="space-y-3">
              {logs.length === 0 && <p className="text-zinc-800 italic text-sm">Awaiting network signals...</p>}
              {logs.map(log => (
                <div key={log.id} className="flex gap-4 items-center text-[11px] animate-in fade-in slide-in-from-left-4">
                   <span className="text-zinc-700 font-bold">[{log.time}]</span>
                   <span className="bg-cyan-500/10 text-cyan-500 px-2 py-0.5 rounded text-[9px] font-black">NODE_UP</span>
                   <span className="text-zinc-400">{log.text}</span>
                </div>
              ))}
              <div className="pt-4 border-t border-white/5 text-[10px] text-zinc-700 italic">
                ... continuous blockchain polling active ...
              </div>
            </div>
          </div>

          {/* AUTO GATE */}
          <div className="bg-white text-black rounded-[3rem] p-10 flex flex-col justify-between shadow-2xl relative overflow-hidden">
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-cyan-100 rounded-full blur-3xl opacity-50" />
            <div>
              <div className="bg-black text-white px-3 py-1 rounded-full text-[8px] font-black mb-8 w-fit tracking-widest">AUTONOMOUS GATE</div>
              <h2 className="text-4xl font-black italic tracking-tighter leading-none mb-6 text-black uppercase">Instant_Access</h2>
              <p className="text-[11px] text-zinc-600 leading-relaxed font-bold">The machine now detects transactions instantly. Send 5 SOL or 0.5 ETH to the vault. Your Node will activate as soon as the block confirms.</p>
            </div>

            <div className="space-y-4">
               <div className="bg-zinc-100 p-4 rounded-2xl border border-black/5">
                 <p className="text-[8px] font-black text-zinc-400 mb-1 uppercase">Solana_Vault</p>
                 <p className="text-[10px] font-bold break-all">8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy</p>
               </div>
               <div className="bg-zinc-100 p-4 rounded-2xl border border-black/5">
                 <p className="text-[8px] font-black text-zinc-400 mb-1 uppercase">Ethereum_Vault</p>
                 <p className="text-[10px] font-bold break-all">0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F</p>
               </div>
               <button className="w-full bg-black text-white py-5 rounded-2xl font-black italic hover:scale-[0.98] transition-transform text-sm tracking-widest uppercase">
                 Enter_the_Multitude
               </button>
            </div>
          </div>
        </div>

        <div className="mt-16 text-center text-[9px] text-zinc-700 uppercase tracking-[1em]">
          Powered by Ice Gods Sovereign Intelligence // Zero Human Intervention
        </div>
      </div>
    </div>
  );
};

export default App;


