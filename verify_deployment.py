import os
import asyncio
import aiohttp
import psycopg2
from dotenv import load_dotenv

load_dotenv()

async def run_diagnostics():
    print("🛡️ --- MEX WARSYSTEM DEPLOYMENT VALIDATOR --- 🛡️\n")

    # 1. TEST DATABASE (SUPABASE)
    print("📡 Checking Supabase Connection...")
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute('SELECT 1')
        print("✅ DATABASE: Connected (PostgreSQL/Supabase)\n")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ DATABASE: Failed! Error: {e}\n")

    async with aiohttp.ClientSession() as session:
        # 2. TEST HELIUS API (SOLANA)
        print("⛓️ Checking Helius API (Solana RPC)...")
        helius_key = os.getenv("HELIUS_API_KEY")
        url = f"https://api.helius.xyz/v0/addresses/HxmywH2gW9ezQ2nBXwurpaWsZS6YvdmLF23R9WgMAM7p/balances?api-key={helius_key}"
        async with session.get(url) as resp:
            if resp.status == 200:
                print("✅ SOLANA RPC: Online (Helius)\n")
            else:
                print(f"❌ SOLANA RPC: Offline! Status: {resp.status}\n")

        # 3. TEST TELEGRAM WEBHOOK SYNC
        print("🤖 Checking Telegram Webhook Sync...")
        token = os.getenv("BOT_TOKEN")
        webhook_url = os.getenv("WEBHOOK_URL")
        tg_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        async with session.get(tg_url) as resp:
            data = await resp.json()
            current_url = data.get('result', {}).get('url', '')
            if webhook_url in current_url:
                print(f"✅ WEBHOOK: Correctly synced to {webhook_url}")
            else:
                print(f"❌ WEBHOOK: Mismatch! Currently set to: {current_url}")
                print(f"👉 Fix: Run 'python3 main.py' to reset it.\n")

    print("\n🚀 STATUS: IF ALL GREEN, YOU ARE READY FOR BCG SUBMISSION.")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())

