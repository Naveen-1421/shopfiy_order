# Shopify Order Automation — Flask API

A Flask-based Shopify order automation system that processes Shopify webhooks, validates HMAC signatures, stores order information in PostgreSQL, generates AI-personalized customer messages using OpenAI, and delivers notifications through the WhatsApp Cloud API.

---

## 1. Project Overview

The system automates customer communication throughout the Shopify order lifecycle.

### Main Features

- Shopify webhook integration.
- HMAC signature verification.
- PostgreSQL database integration.
- Order creation and cancellation handling.
- Fulfillment and shipment tracking updates.
- Idempotent webhook processing.
- Durable notification job queue.
- Background worker for asynchronous processing.
- OpenAI-powered personalized messages.
- WhatsApp Cloud API integration.
- Notification retry and failure handling.
- Database schema management using Flask-Migrate.

---

## 2. System Architecture

```text
                   Shopify Store
                         |
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
        orders/create  orders/    fulfillments/
                       cancelled  create/update
             |           |           |
             +-----------+-----------+
                         |
                         v
                Flask Webhook API
                         |
                         v
                 HMAC Verification
                         |
                         v
                  Event Processing
                         |
                         v
                  PostgreSQL DB
                         |
              +----------+----------+
              |                     |
              v                     v
          Orders Table       Notification Jobs
                                    |
                                    v
                             Background Worker
                                    |
                           +--------+--------+
                           |                 |
                           v                 v
                       OpenAI API       WhatsApp API
                           |                 |
                           v                 v
                    Personalized       Customer
                       Message        Notification
```

---

## 3. Project Workflow

### Workflow 1: Order Creation

Shopify `orders/create` webhook:

1. Shopify sends an order creation event.
2. Flask receives the webhook request.
3. The application verifies the Shopify HMAC signature.
4. The order is checked for duplicate processing.
5. Order information is stored in PostgreSQL.
6. A notification job is created with a unique deduplication key.
7. The background worker retrieves the pending job.
8. OpenAI generates personalized customer communication.
9. WhatsApp Cloud API sends the approved order confirmation template.
10. The notification job is updated with its processing result.

### Workflow 2: Order Cancellation

Shopify `orders/cancelled` webhook:

1. Shopify sends an order cancellation event.
2. Flask verifies the HMAC signature.
3. The application identifies the existing order.
4. The order status is updated to `cancelled`.
5. The cancellation timestamp is stored.
6. A cancellation notification job is created.
7. The background worker processes the notification.
8. WhatsApp sends the cancellation notification.
9. The notification job status is updated.

### Workflow 3: Fulfillment and Shipment Updates

Shopify `fulfillments/create` and `fulfillments/update` webhooks:

1. Shopify sends a fulfillment event.
2. Flask verifies the HMAC signature.
3. The application identifies the associated order.
4. Fulfillment and tracking information is extracted.
5. The order's fulfillment status is updated.
6. Tracking company, tracking number, and tracking URL are stored in PostgreSQL.
7. A shipment notification job is created.
8. The background worker processes the notification.
9. WhatsApp sends the shipping update to the customer.
10. The notification job status is updated.

---

## 4. Technology Stack

| Technology         | Purpose                            |
| ------------------ | ---------------------------------- |
| Python             | Backend programming                |
| Flask              | REST API and webhook handling      |
| PostgreSQL         | Database                           |
| Flask-SQLAlchemy   | ORM                                |
| Flask-Migrate      | Database migrations                |
| Alembic            | Migration management               |
| OpenAI API         | AI-generated personalized messages |
| WhatsApp Cloud API | Customer notifications             |
| Requests           | External API communication         |
| Pytest             | Automated testing                  |
| Docker             | Application containerization       |
| Docker Compose     | Multi-container orchestration      |

---

## 5. Project Structure

```text
shopify-order-automation-flask/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── worker.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── shopify_webhook.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py
│       ├── whatsapp_service.py
│       └── notification_queue.py
│
├── migrations/
│   └── versions/
│
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py
└── README.md
```

