#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
REVENUE CALCULATOR - How much can you make?
═══════════════════════════════════════════════════════════════════════════
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Configuration
SAAS_MONTHLY = float(os.getenv("SAAS_MONTHLY_PRICE", 5.0))
YOUR_COMMISSION = 0.20  # 20%
SOL_PRICE_USD = 150  # Adjust based on market

def calculate_revenue():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           ICEGODS PLATFORM REVENUE CALCULATOR                    ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    scenarios = [
        {"name": "Conservative (10 admins)", "admins": 10},
        {"name": "Moderate (50 admins)", "admins": 50},
        {"name": "Growth (100 admins)", "admins": 100},
        {"name": "Viral (500 admins)", "admins": 500},
        {"name": "Dominance (1000 admins)", "admins": 1000},
    ]
    
    for scenario in scenarios:
        admins = scenario["admins"]
        
        # SaaS Revenue (20% of subscriptions)
        monthly_saas = admins * SAAS_MONTHLY * YOUR_COMMISSION
        yearly_saas = monthly_saas * 12
        
        # Client Bot Commission (estimate 20% of their revenue)
        avg_bots_per_admin = 2
        avg_subs_per_bot = 15
        avg_price_per_sub = 1.0  # SOL
        
        total_bot_revenue = admins * avg_bots_per_admin * avg_subs_per_bot * avg_price_per_sub
        your_bot_commission = total_bot_revenue * 0.2  # 20% of their 80%
        
        monthly_bot = your_bot_commission / 12  # Spread over year
        yearly_bot = your_bot_commission
        
        # Totals
        total_monthly = monthly_saas + monthly_bot
        total_yearly = yearly_saas + yearly_bot
        
        print(f"\n📊 {scenario['name']}")
        print("─" * 50)
        print(f"  SaaS Revenue:     {monthly_saas:.1f} SOL/month (${monthly_saas*SOL_PRICE_USD:.0f})")
        print(f"  Bot Commission:   {monthly_bot:.1f} SOL/month (${monthly_bot*SOL_PRICE_USD:.0f})")
        print(f"  ─────────────────────────────────────")
        print(f"  TOTAL MONTHLY:    {total_monthly:.1f} SOL (${total_monthly*SOL_PRICE_USD:.0f})")
        print(f"  TOTAL YEARLY:     {total_yearly:.1f} SOL (${total_yearly*SOL_PRICE_USD:.0f})")
        print(f"\n  💰 At {admins} admins, you make ${total_monthly*SOL_PRICE_USD:.0f}/month")
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    GROWTH STRATEGY                               ║
╚══════════════════════════════════════════════════════════════════╝

Month 1-2: Bootstrap (10 admins)
  • Deploy yourself, create 3 demo bots
  • Post success stories in 5 crypto groups daily
  • Expected: 10 admins × 5 SOL × 20% = 10 SOL/month

Month 3-4: Viral Loop (50 admins)  
  • Referral system kicks in
  • Cross-channel marketing active
  • Expected: 50 × 5 × 20% = 50 SOL/month + bot commissions

Month 5-6: Scale (100+ admins)
  • Partner with influencer channels
  • Airdrop partnerships (projects pay you for distribution)
  • Expected: 100+ SOL/month passive income

VIRAL MECHANICS BUILT IN:
✅ Referral rewards (3 days free per invite)
✅ Limited bot slots (scarcity drives action)
✅ Automatic group recruitment (welcomes new members)
✅ Payment reminders (reduces churn)
✅ Cross-channel marketing (constant exposure)

YOUR EDGE:
• Competitors charge $100+/month for SaaS
• You charge 5 SOL (~$750) but give 80% to devs
• Devs prefer crypto payments (tax advantages)
• Automatic airdrops attract projects to YOU
""")

if __name__ == "__main__":
    calculate_revenue()

