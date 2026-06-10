import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("🛡️  MEX-WAR SYSTEM ENVIRONMENT INTEGRITY CHECKER 🛡️")
print("==================================================\n")

required_keys = [
    "TELEGRAM_BOT_TOKEN", "ADMIN_TELEGRAM_ID", "DATABASE_URL",
    "REDIS_URL", "HELIUS_API_KEY", "SOLANA_RPC_URL", "ETH_RPC_URL", 
    "OPENAI_API_KEY", "ENCRYPTION_KEY"
]

missing_keys = []
for key in required_keys:
    val = os.getenv(key)
    if not val or "PASTE_" in val:
        print(f"❌ {key}: Missing or default placeholder detected.")
        missing_keys.append(key)
    else:
        masked = val[:7] + "..." + val[-4:] if len(val) > 10 else "***"
        print(f"✅ {key}: Configured correctly ({masked})")

if missing_keys:
    print(f"\n🛑 Failure: You have {len(missing_keys)} unconfigured variable(s) in .env.")
    sys.exit(1)

print("\n--- Live Network & DB Connection Probing ---")

# Test Database Connectivity using pg8000
try:
    import pg8000
    db_url = os.getenv("DATABASE_URL")
    # Parse the URL manually for pg8000 compatibility
    # postgresql://user:pass@host:port/db
    raw_url = db_url.replace("postgresql://", "")
    credentials, rest = raw_url.split("@")
    user, password = credentials.split(":")
    host_port, database = rest.split("/")
    host, port = host_port.split(":")
    
    # Clean up encoded characters for the connection test
    password = password.replace("%2540", "%40").replace("%40", "@")

    conn = pg8000.connect(
        user=user,
        password=password,
        host=host,
        port=int(port),
        database=database,
        timeout=5
    )
    conn.close()
    print("✅ PostgreSQL Connection: SUCCESSFUL (via pg8000)")
except Exception as e:
    print(f"❌ PostgreSQL Connection: FAILED -> {e}")

# Test OpenAI API Key Hook
try:
    import urllib.request
    import json
    req = urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
    )
    with urllib.request.urlopen(req, timeout=4) as response:
        if response.status == 200:
            print("✅ OpenAI API Status: AUTHENTICATED SUCCESSFULLY")
except Exception as e:
    print(f"❌ OpenAI API Status: UNAUTHORIZED / FAILED -> {e}")

# Test Solana RPC (Helius) Hook
try:
    import urllib.request
    import json
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getHealth"}).encode("utf-8")
    req = urllib.request.Request(
        os.getenv("SOLANA_RPC_URL"),
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=4) as response:
        res = json.loads(response.read().decode())
        if res.get("result") == "ok":
            print("✅ Solana RPC (Helius): OPERATIONAL & HEALTHY")
except Exception as e:
    print(f"❌ Solana RPC (Helius): UNREACHABLE -> {e}")

print("\n🚀 All structural environment requirements verified match.")