---

## 6. Local Installation and Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- Git
- Shopify development store
- Meta Developer account
- OpenAI API key

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd shopify-order-automation-flask
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure PostgreSQL

Create a PostgreSQL database:

```sql
CREATE DATABASE shopify_automation;
```

### Step 5: Configure Environment Variables

Copy the example environment file:

Windows:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Configure the required values in `.env`.

```env
FLASK_ENV=development
SECRET_KEY=change_this_secret

DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/shopify_automation

SHOPIFY_WEBHOOK_SECRET=your_shopify_webhook_secret

OPENAI_API_KEY=your_openai_api_key

WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WHATSAPP_API_VERSION=v23.0
WHATSAPP_TEMPLATE_NAME=order_confirmation
WHATSAPP_TEMPLATE_LANGUAGE=en
```

Never commit `.env` or real credentials to GitHub.

### Step 6: Run Database Migrations

```bash
python -m flask --app run.py db upgrade
```

Check the migration revision:

```bash
python -m flask --app run.py db current
```

Generate a new migration after changing SQLAlchemy models:

```bash
python -m flask --app run.py db migrate -m "describe schema change"
```

Apply it:

```bash
python -m flask --app run.py db upgrade
```

### Step 7: Start Flask API

```bash
python run.py
```

API base URL:

```text
http://localhost:5000
```

### Step 8: Start Background Worker

Open a second terminal:

```bash
python -m app.worker
```

The worker processes pending notification jobs asynchronously.

---

## 7. Shopify Webhook Configuration

Register these Shopify webhook subscriptions:

| Shopify Event         | HTTP Method | Flask Endpoint                       |
| --------------------- | ----------- | ------------------------------------ |
| `orders/create`       | POST        | `/webhooks/shopify/orders-create`    |
| `orders/cancelled`    | POST        | `/webhooks/shopify/orders-cancelled` |
| `fulfillments/create` | POST        | `/webhooks/shopify/fulfillments`     |
| `fulfillments/update` | POST        | `/webhooks/shopify/fulfillments`     |

Webhook URL examples:

```text
https://YOUR_DOMAIN/webhooks/shopify/orders-create
```

```text
https://YOUR_DOMAIN/webhooks/shopify/orders-cancelled
```

```text
https://YOUR_DOMAIN/webhooks/shopify/fulfillments
```

Configure the webhook signing secret in `.env`.

### HMAC Verification

Every webhook request must be validated using:

- Raw HTTP request body.
- `X-Shopify-Hmac-Sha256` header.
- Shopify webhook signing secret.
- HMAC-SHA256 comparison.

Invalid signatures must return HTTP 401.

---

## 8. Sample cURL Requests

The following examples illustrate the three Flask endpoints.

Generate a valid HMAC for the exact JSON body before sending the request.

### 8.1 Order Creation

```bash
curl -X POST http://localhost:5000/webhooks/shopify/orders-create \
-H "Content-Type: application/json" \
-H "X-Shopify-Hmac-Sha256: GENERATED_HMAC" \
-d '{
  "id": 123456789,
  "name": "#1047",
  "currency": "INR",
  "total_price": "2499.00",
  "customer": {
    "first_name": "John",
    "phone": "+919876543210"
  },
  "line_items": [
    {
      "title": "Cotton Shirt",
      "quantity": 1,
      "price": "2499.00"
    }
  ]
}'
```

Expected behavior:

- HMAC verification.
- Order creation.
- Notification job creation.
- HTTP 202 Accepted.

### 8.2 Order Cancellation

```bash
curl -X POST http://localhost:5000/webhooks/shopify/orders-cancelled \
-H "Content-Type: application/json" \
-H "X-Shopify-Hmac-Sha256: GENERATED_HMAC" \
-d '{
  "id": 123456789,
  "cancel_reason": "Customer request"
}'
```

Expected behavior:

- HMAC verification.
- Existing order identification.
- Order status updated to `cancelled`.
- Cancellation notification job creation.
- HTTP 202 Accepted.

