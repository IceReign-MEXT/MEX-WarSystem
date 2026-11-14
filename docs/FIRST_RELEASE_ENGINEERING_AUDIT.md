# MEX-WarSystem — First Release Engineering Audit

**Review type:** Source inspection of the default branch  
**Status:** Not approved for paid public launch yet  
**Scope:** Configuration, persistence, Solana discovery, payment verification, alerts, deployment safety

## Executive summary

The repository contains useful building blocks, including a Telegram bot, SQLAlchemy models, a token screening module, and subscription/payment logic. However, these parts are not yet one consistently wired and verified service. This review is source-based; live database, Telegram, RPC, deployment and end-to-end tests have not been run.

## Launch blockers

### 1. Configuration mismatch
`.env.example` documents `TELEGRAM_BOT_TOKEN` and `ADMIN_TELEGRAM_ID`, but `main.py` reads `BOT_TOKEN` and `ADMIN_ID`. The application also reads `MASTER_WALLET`, `WEBHOOK_URL`, `BOT_USERNAME`, and `HELIUS_API_KEY`. `database.py` raises during import if `DATABASE_URL` is missing, while the main bot maintains a separate local JSON data store. Establish one documented configuration contract and validate required settings at startup.

### 2. Split persistence
`main.py` uses `bot_data.json`; `database.py`, `token_detector.py`, and `payment_monitor.py` use SQLAlchemy/PostgreSQL. Account status, payment state, detections and revenue can disagree. Consolidate to one durable database and add schema migrations.

### 3. Token discovery endpoint and scoring
`token_detector.py` calls `/latest/dex/pairs/{chain}`, which is not listed in the current DEX Screener API reference. The documented API includes search, pair-address lookup, and token-pairs-by-token-address endpoints. Confirm the correct discovery design and response schema before relying on it. Reference: https://docs.dexscreener.com/api/reference

The current score uses liquidity, FDV, volume relative to liquidity, and presence of social links. These are screening indicators only, not a security audit or rug-pull guarantee. Do not market scores as safe investments or promise returns.

### 4. Alerts are incomplete
`run_detection_loop()` contains a placeholder instead of subscriber alert delivery. The `known_tokens` cache is in memory and resets after restart. Persist detection identity, implement alert delivery, retries, delivery status, user preferences and opt-out.

### 5. Payment verification
Before granting access, verify the exact transaction signature, successful/finalized status, correct recipient, expected amount, payer/order association, chain/cluster, and replay protection. Enforce uniqueness/idempotency in the database. Never grant entitlement based only on an amount match.

### 6. Deployment safety
`deploy.sh` uses `git push origin main --force`. Remove force-push deployment; use normal CI/deployment integration and protect the default branch.

### 7. Diagnostics and claims
`verify_deployment.py` should return a non-zero exit status when checks fail and handle missing credentials/network errors without false success. Remove fabricated-looking success stories, scarcity counters, and unsupported claims such as “fully operational”, “sub-100ms”, “rug-proof”, or guaranteed opportunities.

## Recommended first paid product

Start with a narrower service: **public Solana wallet watchlists and verified Telegram activity alerts**. Users provide public addresses only. The service must not request seed phrases/private keys, custody funds, execute trades, or provide investment guarantees.

## Release acceptance checklist

- [ ] Single configuration contract and safe startup validation
- [ ] One durable database for users, subscriptions, payments, watchlists, detections and alert delivery
- [ ] Supported Solana data source with timeout, retry/backoff and rate-limit handling
- [ ] Idempotent payment verification and entitlement activation
- [ ] Telegram alert delivery with retries, delivery records and opt-out
- [ ] Unit tests for transaction parsing, duplicate events, payment verification and expiry
- [ ] CI passes and staging end-to-end tests pass
- [ ] Public claims match verified functionality

## Next engineering sequence

1. Map every startup path and reconcile environment variables.
2. Trace all payment and subscription handlers; write tests before changing payment logic.
3. Replace unsupported token discovery assumptions with documented API calls.
4. Complete persistent detection and Telegram alert delivery.
5. Remove unsafe deployment behavior and misleading marketing defaults.
6. Deploy to staging and test with non-production wallets and test payments.
