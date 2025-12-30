import os
import time
import random
import threading
from flask import Flask, render_template_string
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- IDENTITY SETTINGS ---
OPERATOR = "Mex Robert"
VAULT = os.getenv("ADMIN_WALLET", "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F")
TARGET = os.getenv("TOKEN_ADDRESS", "0x2cFa3EAb79E5CfE34EAabfb6aCaAC0Da0565Aa77")

# --- INTEGRATED CYBERPUNK UI ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ICE GODS | NEXUS ROOT</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
        body { background: #020617; color: #f8fafc; font-family: 'JetBrains Mono', monospace; }
        .glow { box-shadow: 0 0 20px rgba(6, 182, 212, 0.2); border: 1px solid #0891b2; }
        .log-box { height: 300px; overflow-y: auto; scrollbar-width: none; }
        .log-box::-webkit-scrollbar { display: none; }
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-6xl mx-auto">
        <div class="flex flex-col md:flex-row justify-between mb-10 border-b border-cyan-900 pb-6">
            <div>
                <h1 class="text-4xl font-black text-white tracking-tighter">ICE GODS <span class="text-cyan-500 underline">WAR-SYSTEM</span></h1>
                <p class="text-cyan-600 text-[10px] font-bold uppercase tracking-[0.4em] mt-2">Operator: {{ operator }} // Status: Active</p>
            </div>
            <div class="mt-4 md:mt-0 text-right">
                <p class="text-[10px] text-slate-500 uppercase">System Vault</p>
                <p class="text-xs text-cyan-400 font-bold">{{ vault }}</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glow bg-cyan-900/10 p-6 rounded-3xl">
                <p class="text-[10px] text-cyan-700 uppercase mb-1">Volume Strike</p>
                <p class="text-2xl font-black text-white">ACTIVE</p>
            </div>
            <div class="glow bg-purple-900/10 p-6 rounded-3xl border-purple-900/30">
                <p class="text-[10px] text-purple-700 uppercase mb-1">Auto-Raid Engine</p>
                <p class="text-2xl font-black text-white">SCANNING</p>
            </div>
            <div class="glow bg-green-900/10 p-6 rounded-3xl border-green-900/30">
                <p class="text-[10px] text-green-700 uppercase mb-1">Tax Revenue</p>
                <p class="text-2xl font-black text-white">2.0% FIXED</p>
            </div>
        </div>

        <div class="bg-black rounded-3xl p-8 border border-white/5 relative overflow-hidden">
            <div class="absolute top-4 right-6 text-[8px] text-cyan-900 animate-pulse font-bold">MONAD_LINK_STABLE</div>
            <h3 class="text-[10px] font-black uppercase text-slate-500 mb-4 tracking-widest"><i class="fas fa-terminal mr-2"></i> System Logs</h3>
            <div id="logs" class="log-box text-xs text-slate-400 space-y-1">
                <p class="text-cyan-500">> [SYSTEM] MEX ROBERT INITIALIZING VALUE-NEXUS...</p>
                <p>> [SYSTEM] DETECTING LIQUIDITY ON MONAD TESTNET...</p>
                <p class="text-white">> [STRIKE] INJECTING VOLUME INTO {{ target }}</p>
            </div>
        </div>
    </div>

    <script>
        const logs = document.getElementById('logs');
        const actions = ["CAPTURED 2% TAX", "VOLUME STRIKE EXECUTED", "RAID SENT TO TWITTER", "NEXUS REVENUE ROUTED", "BOT_NODE_HEARTBEAT"];

        setInterval(() => {
            const p = document.createElement('p');
            const action = actions[Math.floor(Math.random()*actions.length)];
            p.innerHTML = `<span class="text-cyan-800">` + new Date().toLocaleTimeString() + `</span> > [ACTION] ` + action;
            logs.prepend(p);
            if(logs.children.length > 15) logs.lastChild.remove();
        }, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, operator=OPERATOR, vault=VAULT, target=TARGET)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
