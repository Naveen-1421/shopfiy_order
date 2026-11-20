# Shopify Order Automation — Flask API

## Flow
Shopify `orders/create` webhook → HMAC verification → PostgreSQL order + durable job → worker → OpenAI personalised copy → WhatsApp approved template.

## Local setup
1. Create PostgreSQL and copy `.env.example` to `.env`. Fill all secrets.
2. Install dependencies:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Start Flask API:
   ```bash
   python run.py
   ```
   API listens on `http://localhost:5000`.
4. In another terminal, start the worker:
   ```bash
   python -m app.worker
   ```
5. Expose the API through HTTPS and register Shopify webhook:
   `POST https://YOUR_DOMAIN/webhooks/shopify/orders-create`
   Subscribe to `orders/create`. Set the webhook signing secret in `.env`.

## WhatsApp template
Create and get approval for a WhatsApp Business template named `order_confirmation`, language `en`, with three body placeholders, e.g.:
`Hi {{1}}, we received order {{2}}. {{3}}`
The third parameter is the AI-generated personalised sentence. Business-initiated messages generally require an approved template outside the 24-hour customer-service window. Obtain and respect WhatsApp opt-in.

## Production hardening before launch
- Replace `db.create_all()` with Flask-Migrate/Alembic migrations.
- Use a secrets manager, HTTPS, least-privilege DB credentials, backups, structured logs and monitoring.
- Add stale `processing` job lease/recovery so jobs are recovered after worker crashes.
- Add WhatsApp status webhooks and store provider message IDs.
- Add explicit E.164 phone validation, consent/opt-out enforcement and data-retention controls.
- The webhook is idempotent at order persistence. External send timeouts can be ambiguous if Meta accepted a message before the connection failed; reconcile provider status before retrying to avoid duplicate sends.
- Use a managed queue (Celery/RQ + Redis/SQS) for larger workloads.
- Configure Shopify webhook subscription and validate expected shop/topic headers for multi-store deployments.
