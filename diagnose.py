#!/usr/bin/env python3

import os
import importlib

print("=" * 60)
print("MEX-WarSystem Diagnostic")
print("=" * 60)

modules = [
    "telegram",
    "flask",
    "aiohttp",
    "dotenv",
    "sqlalchemy",
    "psycopg2",
    "apscheduler"
]

print("\n[1] Python Modules")
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f"✅ {mod}")
    except Exception as e:
        print(f"❌ {mod} -> {e}")

print("\n[2] Environment Variables")

required_env = [
    "BOT_TOKEN",
    "ADMIN_ID",
    "MASTER_WALLET",
    "WEBHOOK_URL",
    "HELIUS_API_KEY",
    "DATABASE_URL",
    "BOT_USERNAME"
]

for var in required_env:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}")
    else:
        print(f"❌ {var}")

print("\n[3] Critical Files")

files = [
    "main.py",
    "database.py",
    "token_detector.py",
    "client_bot.py",
    "verify_deployment.py",
    ".env"
]

for f in files:
    if os.path.exists(f):
        print(f"✅ {f}")
    else:
        print(f"❌ {f}")

print("\n[4] Quick Result")

missing = []

for mod in modules:
    try:
        importlib.import_module(mod)
    except:
        missing.append(mod)

for var in required_env:
    if not os.getenv(var):
        missing.append(var)

if missing:
    print("\n⚠️ Missing Items:")
    for item in missing:
        print(" -", item)
else:
    print("\n✅ Basic setup appears complete")

print("\nDone.")
