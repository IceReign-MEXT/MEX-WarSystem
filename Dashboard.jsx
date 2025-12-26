import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Zap, 
  Activity, 
  Globe, 
  Database, 
  Lock, 
  Terminal,
  Cpu,
  BarChart3,
  TrendingUp,
  ExternalLink
} from 'lucide-react';

const App = () => {
  const [supply, setSupply] = useState(30000000000);
  const [revenue, setRevenue] = useState(0.00);
  const [status, setStatus] = useState("SYNCHRONIZING");
  const [marketCap, setMarketCap] = useState(0);

  // Metadata from your provided keys
  const DEPLOY_ID = "T6H7KF46NT1GFP9BDRVNQ3D5GI7JPXZ671";
  const GOD_WALLET = "0x7D7A4820355E8597e089BEeB15cEa308cEf3eda3";
  const SOL_WALLET = "5s3vajJvaAbabQvxFdiMfg14y23b2jvK6K2Mw4PYcYK";

  useEffect(() => {
    const timer = setTimeout(() => setStatus("SYSTEM ACTIVE"), 2000);
    const interval = setInterval(() => {
      setRevenue(prev => prev + (Math.random() * 0.001));
    }, 5000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-black text-cyan-400 font-mono overflow-x-hidden selection:bg-cyan-900 selection:text-white">
      {/* Background Grid Effect */}
      <div className="fixed inset-0 bg-[linear-gradient(rgba(0,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.05)_1px,transparent_1px)] bg-[size:30px_30px] pointer-events-none"></div>

      {/* Navigation Header */}
      <nav className="relative z-10 border-b border-cyan-900 bg-black/80 backdrop-blur-md p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-cyan-500 rounded-sm flex items-center justify-center animate-pulse">
              <Shield className="text-black w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tighter">ICE GODS COMMAND</span>
          </div>
          <div className="hidden md:flex gap-6 text-xs font-bold uppercase tracking-widest">
            <a href="#" className="hover:text-white transition-colors">Oracle</a>
            <a href="#" className="hover:text-white transition-colors">War-Chest</a>
            <a href="#" className="hover:text-white transition-colors">Nodes</a>
            <span className="text-green-500 underline underline-offset-4 decoration-2">{status}</span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto p-6 space-y-8">
        
        {/* Top Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Total Supply" value="30.0B" subValue="$IBS" icon={<Database className="w-4 h-4" />} color="text-cyan-400" />
          <StatCard title="Passive Fee" value="1.0%" subValue="REVENUE" icon={<Zap className="w-4 h-4" />} color="text-yellow-400" />
          <StatCard title="Est. Revenue" value={`${revenue.toFixed(4)}`} subValue="MON" icon={<TrendingUp className="w-4 h-4" />} color="text-green-400" />
          <StatCard title="Market Status" value="FRONT-LINE" subValue="ACTIVE" icon={<Activity className="w-4 h-4" />} color="text-purple-400" />
        </div>

        {/* Central Display Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Terminal */}
          <div className="lg:col-span-2 space-y-6">
            <div className="border border-cyan-900 bg-gray-900/40 p-6 rounded-lg backdrop-blur-sm">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-sm font-bold flex items-center gap-2 tracking-[0.2em] uppercase">
                  <Terminal className="w-4 h-4" /> System Logs
                </h2>
                <span className="text-[10px] opacity-50">ID: {DEPLOY_ID}</span>
              </div>
              <div className="space-y-3 text-[13px]">
                <LogEntry time="19:50:01" msg="Establishing Cross-Chain Bridge to Helius Solana..." type="info" />
                <LogEntry time="19:50:05" msg={`Scanning Maker Wallet: ${GOD_WALLET}`} type="info" />
                <LogEntry time="19:51:12" msg="Tokenomics Verified: 30,000,000,000 IBS detected." type="success" />
                <LogEntry time="19:52:45" msg="Alchemy RPC Pulse: 12ms latency." type="success" />
                <LogEntry time="19:54:20" msg="Passive Revenue Filter Enabled: 1% Fee Active." type="warning" />
                <div className="animate-pulse flex items-center gap-2 text-cyan-500">
                  <span className="w-2 h-2 bg-cyan-500 rounded-full"></span>
                  Listening for incoming trades...
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <WalletPanel title="ETH/Monad God Wallet" address={GOD_WALLET} />
              <WalletPanel title="Solana Dev God Wallet" address={SOL_WALLET} />
            </div>
          </div>

          {/* Sidebar Tools */}
          <div className="space-y-6">
            <div className="border border-cyan-900 bg-cyan-950/20 p-6 rounded-lg">
              <h3 className="text-xs font-bold uppercase mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4" /> Global Control
              </h3>
              <div className="space-y-4">
                <ControlToggle label="Auto-Taxation" active={true} />
                <ControlToggle label="Oracle Sync" active={true} />
                <ControlToggle label="Dashboard Public" active={true} />
                <button className="w-full mt-4 py-3 bg-cyan-500 text-black font-bold uppercase text-xs hover:bg-white transition-all rounded">
                  Sync with Alchemy RPC
                </button>
              </div>
            </div>

            <div className="border border-cyan-900 bg-gray-900/40 p-6 rounded-lg">
              <h3 className="text-xs font-bold uppercase mb-4">Network Distribution</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] uppercase">
                  <span>Circulating</span>
                  <span>100%</span>
                </div>
                <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-500 w-full animate-pulse"></div>
                </div>
                <p className="text-[10px] opacity-50 mt-4 leading-relaxed italic">
                  "The Alien Brain system distributes 30B tokens into the frontline. 1% of every movement flows back to the Godhead."
                </p>
              </div>
            </div>
          </div>

        </div>
      </main>

      <footer className="relative z-10 border-t border-cyan-900 mt-20 p-8 text-center bg-black/80">
        <p className="text-[10px] uppercase tracking-[0.5em] opacity-30">
          Ice Gods Empire © 2025 // Secure Token Infrastructure
        </p>
      </footer>
    </div>
  );
};

const StatCard = ({ title, value, subValue, icon, color }) => (
  <div className="border border-cyan-900 bg-gray-900/40 p-5 rounded-lg hover:border-cyan-400 transition-colors cursor-crosshair">
    <div className="flex items-center gap-2 text-[10px] uppercase opacity-50 mb-2 tracking-widest">
      {icon} {title}
    </div>
    <div className={`text-3xl font-bold ${color} tracking-tight`}>
      {value} <span className="text-xs opacity-50 font-normal">{subValue}</span>
    </div>
  </div>
);

const LogEntry = ({ time, msg, type }) => {
  const colors = {
    info: "text-cyan-400",
    success: "text-green-400",
    warning: "text-yellow-400",
    error: "text-red-400"
  };
  return (
    <div className="flex gap-4 font-mono">
      <span className="opacity-30">[{time}]</span>
      <span className={colors[type] || "text-white"}>{msg}</span>
    </div>
  );
};

const WalletPanel = ({ title, address }) => (
  <div className="border border-cyan-900 bg-black/40 p-4 rounded-lg">
    <div className="text-[10px] opacity-50 uppercase mb-2 flex items-center gap-1">
      <Globe className="w-3 h-3" /> {title}
    </div>
    <div className="text-[11px] break-all text-white font-bold bg-gray-800/50 p-3 rounded border border-cyan-900/30">
      {address}
    </div>
    <div className="flex justify-end mt-2">
      <button className="text-[10px] flex items-center gap-1 hover:text-white transition-colors">
        VIEW ON EXPLORER <ExternalLink className="w-3 h-3" />
      </button>
    </div>
  </div>
);

const ControlToggle = ({ label, active }) => (
  <div className="flex justify-between items-center">
    <span className="text-[11px] uppercase tracking-wider">{label}</span>
    <div className={`w-8 h-4 rounded-full relative transition-colors ${active ? 'bg-cyan-500' : 'bg-gray-700'}`}>
      <div className={`absolute top-1 left-1 w-2 h-2 rounded-full bg-black transition-all ${active ? 'translate-x-4' : 'translate-x-0'}`}></div>
    </div>
  </div>
);

export default App;