### 8.3 Fulfillment Creation or Update

```bash
curl -X POST http://localhost:5000/webhooks/shopify/fulfillments \
-H "Content-Type: application/json" \
-H "X-Shopify-Hmac-Sha256: GENERATED_HMAC" \
-d '{
  "id": 987654321,
  "order_id": 123456789,
  "status": "success",
  "tracking_company": "DHL",
  "tracking_number": "TRACK123",
  "tracking_url": "https://tracking.example.com/TRACK123"
}'
```

Expected behavior:

- HMAC verification.
- Order identification.
- Fulfillment and tracking information updated.
- Shipment notification job creation.
- HTTP 202 Accepted.

Note: These are example payloads. Use the exact fields required by the corresponding Flask route. For fulfillment events, Shopify's payload structure must be respected.

---

## 9. OpenAI Integration

OpenAI is used to generate personalized customer messages based on order information.

Example input:

```json
{
  "customer_name": "John",
  "order_number": "#1047",
  "currency": "INR",
  "total_price": "2499.00",
  "line_items": [
    {
      "title": "Cotton Shirt",
      "quantity": 1
    }
  ]
}
```

Example output:

```json
{
  "message": "Hi John! Thank you for ordering from us. Your order #1047 has been received. We appreciate your purchase!"
}
```

AI fallback behavior should provide a safe predefined message if the OpenAI API is unavailable.

Order notes and customer-supplied text must be treated as untrusted input to prevent prompt injection.

---

## 10. WhatsApp Cloud API Integration

WhatsApp Cloud API is used to deliver customer notifications.

Required configuration:

- WhatsApp access token.
- WhatsApp Phone Number ID.
- Graph API version.
- Approved WhatsApp message template.
- Customer WhatsApp opt-in.

Example approved template:

Template name: `order_confirmation`

Language: `en`

Template body:

```text
Hi {{1}}, we received order {{2}}. {{3}}
```

Parameters:

1. Customer name.
2. Order number.
3. AI-generated personalized message.

Business-initiated messages generally require an approved template outside the 24-hour customer-service window.

---

## 11. Database Design

### Orders Table

Stores Shopify order and fulfillment information.

| Column             | Purpose                   |
| ------------------ | ------------------------- |
| id                 | Internal order ID         |
| shopify_order_id   | Shopify order identifier  |
| order_number       | Shopify order number      |
| customer_name      | Customer name             |
| phone              | Customer phone            |
| currency           | Order currency            |
| total_price        | Order total               |
| line_items         | Order product information |
| status             | Order lifecycle status    |
| cancelled_at       | Cancellation timestamp    |
| fulfillment_status | Fulfillment state         |
| tracking_company   | Shipping company          |
| tracking_number    | Tracking number           |
| tracking_url       | Tracking link             |
| delivered_at       | Delivery timestamp        |
| created_at         | Order creation timestamp  |
| updated_at         | Last update timestamp     |

### Notification Jobs Table

Stores notification processing information.

| Column            | Purpose                                |
| ----------------- | -------------------------------------- |
| id                | Notification job ID                    |
| order_id          | Associated order                       |
| notification_type | Confirmation, cancellation or shipment |
| dedupe_key        | Unique notification identifier         |
| payload           | Notification data                      |
| channel           | WhatsApp                               |
| status            | Pending, processing, sent or failed    |
| attempts          | Retry count                            |
| next_attempt_at   | Next retry time                        |
| last_error        | Last error message                     |
| created_at        | Job creation timestamp                 |
| sent_at           | Successful delivery timestamp          |

---

## 12. Idempotency and Reliability

The system uses unique identifiers to prevent duplicate notification jobs.

Example:

```text
10:confirmation
10:cancelled
10:fulfillment:987654321:shipped
```

The unique deduplication key ensures that processing the same event again does not create another identical notification job.

The database-backed notification queue allows jobs to remain stored while the worker is unavailable.

Failed notifications should use exponential backoff and a configurable maximum retry count.

