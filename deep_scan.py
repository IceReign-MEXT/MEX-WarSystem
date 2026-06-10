import os

keywords = [
    "BOT_TOKEN",
    "HELIUS",
    "telegram",
    "send_message",
    "set_webhook",
    "airdrop",
    "token",
    "wallet",
    "deploy",
    "subscriber",
    "whale",
    "liquidity",
    "market_cap"
]

for file in os.listdir("."):
    if file.endswith(".py"):
        print("\n" + "="*60)
        print(file)
        print("="*60)

        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for n, line in enumerate(lines, start=1):
                for k in keywords:
                    if k.lower() in line.lower():
                        print(f"{n}: {line.strip()}")
                        break
        except Exception as e:
            print(e)
