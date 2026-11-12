# MEX WAR SYSTEM — ON-CHAIN INTELLIGENCE

Built by ICE REIGN SYSTEMS.

A Solana/Ethereum public-wallet watchlist and token-market research dashboard. This launch foundation includes a responsive web interface, public-address format checks, DexScreener market lookup, health endpoint, SQLite/PostgreSQL persistence and optional Paystack checkout with server-side verification.

## Honest launch status

This is a launch foundation, not a claim that every production feature is already live. Wallet addresses can be stored; continuous chain event ingestion, Telegram alert workers, authenticated customer accounts and complete subscription entitlement enforcement remain separate milestones. Do not sell those as active until implemented and tested.

No seed phrases or private keys are requested or stored. No transaction signing, automatic fund transfers or trading is provided. Market data is informational, not financial advice.

## Render deployment

Connect this repository to Render or deploy the included render.yaml blueprint. Create a managed PostgreSQL database and set DATABASE_URL to its internal URL. Set APP_BASE_URL to the HTTPS Render URL. Set a long random SECRET_KEY. Configure PAYSTACK_SECRET_KEY only after setting up your own Paystack account; begin with test mode. Configure plan prices in whole NGN naira; zero disables checkout. Set the Paystack webhook to https://YOUR-SERVICE.onrender.com/webhooks/paystack. Deploy and verify /health.

Build: pip install -r requirements.txt
Start: gunicorn app:app --workers 2 --threads 4 --timeout 90

## Local development

Copy .env.example to .env, fill local values, install requirements and run python app.py. Never upload .env, API keys, bot tokens, database passwords or payment secrets to GitHub. Rotate any secret that was ever committed.

## Payments

Checkout remains disabled until Paystack secret, HTTPS APP_BASE_URL and non-zero plan prices are configured. Payments are checked server-to-server for status, expected amount, reference and customer email. Test with Paystack test mode before real payments. Verified subscriptions are recorded, but login and protected feature gates must be completed before selling gated monitoring as finished.

## Before commercial launch

Add authenticated customer accounts, email verification, password reset and account-scoped watchlists; implement a separate chain-indexing worker and retry-safe Telegram notifications; add subscription middleware, renewals, cancellations, invoices and admin audit logs; add automated tests, rate limits, abuse protection, privacy policy and terms; test database persistence, webhook replay and payment failure paths.
