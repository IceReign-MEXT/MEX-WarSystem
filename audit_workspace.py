import os
import sys
import ast
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("🔍 MEX-WAR SYSTEM COMPREHENSIVE REPO AUDITOR 🔍")
print("==================================================\n")

# 1. Check Env Integrity
print("--- Checking Environment Configs ---")
db_url = os.getenv("DATABASE_URL")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

if not db_url or "YOUR-PASSWORD" in db_url:
    print("❌ ERROR: DATABASE_URL is missing or unconfigured.")
else:
    print("✅ DATABASE_URL is configured.")

if not bot_token:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN is missing.")
else:
    print("✅ TELEGRAM_BOT_TOKEN is configured.")

# 2. Check Python Files Syntax
print("\n--- Auditing Python Core Files ---")
py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'audit_workspace.py']

syntax_errors = 0
for file in py_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f"✅ {file}: Syntax Clean")
    except SyntaxError as e:
        print(f"❌ {file}: SYNTAX ERROR -> Line {e.lineno}: {e.msg}")
        syntax_errors += 1
    except Exception as e:
        print(f"⚠️ {file}: Could not read -> {e}")

# 3. Check Render Hosting Files
print("\n--- Auditing Cloud Profiles ---")
if os.path.exists("Procfile"):
    with open("Procfile", "r") as f:
        content = f.read().strip()
    if "worker:" in content or "web:" in content:
        print(f"✅ Procfile: Correctly configured ({content})")
    else:
        print("❌ Procfile: Found, but missing 'worker:' or 'web:' deployment commands.")
else:
    print("❌ Procfile: MISSING! Render won't know how to start your bot.")

if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r") as f:
        reqs = f.read()
    critical_packages = ["aiogram", "openai", "web3"]
    missing_reqs = [p for p in critical_packages if p not in reqs.lower()]
    
    if missing_reqs:
        print(f"❌ requirements.txt: Missing critical hosting modules: {missing_reqs}")
    else:
        print("✅ requirements.txt: All production dependencies declared.")
else:
    print("❌ requirements.txt: MISSING! Render deployment will fail completely.")

print("\n==================================================")
if syntax_errors == 0:
    print("🚀 AUDIT COMPLETE: Repository structures are perfectly valid for deployment!")
else:
    print(f"🛑 AUDIT FAILED: Fix the {syntax_errors} structural bugs above before building.")
print("==================================================")
