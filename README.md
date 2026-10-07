# Notification Dispatcher

[![CI](https://github.com/TkachukStanislav/notification-dispatcher/actions/workflows/ci.yml/badge.svg)](https://github.com/TkachukStanislav/notification-dispatcher/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-DLQ-FF6600)
![Redis](https://img.shields.io/badge/Redis-idempotency-DC382D)

**Reliable asynchronous notification delivery.** The API accepts a notification and responds
instantly; a background worker delivers it through a message queue with retries, duplicate
protection and a dead-letter queue — so a slow or failing provider never blocks clients and no
message is lost or sent twice.

## Architecture

```mermaid
flowchart LR
    C[Client] -->|POST /api/v1/notifications| API[FastAPI]
    API -->|status: pending| DB[(PostgreSQL)]
    API -->|publish| Q[[RabbitMQ<br/>notifications.queue]]
    Q --> W[Worker]
    Q -.->|invalid message| DLQ[[Dead-letter queue]]
    W -->|lock idempotency_key| R[(Redis)]
    W -->|send with retries| T[Telegram API<br/>mock]
    W -->|sent / failed + delivery_logs| DB
```

## Features

| | |
|---|---|
| **Async API** | FastAPI + SQLAlchemy 2.0 (asyncpg) with an explicit connection pool |
| **Message queue** | RabbitMQ with a direct exchange and a dead-letter queue for invalid messages |
| **Idempotency** | Unique key in PostgreSQL + atomic Redis `SET NX EX` lock in the worker |
| **Retries** | 3 attempts on 5xx / connection errors, exponential backoff with jitter |
| **Delivery history** | Every attempt stored in `delivery_logs` |
| **Health checks** | `/health/live` (process) and `/health/ready` (PostgreSQL + Redis, `503` on failure) |
| **Zero-downtime migrations** | Alembic indexes built `CONCURRENTLY` |
| **Tests** | Isolated per-test DB transactions, dependency overrides, HTTP mocking — no real network |
| **Docker** | Multi-stage image running as a non-root user |
| **CI** | GitHub Actions: lint, tests against PostgreSQL, Docker build |

**Stack:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · asyncpg · Alembic ·
RabbitMQ (aio-pika) · Redis · httpx · pytest · respx · ruff · Docker · GitHub Actions

## Key design decisions

- **Ack after processing, not on receive.** If the worker crashes mid-delivery, RabbitMQ
  redelivers the message instead of losing it (at-least-once delivery). The resulting risk of
  duplicates is handled by idempotency.
- **Idempotency on two levels.** A unique `idempotency_key` in PostgreSQL rejects repeated API
  requests; a Redis `SET NX EX` lock stops the worker from delivering a redelivered message twice.
  `NX` makes check-and-set a single atomic step, so two workers cannot both win.
- **Poison messages go to a DLQ.** Invalid payloads are rejected with `requeue=False` and routed to
  `notifications.dlq` by RabbitMQ, instead of being redelivered forever and blocking the queue.
- **Retry only what can succeed.** 5xx and connection errors are retried with
  `2^attempt + random jitter` seconds of delay; 4xx responses fail immediately, because repeating
  a bad request will not fix it. Jitter prevents all failed messages from retrying at once.
- **Bounded concurrency.** `prefetch_count=10` limits in-flight messages per worker, so a large
  backlog cannot exhaust database or Redis connections.
- **Indexes without locking writes.** Indexes are created in a separate migration with
  `CREATE INDEX CONCURRENTLY` inside Alembic's `autocommit_block()`.
- **Tests never touch real data or network.** Each test runs in a transaction that is rolled back;
  the DB session is swapped via `dependency_overrides`, RabbitMQ via `monkeypatch`, the Telegram
  API via respx.

## Known limitations & next steps

Honest list of what a production version would still need:

- **Transactional outbox.** The notification is committed before it is published; if RabbitMQ is
  down at that moment, the record stays `pending` with no message in the queue.
- **Lock is taken before sending.** If the worker crashes after acquiring the Redis lock, the
  redelivered message is treated as a duplicate until the lock expires (5 min).
- **Duplicate API requests return `500`.** Should return the existing notification or `409`.
- **Retries block a worker slot.** Delayed retries via a RabbitMQ delay queue would free it.
- **Rate limiting** towards the provider (e.g. a Redis token bucket) is not implemented.
- **Real Telegram Bot API** instead of the local mock.

## Running locally

1. Start PostgreSQL, Redis and RabbitMQ:
   ```bash
   docker compose up -d
   ```
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create `.env`:
   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=notification_db
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   REDIS_URL=redis://localhost:6379/0
   RABBITMQ_URL=amqp://guest:guest@localhost:5672/
   TELEGRAM_URL=http://localhost:9000/send
   ```
4. Apply migrations:
   ```bash
   alembic upgrade head
   ```
5. Run each process in its own terminal:
   ```bash
   uvicorn mock_telegram:app --port 9000      # mock Telegram API
   uvicorn app.main:app --reload              # API → http://localhost:8000/docs
   python -m app.workers.consumer             # worker
   ```

### Try it

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": 42, "message": "Your order has shipped", "idempotency_key": "order-123"}'
```

```json
{"id": 1, "status": "pending", "recipient_id": 42, "message": "Your order has shipped", "idempotency_key": "order-123", "created_at": "2026-10-07T12:00:00Z"}
```

The worker picks it up within a second and sets the status to `sent` (or `failed` after 3 attempts).

## Tests

```bash
pytest -v
```

Needs the PostgreSQL container with migrations applied; RabbitMQ and the Telegram API are mocked.

## Project structure

```
app/
├── api/            # endpoints (notifications, health) and dependencies
├── core/           # settings, database engine
├── models/         # Notification, DeliveryLog
├── schemas/        # Pydantic schemas
├── services/       # RabbitMQ broker, idempotency lock, HTTP sender
├── workers/        # queue consumer with retries
└── main.py         # FastAPI app and lifespan
alembic/            # migrations
tests/              # pytest suite
mock_telegram.py    # local stand-in for the Telegram API
```

## Docker

```bash
docker build -t notification-dispatcher .
```

The container reads the same environment variables as `.env`. Inside a container `localhost` is
the container itself, so point hosts to the services (e.g. `POSTGRES_HOST=host.docker.internal`
on Docker Desktop). The worker runs from the same image with `python -m app.workers.consumer`.
