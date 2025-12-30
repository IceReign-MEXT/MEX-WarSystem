import os
import time
import random
import threading
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- IDENTITY ---
OPERATOR = "Mex Robert"
VAULT = os.getenv("ADMIN_WALLET", "0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F")
TARGET = os.getenv("TOKEN_ADDRESS", "0x2cFa3EAb79E5CfE34EAabfb6aCaAC0Da0565Aa77")

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ICE GODS | NEXUS ROOT</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #020617; color: #f8fafc; font-family: monospace; }
        .glow { box-shadow: 0 0 20px rgba(6, 182, 212, 0.2); border: 1px solid #0891b2; }
    </style>
</head>
<body class="p-10">
    <div class="max-w-4xl mx-auto glow bg-black/50 p-8 rounded-3xl">
        <h1 class="text-3xl font-black text-cyan-500 mb-2">WAR-SYSTEM ACTIVE</h1>
        <p class="text-xs text-slate-500 mb-6 uppercase tracking-widest">Operator: {{ operator }} // Vault: {{ vault }}</p>
        <div class="bg-slate-900/50 p-4 rounded-xl h-64 overflow-y-auto text-[10px] text-cyan-400 font-mono" id="logs">
            <p>> [SYSTEM] DEPLOYMENT SUCCESSFUL.</p>
            <p>> [NEXUS] MONITORING REVENUE STREAMS...</p>
        </div>
    </div>
    <script>
        setInterval(() => {
            const p = document.createElement('p');
            p.innerHTML = '> [' + new Date().toLocaleTimeString() + '] HEARTBEAT_STABLE';
            document.getElementById('logs').prepend(p);
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, operator=OPERATOR, vault=VAULT)

if __name__ == "__main__":
    # Render provides the PORT variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