Jobs that exceed the retry limit should be moved to a dead-letter state for manual investigation.

External API timeouts may have ambiguous delivery outcomes. Reconcile provider message status before retrying to avoid duplicate customer messages.

---

## 13. Docker Setup

### Required Files

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`

### Start the Application

```bash
docker compose up --build
```

### Stop the Application

```bash
docker compose down
```

### View Logs

```bash
docker compose logs -f
```

### Run Database Migration

Use the actual Flask API service name defined in `docker-compose.yml`:

```bash
docker compose exec web python -m flask --app run.py db upgrade
```

The Docker Compose configuration should start:

1. Flask API.
2. PostgreSQL.
3. Background worker.

Ensure that the worker and API share the same database configuration.

---

## 14. Automated Testing

The project should include at least six automated tests.

| No. | Test                        | Expected Result                                             |
| --- | --------------------------- | ----------------------------------------------------------- |
| 1   | HMAC validation             | Valid signatures accepted; invalid signatures rejected      |
| 2   | Duplicate webhook handling  | Duplicate events do not create duplicate jobs               |
| 3   | State-machine transitions   | Valid transitions accepted; invalid transitions rejected    |
| 4   | AI fallback                 | Safe fallback message generated when OpenAI fails           |
| 5   | Prompt-injection protection | Malicious customer input cannot override business rules     |
| 6   | Retry and dead-letter       | Failed jobs retry and eventually move to dead-letter status |

### Run Tests

```bash
pytest -v
```

External API calls should be mocked during automated testing.

---

## 15. Security Considerations

- Validate every Shopify webhook HMAC signature.
- Never expose API keys or webhook secrets in source code.
- Use environment variables for credentials.
- Validate and sanitize webhook payloads.
- Use PostgreSQL parameterized queries through SQLAlchemy.
- Implement duplicate-event protection.
- Enforce WhatsApp customer opt-in and opt-out.
- Validate customer phone numbers using E.164 format.
- Apply appropriate access controls to administrative endpoints.
- Use HTTPS in production.
- Apply data-retention and privacy policies.

---

## 16. Production Hardening

Before production deployment:

- Replace `db.create_all()` with Flask-Migrate/Alembic migrations.
- Configure a secrets manager.
- Use HTTPS and least-privilege database credentials.
- Configure database backups and monitoring.
- Add stale `processing` job recovery after worker crashes.
- Add WhatsApp status webhooks and store provider message IDs.
- Implement explicit phone validation and consent checks.
- Add structured logging and request correlation IDs.
- Consider Celery/RQ with Redis or SQS for larger workloads.
- Handle out-of-order Shopify events.
- Reconcile ambiguous external API delivery outcomes before retries.

---

## 17. Current Implementation Status

| Component                 | Status                                       |
| ------------------------- | -------------------------------------------- |
| Flask API                 | Implemented                                  |
| Shopify webhook routes    | Registered                                   |
| HMAC validation           | Implemented; automated verification required |
| PostgreSQL integration    | Working                                      |
| Flask-Migrate             | Configured and migration applied             |
| Order creation            | HTTP 202 observed                            |
| Order cancellation        | HTTP 202 observed                            |
| Fulfillment route         | Registered                                   |
| Notification job creation | Verified in database                         |
| OpenAI integration        | Requires credential verification             |
| WhatsApp integration      | Requires token and template configuration    |
| Docker                    | Requires build and runtime verification      |
| Automated tests           | Requires execution and result verification   |

---

## 18. Conclusion

The Shopify Order Automation project provides a Flask-based backend for automating Shopify order events and customer communication.

It integrates Shopify Webhooks, PostgreSQL, OpenAI, and WhatsApp Cloud API to manage order creation, cancellation, fulfillment updates, and asynchronous notification processing.

The system uses HMAC authentication, database-backed notification jobs, idempotency, and migration management to improve security and reliability.

The remaining production work focuses on external API configuration, Docker validation, automated test execution, and enhanced retry and recovery mechanisms.
