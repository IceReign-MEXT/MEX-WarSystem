import React, { useState, useEffect } from 'react';
import { LineChart, Wallet, Shield, Zap } from 'lucide-react';

export default function App() {
    return (
        <div className="min-h-screen bg-slate-900 text-cyan-400 p-8 font-mono">
            <header className="border-b border-cyan-900 pb-4 mb-8">
                <h1 className="text-4xl font-bold tracking-tighter">ICE GODS ENGINE v1.01</h1>
                <p className="text-slate-500">Connected to Master Vault: 0x7D7A...eda3</p>
            </header>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-800 p-6 rounded-lg border border-cyan-500/20">
                    <Zap className="mb-2" />
                    <h2 className="text-xl">30B SUPPLY</h2>
                    <p className="text-3xl font-bold text-white">IBS TOKEN</p>
                </div>
                <div className="bg-slate-800 p-6 rounded-lg border border-cyan-500/20">
                    <LineChart className="mb-2" />
                    <h2 className="text-xl">REVENUE TAX</h2>
                    <p className="text-3xl font-bold text-white">1% PASSIVE</p>
                </div>
                <div className="bg-slate-800 p-6 rounded-lg border border-cyan-500/20">
                    <Shield className="mb-2" />
                    <h2 className="text-xl">SCM SCANNER</h2>
                    <p className="text-3xl font-bold text-white">ACTIVE</p>
                </div>
            </div>
            
            <div className="mt-12 p-8 bg-black/50 rounded-xl border border-cyan-500/10">
                <h3 className="text-2xl mb-4">SYSTEM LOGS</h3>
                <div className="space-y-2 text-sm text-cyan-700">
                    <p>> [INFO] Oracle Nodes Synchronized...</p>
                    <p>> [INFO] 101 Machine Monitoring Liquidity...</p>
                    <p>> [WARN] 0 Scams Detected in Last Block.</p>
                </div>
            </div>
        </div>
    );
}
