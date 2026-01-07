import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, onSnapshot, doc, setDoc } from 'firebase/firestore';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { Shield, Zap, Terminal, Activity, Cpu, Globe, Database, Lock, Wallet, Target, Fingerprint, ChevronRight, BarChart3, ArrowUpRight, ArrowDownRight } from 'lucide-react';

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
  const [tgId, setTgId] = useState("6453658778"); // Defaulting to your ID
  const [isVerified, setIsVerified] = useState(false);
  const [logs, setLogs] = useState([]);
  const [ethPrice, setEthPrice] = useState(2642.88);
  const [solPrice, setSolPrice] = useState(142.15);
  const [activeTab, setActiveTab] = useState('TERMINAL');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    signInAnonymously(auth);
    onAuthStateChanged(auth, (u) => {
      setUser(u);
    });

    // Listen for activations globally to show in terminal
    const q = collection(db, 'artifacts', appId, 'public', 'data', 'verified_users');
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const isUserFound = snapshot.docs.some(doc => doc.id === tgId);
      setIsVerified(isUserFound);

      const newLogs = snapshot.docs.map(doc => ({
        id: doc.id,
        text: `NODE_${doc.id.substring(0,6).toUpperCase()}_ACTIVATED`,
        time: new Date().toLocaleTimeString()
      }));
      setLogs(newLogs.slice(-10).reverse());
    });

    const timer = setInterval(() => {
      setEthPrice(p => p + (Math.random() - 0.5) * 5);
      setSolPrice(p => p + (Math.random() - 0.5) * 2);
    }, 3000);
    
    return () => {
        clearInterval(timer);
        unsubscribe();
    };
  }, [tgId]);

  const connectWallet = async () => {
    setLoading(true);
    setTimeout(() => {
      setWalletAddress("0x" + Math.random().toString(16).slice(2, 10).toUpperCase() + "...7FC1");
      setLoading(false);
    }, 8000);
  };

  const processPayment = async () => {
    if (!tgId) return;
    setLoading(true);
    // CRITICAL: We save the doc using the Telegram ID as the ID
    try {
        await setDoc(doc(db, 'artifacts', appId, 'public', 'data', 'verified_users', tgId), {
            wallet: walletAddress || "LOCAL_NODE",
            timestamp: new Date().toISOString(),
            status: 'ACTIVE',
            type: 'SOVEREIGN_NODE'
        });
        setLoading(false);
    } catch (error) {
        console.error("Activation failed", error);
        setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020202] text-[#efefef] font-mono p-2 md:p-6 overflow-x-hidden">
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none" />
      
      <div className="max-w-[1800px] mx-auto relative z-10">
        {/* STATS BAR */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-zinc-800 border border-zinc-800 mb-6 rounded-lg overflow-hidden">
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase">ETH/USD</span>
             <span className="text-sm font-black italic">${ethPrice.toFixed(2)}</span>
          </div>
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase">SOL/USD</span>
             <span className="text-sm font-black italic">${solPrice.toFixed(2)}</span>
          </div>
          <div className="bg-black p-4 flex justify-between items-center text-cyan-500">
             <span className="text-[10px] font-bold uppercase">SYNC_STATUS</span>
             <span className="text-xs font-black animate-pulse">ENCRYPTED</span>
          </div>
          <div className="bg-black p-4 flex justify-between items-center">
             <span className="text-[10px] text-zinc-500 font-bold uppercase">VERIFIED_NODES</span>
             <span className="text-xs font-black">{logs.length}</span>
          </div>
        </div>

        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-6">
          <div>
            <div className="flex items-center gap-4 mb-2">
              <div className="w-12 h-12 bg-white flex items-center justify-center text-black rounded-lg">
                <Shield size={32} />
              </div>
              <h1 className="text-5xl md:text-7xl font-black italic tracking-tighter uppercase">ICE_GODS</h1>
            </div>
            <p className="text-[10px] text-zinc-600 tracking-[0.4em] font-bold">MONOLITH_OS_V2_ACTIVE</p>
          </div>

          <div className="flex flex-col items-end gap-3">
             <div className="bg-zinc-900 border border-white/10 p-2 px-4 rounded-full flex items-center gap-4">
                <span className="text-[10px] text-zinc-500 font-bold uppercase">TG_SYNC:</span>
                <input 
                    className="bg-transparent border-none outline-none text-[10px] font-black text-cyan-500 w-24"
                    value={tgId}
                    onChange={(e) => setTgId(e.target.value)}
                    placeholder="ENTER_TG_ID"
                />
             </div>
             <button onClick={connectWallet} className="px-6 py-2 border border-white/10 rounded-full text-[10px] font-black uppercase hover:bg-white hover:text-black transition-all">
                {loading ? "CONNECTING..." : walletAddress ? walletAddress : "CONNECT_WALLET"}
             </button>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* NAV */}
          <div className="lg:col-span-3 space-y-4">
            <div className="bg-zinc-900/40 border border-white/5 p-6 rounded-3xl">
              <p className="text-[10px] font-black text-zinc-600 mb-6 uppercase tracking-widest">System_Control</p>
              {['TERMINAL', 'STRIKE', 'SNIPERS', 'RAID'].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} className={`w-full text-left p-4 rounded-xl text-xs font-black mb-2 transition-all ${activeTab === tab ? 'bg-white text-black translate-x-2' : 'text-zinc-500 hover:text-zinc-200'}`}>
                  /{tab}
                </button>
              ))}
            </div>
            
            <div className="bg-white text-black p-8 rounded-3xl">
                <p className="text-[10px] font-black uppercase mb-4">Activation_Protocol</p>
                <div className="text-4xl font-black italic mb-6">0.5 <span className="text-lg opacity-50">SOL</span></div>
                <button onClick={processPayment} disabled={isVerified} className="w-full bg-black text-white py-4 rounded-xl font-black text-xs uppercase hover:bg-cyan-600 transition-all">
                    {isVerified ? "NODE_OPERATIONAL" : "INITIALIZE_STRIKE"}
                </button>
            </div>
          </div>

          {/* MAIN */}
          <div className="lg:col-span-6 bg-black border border-zinc-800 rounded-[2.5rem] p-8 md:p-12 relative min-h-[500px]">
             {activeTab === 'TERMINAL' ? (
                <div>
                   <h2 className="text-3xl font-black italic mb-8 uppercase flex items-center gap-4">
                     <Terminal className="text-cyan-500" /> Nexus_Surveillance
                   </h2>
                   <div className="space-y-4">
                      {logs.map((log, i) => (
                        <div key={i} className="flex items-center gap-4 text-[10px] font-bold text-zinc-500">
                           <span className="text-zinc-800">[{log.time}]</span>
                           <span className="text-cyan-600">>></span>
                           <span className="uppercase tracking-widest">{log.text}</span>
                        </div>
                      ))}
                      <div className="text-[10px] text-cyan-500 animate-pulse mt-10">_AWAITING_NEW_SIGNATURES...</div>
                   </div>
                </div>
             ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20">
                    {!isVerified ? (
                        <>
                            <Lock size={48} className="text-zinc-800 mb-6" />
                            <h3 className="text-2xl font-black italic mb-2 uppercase">Protocol_Locked</h3>
                            <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Node {tgId} requires activation.</p>
                        </>
                    ) : (
                        <div className="animate-in zoom-in duration-500">
                            <Zap size={64} className="text-cyan-500 mb-6 mx-auto animate-bounce" />
                            <h3 className="text-4xl font-black italic text-cyan-500 uppercase mb-2">{activeTab}_ENABLED</h3>
                            <p className="text-[10px] text-zinc-400 uppercase tracking-widest">Bot ID {tgId} synchronized with monolith.</p>
                        </div>
                    )}
                </div>
             )}
          </div>

          {/* ASSETS */}
          <div className="lg:col-span-3 space-y-6">
             <div className="bg-zinc-900/20 border border-white/5 p-6 rounded-3xl">
                <p className="text-[10px] font-black text-zinc-600 mb-6 uppercase tracking-widest">Identity_Log</p>
                <div className="space-y-4">
                   <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-zinc-800 rounded flex items-center justify-center text-zinc-500"><Cpu size={14}/></div>
                      <div>
                         <p className="text-[8px] text-zinc-600 uppercase">Operator_ID</p>
                         <p className="text-[10px] font-black truncate">{tgId}</p>
                      </div>
                   </div>
                   <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-zinc-800 rounded flex items-center justify-center text-zinc-500"><Globe size={14}/></div>
                      <div>
                         <p className="text-[8px] text-zinc-600 uppercase">Region</p>
                         <p className="text-[10px] font-black">LAG_NODE_01</p>
                      </div>
                   </div>
                </div>
             </div>

             <div className="bg-cyan-500 p-8 rounded-3xl text-black">
                <p className="text-[10px] font-black uppercase mb-6 opacity-60">Vault_Addresses</p>
                <div className="space-y-4">
                    <div>
                        <p className="text-[8px] font-black uppercase mb-1">SOL_TARGET</p>
                        <p className="text-[9px] font-bold truncate">{VAULT_SOL}</p>
                    </div>
                    <div>
                        <p className="text-[8px] font-black uppercase mb-1">ETH_TARGET</p>
                        <p className="text-[9px] font-bold truncate">{VAULT_ETH}</p>
                    </div>
                </div>
             </div>
          </div>
        </div>

        <footer className="mt-20 border-t border-white/5 pt-10 pb-10 flex flex-col md:flex-row justify-between items-center gap-6 opacity-20">
            <div className="flex items-center gap-6 text-[8px] font-black uppercase tracking-[0.4em]">
                <Fingerprint size={12}/> IDENTITY_SECURED
                <Database size={12}/> FIRESTORE_LIVE
            </div>
            <p className="text-[8px] font-black uppercase tracking-[0.2em]">Mex Robert © 2026 // Sovereign Protocol</p>
        </footer>
      </div>
    </div>
  );
}


