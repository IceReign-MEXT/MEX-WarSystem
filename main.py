import os
import time
import random
import threading
from flask import Flask, render_template_string
from web3 import Web3
from dotenv import load_dotenv

# Load Environment
load_dotenv()

app = Flask(__name__)

# --- CONFIG ---
OPERATOR_NAME = "Mex Robert"
OPERATOR_HANDLE = "@RobertSmithETH"
ADMIN_WALLET = os.getenv("ADMIN_WALLET", "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL", "https://testnet-rpc.monad.xyz")
TOKEN_ADDR = os.getenv("TOKEN_ADDRESS", "0x2cFa3EAb79E5CfE34EAabfb6aCaAC0Da0565Aa77")

# --- DASHBOARD UI ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICE GODS | WAR-SYSTEM v3.5</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #020617; color: #22d3ee; font-family: monospace; }
        .neon-border { border: 1px solid #06b6d4; box-shadow: 0 0 15px rgba(6, 182, 212, 0.3); }
        .scanline { background: linear-gradient(to bottom, transparent 50%, rgba(34, 211, 238, 0.05) 50%); background-size: 100% 4px; }
    </style>
</head>
<body class="p-8 scanline min-h-screen">
    <div class="max-w-5xl mx-auto">
        <header class="border-b border-cyan-900 pb-4 mb-8">
            <h1 class="text-5xl font-black text-cyan-400 uppercase tracking-tighter">WAR-SYSTEM v3.5</h1>
            <p class="text-purple-500 font-bold">MONAD TESTNET // ALIEN-GRADE VOLUME ENGINE</p>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="neon-border bg-slate-900/80 p-6 rounded-lg">
                <p class="text-xs text-slate-400">STATUS</p>
                <p class="text-2xl font-bold text-green-400 animate-pulse">ONLINE</p>
            </div>
            <div class="neon-border bg-slate-900/80 p-6 rounded-lg">
                <p class="text-xs text-slate-400">OPERATOR</p>
                <p class="text-2xl font-bold">{{ name }}</p>
            </div>
            <div class="neon-border bg-slate-900/80 p-6 rounded-lg">
                <p class="text-xs text-slate-400">VAULT</p>
                <p class="text-sm font-bold truncate">{{ wallet }}</p>
            </div>
        </div>

        <div class="neon-border bg-black p-6 rounded-xl h-64 overflow-y-auto font-mono text-xs text-cyan-500">
            <p>> [SYS] INITIALIZING WAR-NEXUS MODULES...</p>
            <p>> [NET] CONNECTED TO MONAD CHAIN ID 10143</p>
            <p>> [WAR] TARGETING: {{ token }}</p>
            <p class="text-white animate-pulse">> [ACTIVE] INJECTING VOLUME STRIKES...</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML, name=OPERATOR_NAME, wallet=ADMIN_WALLET, token=TOKEN_ADDR)

def volume_loop():
    print(f"🔥 War-System Active for {OPERATOR_NAME}")
    while True:
        try:
            # High-Frequency Logic Here
            time.sleep(random.randint(300, 900))
        except Exception as e:
            print(f"⚠️ [MISFIRE]: {e}")

if __name__ == "__main__":
    threading.Thread(target=volume_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)