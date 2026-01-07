import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, onSnapshot, doc, setDoc } from 'firebase/firestore';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { Shield, Zap, Terminal, Activity, Lock, Wallet, ChevronRight, Fingerprint, Globe } from 'lucide-react';

// YOUR UNIQUE FIREBASE CONFIG
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
  const [wallet, setWallet] = useState(null);
  const [isVerified, setIsVerified] = useState(false);
  const [activeTab, setActiveTab] = useState('TERMINAL');
  const [ethPrice, setEthPrice] = useState(2642.88);
  const [terminalLogs, setTerminalLogs] = useState(["SYSTEM_INITIALIZED", "AWAITING_COMMAND..."]);

  // SYNC WITH BOT BACKEND
  useEffect(() => {
    signInAnonymously(auth);
    onAuthStateChanged(auth, (u) => {
      setUser(u);
      if (u) {
        // This listener detects if the user paid via the BOT or the WEB
        onSnapshot(collection(db, 'artifacts', appId, 'public', 'data', 'verified_users'), (snap) => {
          setIsVerified(snap.docs.some(d => d.id === u.uid));
        });
      }
    });

    // LIVE ETH PRICE SIMULATION
    const priceTimer = setInterval(() => {
      setEthPrice(p => p + (Math.random() - 0.5) * 5);
    }, 3000);
    return () => clearInterval(priceTimer);
  }, []);

  const handleCommand = (cmd) => {
    setActiveTab(cmd);
    const time = new Date().toLocaleTimeString();
    if (!isVerified && cmd !== 'TERMINAL') {
      setTerminalLogs(prev => [`[${time}] ERROR: ACCESS_DENIED. NODE_INACTIVE.`, ...prev]);
    } else {
      setTerminalLogs(prev => [`[${time}] EXECUTING_/${cmd}_PROTOCOL...`, ...prev]);
    }
  };

  const activateNode = async () => {
    if (!wallet || !user) return;
    await setDoc(doc(db, 'artifacts', appId, 'public', 'data', 'verified_users', user.uid), {
      wallet,
      timestamp: new Date().toISOString(),
      status: 'ACTIVE',
      platform: 'WEB_DASHBOARD'
    });
    setTerminalLogs(prev => [`[${new Date().toLocaleTimeString()}] SUCCESS: NODE_ACTIVATED.`, ...prev]);
  };

  return (
    <div className="min-h-screen bg-[#020202] text-white font-mono p-4 md:p-10 selection:bg-cyan-500 selection:text-black">
      <div className="max-w-7xl mx-auto border border-white/10 rounded-[2.5rem] bg-black/40 backdrop-blur-3xl overflow-hidden shadow-2xl">
        
        {/* HEADER */}
        <div className="p-8 border-b border-white/5 flex flex-wrap justify-between items-center bg-white/5 gap-4">
          <div className="flex items-center gap-6">
            <div className="bg-white text-black p-3 rounded-2xl shadow-[0_0_15px_rgba(255,255,255,0.2)]"><Shield size={24}/></div>
            <div>
              <h1 className="text-4xl font-black italic tracking-tighter leading-none">ICE_GODS</h1>
              <div className="flex gap-4 mt-1">
                <span className="text-[10px] text-cyan-500 font-bold animate-pulse uppercase">● Sovereign_OS_V2</span>
                <span className="text-[10px] text-zinc-500 font-bold">ETH: ${ethPrice.toFixed(2)}</span>
              </div>
            </div>
          </div>
          <button onClick={() => setWallet("0x" + Math.random().toString(16).slice(2,10).toUpperCase())} 
            className="px-6 py-2 border border-white/20 rounded-full text-[10px] font-black uppercase tracking-widest hover:bg-white hover:text-black transition-all">
            {wallet ? wallet : "CONNECT_WALLET"}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[600px]">
          {/* SIDEBAR - COMMAND HANDLER */}
          <div className="lg:col-span-3 border-r border-white/5 p-8 space-y-3">
            <p className="text-[10px] text-zinc-700 font-black mb-6 tracking-[0.3em]">COMMAND_CENTER</p>
            {['TERMINAL', 'STRIKE', 'SNIPERS', 'RAID'].map(tab => (
              <button key={tab} onClick={() => handleCommand(tab)} 
                className={`w-full text-left p-4 rounded-xl text-xs font-black transition-all ${activeTab === tab ? 'bg-white text-black translate-x-2' : 'text-zinc-500 hover:text-white hover:bg-white/5'}`}>
                /{tab}
              </button>
            ))}
          </div>

          {/* MAIN ENGINE VIEW */}
          <div className="lg:col-span-6 p-8 md:p-12 bg-black/20">
            {activeTab === 'TERMINAL' ? (
              <div className="space-y-4">
                <h2 className="text-5xl font-black italic mb-10 tracking-tighter">NEXUS_STREAM</h2>
                <div className="space-y-2">
                  {terminalLogs.map((log, i) => (
                    <p key={i} className="text-[11px] text-cyan-500 font-bold tracking-widest animate-in fade-in slide-in-from-left-2">{log}</p>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                {!isVerified ? (
                  <div className="animate-in zoom-in-95 duration-500">
                    <Lock size={64} className="text-zinc-800 mb-8 mx-auto" />
                    <h3 className="text-4xl font-black italic mb-4">ACCESS_LOCKED</h3>
                    <p className="text-[10px] text-zinc-500 uppercase tracking-widest max-w-sm mb-10 leading-relaxed font-bold">
                      Protocol /{activeTab} requires an active sovereign node. Activate via the vault below.
                    </p>
                    <button onClick={activateNode} className="px-12 py-4 bg-white text-black font-black rounded-full hover:scale-110 transition-transform shadow-[0_0_30px_rgba(255,255,255,0.1)]">
                      ACTIVATE_NODE (0.5 SOL)
                    </button>
                  </div>
                ) : (
                  <div className="animate-pulse">
                    <Zap size={64} className="text-cyan-500 mb-6 mx-auto" />
                    <h3 className="text-4xl font-black italic text-cyan-500">/{activeTab}_ENGAGED</h3>
                    <p className="text-xs text-zinc-400 mt-4 font-bold tracking-widest uppercase">Scanning Blockchain Mempool for Alpha...</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* VAULT PANEL */}
          <div className="lg:col-span-3 bg-white/5 p-8 flex flex-col justify-between">
            <div className="space-y-8">
              <p className="text-[10px] text-zinc-600 font-black tracking-widest uppercase">Architect_Vaults</p>
              <div className="space-y-4">
                <div className="bg-black p-5 rounded-2xl border border-white/5">
                  <p className="text-[8px] text-zinc-700 font-bold mb-1">SOLANA_NETWORK</p>
                  <p className="text-[9px] text-zinc-400 truncate tracking-tighter">{VAULT_SOL}</p>
                </div>
                <div className="bg-black p-5 rounded-2xl border border-white/5">
                  <p className="text-[8px] text-zinc-700 font-bold mb-1">ETH_NETWORK</p>
                  <p className="text-[9px] text-zinc-400 truncate tracking-tighter">{VAULT_ETH}</p>
                </div>
              </div>
            </div>
            <div className="pt-10 border-t border-white/5">
              <div className="flex items-center gap-4 text-zinc-700">
                <Fingerprint size={24}/>
                <span className="text-[9px] font-black uppercase tracking-[0.3em]">Identity_Secured</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


