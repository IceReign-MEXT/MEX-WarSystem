import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, onSnapshot, doc, setDoc, query, orderBy, limit } from 'firebase/firestore';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { Shield, Zap, Terminal, Activity, Cpu, Globe, Database, Lock, Wallet, Crosshair, Target, Fingerprint, ChevronRight, BarChart3, ArrowUpRight, ArrowDownRight } from 'lucide-react';

// FIREBASE CONFIG
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

const VAULT_SOL = "8dtuyskTtsB78DFDPWZszarvDpedwftKYCoMdZwjHbxy";
const VAULT_ETH = "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F";

export default function App() {
  const [user, setUser] = useState(null);
  const [walletAddress, setWalletAddress] = useState(null);
  const [isVerified, setIsVerified] = useState(false);
  const [logs, setLogs] = useState([]);
  const [ethPrice, setEthPrice] = useState(2642.88);
  const [solPrice, setSolPrice] = useState(142.15);
  const [activeTab, setActiveTab] = useState('TERMINAL');
  const [loading, setLoading] = useState(false);

  // Authenticate and fetch status
  useEffect(() => {
    signInAnonymously(auth);
    onAuthStateChanged(auth, (u) => {
      setUser(u);
      if (u) checkVerification(u.uid);
    });
    
    // Price Simulation
    const timer = setInterval(() => {
      setEthPrice(p => p + (Math.random() - 0.5) * 5);
      setSolPrice(p => p + (Math.random() - 0.5) * 2);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const checkVerification = async (uid) => {
    const q = collection(db, 'artifacts', appId, 'public', 'data', 'verified_users');
    onSnapshot(q, (snapshot) => {
      const isUserFound = snapshot.docs.some(doc => doc.id === uid);
      setIsVerified(isUserFound);
      
      const newLogs = snapshot.docs.map(doc => ({
        id: doc.id,
        text: `INCOMING_NODE_${doc.id.substring(0,6).toUpperCase()}_ACTIVATED`,
        time: new Date().toLocaleTimeString()
      }));
      setLogs(newLogs.slice(0, 15));
    });
  };

  const connectWallet = async () => {
    setLoading(true);
    setTimeout(() => {
      setWalletAddress("0x" + Math.random().toString(16).slice(2, 10).toUpperCase() + "...7FC1");
      setLoading(false);
    }, 1000);
  };

  const processPayment = async () => {
    if (!walletAddress) return;
    setLoading(true);
    setTimeout(async () => {
      if (user) {
        await setDoc(doc(db, 'artifacts', appId, 'public', 'data', 'verified_users', user.uid), {
          wallet: walletAddress,
          timestamp: new Date().toISOString(),
          status: 'ACTIVE'
        });
        setIsVerified(true);
      }
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#020202] text-[#efefef] font-mono p-2 md:p-6 selection:bg-cyan-500 selection:text-black">
      {/* GLOBAL GRID OVERLAY */}
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none" />
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

      <div className="max-w-[1800px] mx-auto relative z-10">
        
        {/* TOP MONITORING BAR */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-zinc-800 border border-zinc-800 mb-6 rounded-lg overflow-hidden">
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">ETH/USD</span>
             <div className="flex items-center gap-2">
                <span className="text-sm font-black italic">${ethPrice.toFixed(2)}</span>
                <ArrowUpRight size={12} className="text-green-500" />
             </div>
          </div>
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">SOL/USD</span>
             <div className="flex items-center gap-2">
                <span className="text-sm font-black italic">${solPrice.toFixed(2)}</span>
                <ArrowDownRight size={12} className="text-red-500" />
             </div>
          </div>
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">NETWORK_LOAD</span>
             <span className="text-xs font-black text-cyan-500 animate-pulse">OPTIMAL [0.02ms]</span>
          </div>
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">SOVEREIGN_OS</span>
             <span className="text-xs font-black text-white/50">V22.0.1_STABLE</span>
          </div>
        </div>

        {/* MAIN TERMINAL HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-6">
          <div>
            <div className="flex items-center gap-4 mb-2">
              <div className="w-12 h-12 bg-white flex items-center justify-center text-black">
                <Shield size={32} />
              </div>
              <h1 className="text-5xl md:text-8xl font-black italic tracking-tighter uppercase leading-none">
                ICE_GODS<span className="text-cyan-500 opacity-50">.</span>IO
              </h1>
            </div>
            <p className="text-[10px] text-zinc-500 tracking-[0.5em] font-bold">AUTONOMOUS_WAR_SYSTEM_ESTABLISHED_2026</p>
          </div>
          
          <div className="flex flex-col items-end gap-4 w-full md:w-auto">
            <button 
              onClick={connectWallet}
              className={`w-full md:w-auto px-8 py-3 border ${walletAddress ? 'border-cyan-500 text-cyan-500 shadow-[0_0_20px_rgba(6,182,212,0.2)]' : 'border-white/20 text-white'} rounded-full text-[10px] font-black tracking-widest uppercase transition-all hover:bg-white/5 flex items-center justify-center gap-3`}
            >
              <Wallet size={16} />
              {loading ? "LINKING..." : walletAddress ? walletAddress : "CONNECT_SECURE_WALLET"}
            </button>
            <div className="flex gap-4">
               <div className="flex items-center gap-2 text-[8px] text-zinc-600 font-bold uppercase">
                  <Globe size={10} /> 12_REGION_EDGE_NODES
               </div>
               <div className="flex items-center gap-2 text-[8px] text-zinc-600 font-bold uppercase">
                  <Database size={10} /> FIRESTORE_SYNCED
               </div>
            </div>
          </div>
        </header>

        {/* WORKSTATION GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* SIDEBAR: COMMAND HANDLER */}
          <div className="lg:col-span-3 space-y-4">
            <div className="bg-zinc-900/20 border border-white/5 p-6 rounded-3xl backdrop-blur-xl">
              <h3 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.3em] mb-8 flex items-center gap-2">
                <Terminal size={14} /> SYSTEM_CMDS
              </h3>
              <div className="space-y-3">
                {['TERMINAL', 'STRIKE', 'SNIPERS', 'RAID', 'MEMPOOL'].map((cmd) => (
                  <button 
                    key={cmd}
                    onClick={() => setActiveTab(cmd)}
                    className={`group w-full flex items-center justify-between p-4 rounded-xl text-[11px] font-black transition-all ${activeTab === cmd ? 'bg-white text-black translate-x-2' : 'hover:bg-white/5 text-zinc-500'}`}
                  >
                    <div className="flex items-center gap-3">
                       <span className={activeTab === cmd ? 'text-black' : 'text-zinc-800'}>//</span>
                       <span>/{cmd}</span>
                    </div>
                    <ChevronRight size={14} className={activeTab === cmd ? 'opacity-100' : 'opacity-0 group-hover:opacity-50 transition-opacity'} />
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-black border border-white/5 p-8 rounded-3xl">
               <p className="text-[10px] font-black text-cyan-500 mb-4 tracking-widest animate-pulse">PROTOCOL_FEE</p>
               <div className="flex items-end gap-2 mb-6">
                  <span className="text-5xl font-black italic">0.5</span>
                  <span className="text-xl font-black text-zinc-500 italic mb-1">SOL/ETH</span>
               </div>
               <p className="text-[9px] text-zinc-600 leading-relaxed font-bold uppercase mb-8">
                 Access is permanent. Node activation grants access to all strike tools and autonomous Telegram bot functionality.
               </p>
               <button 
                onClick={processPayment}
                className="w-full bg-zinc-100 text-black py-4 rounded-xl font-black text-xs uppercase hover:bg-cyan-500 transition-colors"
               >
                 {loading ? "EXECUTING..." : isVerified ? "PROTOCOL_ACTIVE" : "INITIALIZE_NODE"}
               </button>
            </div>
          </div>

          {/* MAIN INTERFACE: THE MONOLITH */}
          <div className="lg:col-span-6">
            <div className="bg-black border-2 border-zinc-900 rounded-[3rem] p-6 md:p-12 min-h-[600px] relative overflow-hidden shadow-[inset_0_0_100px_rgba(0,0,0,1)]">
               
               {/* UI DECOR */}
               <div className="absolute top-0 right-0 p-12 opacity-[0.02] rotate-12"><Cpu size={300} /></div>

               {activeTab === 'TERMINAL' && (
                 <div className="relative">
                    <div className="flex justify-between items-center mb-12">
                       <h2 className="text-4xl font-black italic tracking-tighter uppercase">Nexus_Surveillance</h2>
                       <Activity className="text-cyan-500 animate-pulse" />
                    </div>
                    <div className="space-y-4">
                       {logs.map((log, i) => (
                         <div key={i} className="flex gap-4 items-center text-[10px] group">
                           <span className="text-zinc-800">[{log.time}]</span>
                           <span className="text-cyan-900 group-hover:text-cyan-500 transition-colors">>></span>
                           <span className="text-zinc-500 font-bold tracking-widest uppercase">{log.text}</span>
                           <div className="flex-1 border-b border-zinc-900/50 border-dashed" />
                           <span className="text-zinc-800">0x00A{i}</span>
                         </div>
                       ))}
                       {logs.length === 0 && (
                         <div className="py-20 text-center opacity-20 italic text-xs uppercase tracking-widest">
                            Waiting for On-Chain Signatures...
                         </div>
                       )}
                    </div>
                 </div>
               )}

               {activeTab !== 'TERMINAL' && !isVerified && (
                 <div className="h-full flex flex-col items-center justify-center text-center py-20 relative z-20">
                    <div className="w-24 h-24 rounded-full border border-white/10 flex items-center justify-center mb-8 bg-zinc-900/20 backdrop-blur-xl">
                       <Lock size={32} className="text-zinc-700" />
                    </div>
                    <h3 className="text-3xl font-black italic mb-4 tracking-tighter">ACCESS_RESTRICTED</h3>
                    <p className="text-[10px] text-zinc-500 max-w-xs uppercase leading-relaxed tracking-widest font-bold">
                       System Command <span className="text-white italic">/{activeTab}</span> requires an active sovereign node. Connect your wallet and initiate the activation protocol.
                    </p>
                    <button 
                      onClick={processPayment}
                      className="mt-10 px-12 py-4 bg-white text-black font-black text-xs rounded-full hover:scale-110 transition-transform shadow-[0_0_30px_rgba(255,255,255,0.1)]"
                    >
                       PAY_PROTOCOL_FEE
                    </button>
                 </div>
               )}

               {activeTab !== 'TERMINAL' && isVerified && (
                 <div className="relative animate-in fade-in duration-700">
                    <h2 className="text-5xl font-black italic mb-12 tracking-tighter uppercase text-cyan-500">{activeTab}_INTERFACE</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                       <div className="bg-zinc-900/30 border border-white/5 p-8 rounded-3xl">
                          <BarChart3 className="text-cyan-900 mb-4" />
                          <p className="text-[10px] text-zinc-500 mb-2 uppercase">Mempool_Depth</p>
                          <p className="text-3xl font-black italic">84.2_GB/S</p>
                       </div>
                       <div className="bg-zinc-900/30 border border-white/5 p-8 rounded-3xl">
                          <Target className="text-cyan-900 mb-4" />
                          <p className="text-[10px] text-zinc-500 mb-2 uppercase">Whale_Alerts</p>
                          <p className="text-3xl font-black italic">ACTIVE</p>
                       </div>
                       <div className="md:col-span-2 bg-cyan-500/5 border border-cyan-500/20 p-8 rounded-3xl">
                          <div className="flex items-center gap-4 mb-4">
                             <Fingerprint className="text-cyan-500" />
                             <p className="text-[10px] font-black uppercase text-cyan-500">Live_Bot_Link_Active</p>
                          </div>
                          <p className="text-[11px] text-zinc-400 font-bold uppercase leading-relaxed">
                             System identifying whale movement on SOLANA_MAINNET. Strike nodes are positioned for front-run entry.
                          </p>
                       </div>
                    </div>
                 </div>
               )}
            </div>
          </div>

          {/* RIGHT SIDEBAR: VAULT & IDENTITY */}
          <div className="lg:col-span-3 space-y-6">
             <div className="bg-zinc-900/20 border border-white/5 p-8 rounded-[2.5rem]">
                <h4 className="text-[10px] font-black text-zinc-500 mb-8 tracking-[0.4em] uppercase">Identity_Sectors</h4>
                <div className="space-y-6">
                   <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-zinc-800 flex items-center justify-center rounded-xl"><UserIcon /></div>
                      <div>
                         <p className="text-[8px] text-zinc-600 uppercase">Current_User</p>
                         <p className="text-[10px] font-black">{walletAddress ? "VERIFIED_OPERATOR" : "GUEST_USER"}</p>
                      </div>
                   </div>
                   <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-zinc-800 flex items-center justify-center rounded-xl"><Server size={18} /></div>
                      <div>
                         <p className="text-[8px] text-zinc-600 uppercase">Assigned_Node</p>
                         <p className="text-[10px] font-black uppercase tracking-tighter">MEX_SOVEREIGN_0024</p>
                      </div>
                   </div>
                </div>
             </div>

             <div className="bg-white text-black p-8 rounded-[2.5rem] relative overflow-hidden group">
                <div className="relative z-10">
                   <p className="text-[10px] font-black uppercase tracking-widest mb-6 border-b border-black/10 pb-4">Architect_Vaults</p>
                   <div className="space-y-4">
                      <div>
                         <p className="text-[8px] font-black uppercase mb-1 opacity-40">Solana_Mainnet</p>
                         <p className="text-[10px] font-bold truncate tracking-tighter select-all">{VAULT_SOL}</p>
                      </div>
                      <div>
                         <p className="text-[8px] font-black uppercase mb-1 opacity-40">Ethereum_Mainnet</p>
                         <p className="text-[10px] font-bold truncate tracking-tighter select-all">{VAULT_ETH}</p>
                      </div>
                   </div>
                </div>
                <div className="absolute -bottom-10 -right-10 opacity-5 group-hover:scale-110 transition-transform duration-1000">
                   <Shield size={180} />
                </div>
             </div>
          </div>

        </div>

        {/* FOOTER TERMINAL */}
        <footer className="mt-12 flex flex-col md:flex-row justify-between items-center gap-6 text-[9px] font-black text-zinc-800 uppercase tracking-[0.3em] border-t border-white/5 pt-12">
           <div className="flex items-center gap-6">
              <span className="flex items-center gap-2"><Fingerprint size={14}/> IDENTITY_SECURED</span>
              <span className="flex items-center gap-2 text-cyan-900"><Activity size={14}/> REAL_TIME_SYNC</span>
           </div>
           <p className="text-center">Mex Robert © 2026 // MONOLITH Autonomous Sovereign OS</p>
           <div className="flex gap-8">
              <span className="hover:text-white cursor-pointer transition-colors">Documentation</span>
              <span className="hover:text-white cursor-pointer transition-colors">Security_Log</span>
           </div>
        </footer>

      </div>
    </div>
  );
}

const UserIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
);

const Server = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
);


