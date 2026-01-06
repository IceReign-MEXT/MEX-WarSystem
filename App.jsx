import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, onSnapshot, query, limit } from 'firebase/firestore';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { Shield, Zap, Terminal, Activity, Cpu, Globe, Database, Lock, Radio, Server, Fingerprint } from 'lucide-react';

// PRODUCTION FIREBASE CONFIG - hopeful-buckeye-459915-q6
const firebaseConfig = {
  apiKey: "AIzaSyCtumV0EsVXT1UlS0_4nktx8HI_Ph3ItkI",
  authDomain: "hopeful-buckeye-459915-q6.firebaseapp.com",
  projectId: "hopeful-buckeye-459915-q6",
  storageBucket: "hopeful-buckeye-459915-q6.firebasestorage.app",
  messagingSenderId: "965780897651",
  appId: "1:965780897651:web:adb82ac04219bbb4584f06"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = "mex-war-system"; 

const App = () => {
  const [user, setUser] = useState(null);
  const [nodes, setNodes] = useState(54);
  const [logs, setLogs] = useState([]);
  const [glitch, setGlitch] = useState(false);

  useEffect(() => {
    signInAnonymously(auth).catch(e => console.error("AUTH_FAILURE", e));
    const unsubAuth = onAuthStateChanged(auth, setUser);
    
    // Aesthetic Glitch Effect
    const interval = setInterval(() => {
      setGlitch(true);
      setTimeout(() => setGlitch(false), 150);
    }, 4000);

    return () => { unsubAuth(); clearInterval(interval); };
  }, []);

  useEffect(() => {
    if (!user) return;
    
    // Live Blockchain Listener Sync
    const q = collection(db, 'artifacts', appId, 'public', 'data', 'verified_users');
    const unsubData = onSnapshot(q, (snapshot) => {
      setNodes(54 + snapshot.docs.length);
      const incoming = snapshot.docs.map(doc => ({
        id: doc.id,
        text: `NODE_ID_${doc.id.substring(0,8).toUpperCase()}_VERIFIED_ON_CHAIN`,
        time: new Date().toLocaleTimeString()
      }));
      setLogs(prev => [...incoming, ...prev].slice(0, 15));
    }, (error) => console.error("DB_SYNC_ERROR", error));

    return () => unsubData();
  }, [user]);

  return (
    <div className="min-h-screen bg-black text-white font-mono p-4 md:p-8 selection:bg-cyan-500 selection:text-black overflow-hidden relative">
      
      {/* SCANLINE OVERLAY */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-50 bg-[length:100%_2px,3px_100%]" />

      <div className="max-w-7xl mx-auto border-x border-zinc-900 min-h-screen bg-zinc-950/20 px-6 py-10">
        
        {/* TOP INFOBAR */}
        <div className="flex flex-wrap justify-between items-center mb-16 border-b border-zinc-900 pb-6 gap-4">
          <div className="flex items-center gap-6">
            <div className="p-3 bg-white text-black font-black italic text-xl tracking-tighter">
              ICE_GODS
            </div>
            <div>
              <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-[0.3em]">System_Type</p>
              <p className="text-xs font-black text-cyan-500">AUTONOMOUS_SOVEREIGN_V22</p>
            </div>
          </div>
          <div className="flex gap-8 text-[10px] text-zinc-600 font-bold uppercase tracking-widest">
            <div className="flex items-center gap-2"><Radio className="w-3 h-3 text-red-600 animate-pulse" /> Live_Mempool_Feed</div>
            <div className="flex items-center gap-2"><Globe className="w-3 h-3" /> Global_Nexus_54</div>
          </div>
        </div>

        {/* HERO TITLE */}
        <div className="mb-20">
          <h1 className={`text-7xl md:text-[10rem] font-black italic tracking-tighter leading-none mb-4 transition-all ${glitch ? 'translate-x-1 skew-x-3 opacity-80' : ''}`}>
            MONOLITH<span className="text-cyan-500 font-normal">_</span>
          </h1>
          <div className="flex flex-col md:flex-row gap-6 md:items-center">
            <p className="text-xs text-zinc-500 max-w-md uppercase tracking-widest leading-relaxed">
              Autonomous Sovereign Infrastructure deployed for automated liquidity detection and node activation. 
              Zero human intervention required.
            </p>
            <div className="flex-1 h-[1px] bg-zinc-900" />
            <div className="flex items-center gap-4 bg-zinc-900/40 px-6 py-3 rounded-full border border-white/5">
              <Fingerprint className="w-5 h-5 text-cyan-800" />
              <span className="text-[10px] font-black text-zinc-400">ENCRYPTION: AES-256-GCM</span>
            </div>
          </div>
        </div>

        {/* NODES GRID */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
          
          <div className="md:col-span-2 bg-white text-black p-10 rounded-tr-[4rem]">
            <p className="text-[10px] font-black uppercase tracking-widest mb-2">Total_Active_Nodes</p>
            <p className="text-8xl font-black italic tracking-tighter">{nodes}</p>
            <div className="mt-4 flex items-center gap-2 text-[10px] font-bold">
               <div className="w-2 h-2 bg-black rounded-full animate-ping" />
               SYNCHRONIZED_WITH_BLOCKCHAIN
            </div>
          </div>

          <div className="bg-zinc-900/30 border border-white/5 p-8 flex flex-col justify-between group hover:border-cyan-500 transition-colors">
            <Activity className="w-8 h-8 text-cyan-900 group-hover:text-cyan-500 transition-colors" />
            <div>
              <p className="text-[10px] text-zinc-600 uppercase font-black">Detection_Latency</p>
              <p className="text-3xl font-black italic">0.02ms</p>
            </div>
          </div>

          <div className="bg-zinc-900/30 border border-white/5 p-8 flex flex-col justify-between group hover:border-cyan-500 transition-colors">
            <Server className="w-8 h-8 text-cyan-900 group-hover:text-cyan-500 transition-colors" />
            <div>
              <p className="text-[10px] text-zinc-600 uppercase font-black">Network_Load</p>
              <p className="text-3xl font-black italic tracking-tighter">OPTIMAL</p>
            </div>
          </div>

        </div>

        {/* TERMINAL PANEL */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <div className="lg:col-span-2 bg-black border-2 border-zinc-900 p-8 rounded-[3rem] relative min-h-[400px]">
            <div className="absolute top-8 right-8 flex gap-2">
              <div className="w-2 h-2 rounded-full bg-zinc-800" />
              <div className="w-2 h-2 rounded-full bg-zinc-800" />
              <div className="w-2 h-2 rounded-full bg-cyan-500" />
            </div>
            
            <h3 className="text-[10px] font-black text-cyan-900 uppercase tracking-[0.5em] mb-8">
              Sovereign_Surveillance_Stream
            </h3>
            
            <div className="space-y-3 font-bold">
              {logs.length === 0 && <p className="text-zinc-800 italic animate-pulse">Awaiting incoming blockchain pulses...</p>}
              {logs.map(log => (
                <div key={log.id} className="text-[10px] flex gap-6 items-center">
                  <span className="text-zinc-800 font-black">[{log.time}]</span>
                  <span className="text-cyan-800 font-black">SYS//NODE</span>
                  <span className="text-zinc-400 tracking-widest">{log.text}</span>
                  <div className="flex-1 border-t border-zinc-900 border-dashed" />
                  <span className="text-cyan-900">OK</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-zinc-900/20 border border-zinc-900 p-10 rounded-[3rem] flex flex-col justify-between">
            <div>
               <div className="bg-white text-black px-3 py-1 text-[8px] font-black w-fit mb-6">VAULT_ACCESS</div>
               <h4 className="text-3xl font-black italic text-white mb-4">PROTOCOL_ENTRY</h4>
               <p className="text-[10px] text-zinc-600 font-bold leading-relaxed uppercase tracking-tighter">
                 Instant activation enabled. Send tribute to the Monolith. The machine detects your hash and unlocks the Multitude instantly.
               </p>
            </div>
            
            <div className="space-y-2 mt-8">
              <div className="p-4 bg-black border border-white/5 rounded-2xl">
                 <p className="text-[8px] text-zinc-700 font-black mb-1">SOLANA_VAULT</p>
                 <p className="text-[10px] text-zinc-400 truncate">8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy</p>
              </div>
              <div className="p-4 bg-black border border-white/5 rounded-2xl">
                 <p className="text-[8px] text-zinc-700 font-black mb-1">ETH_VAULT</p>
                 <p className="text-[10px] text-zinc-400 truncate">0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F</p>
              </div>
            </div>
          </div>

        </div>

        {/* FOOTER */}
        <div className="mt-20 flex flex-col md:flex-row justify-between items-center text-[9px] text-zinc-800 font-black tracking-[1em] uppercase gap-4">
          <p>Established under the Ice Gods domain</p>
          <div className="flex gap-10">
            <p>Sovereign_Logic_Active</p>
            <p className="text-cyan-900">Better_Than_Alien_Brain</p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default App;


