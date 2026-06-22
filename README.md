# Event-Driven Logistics Analytics Platform

A portfolio-grade software/data engineering project using the Olist Brazilian E-Commerce dataset.

The system replays historical e-commerce timestamps as live shipment events:

```text
CSV raw data -> master_event_stream.csv -> RabbitMQ -> consumers -> PostgreSQL + MongoDB -> FastAPI -> Angular
                                                             |
                                                             -> Spark batch analytics -> PostgreSQL KPI tables
```

No NLP. No ML. This project demonstrates event-driven architecture, message queues, relational + document databases, API design, Angular/TypeScript frontend, and Spark analytics.

## Tech Stack

- Angular + TypeScript: dashboard frontend
- FastAPI: backend REST API
- RabbitMQ: event messaging
- PostgreSQL: operational database and analytics tables
- MongoDB: event timelines and live event history
- Spark: batch analytics over processed event stream
- Docker Compose: local infrastructure

## 1. Setup

Install locally:

- Docker Desktop
- Python 3.11+
- Node.js 20+
- Angular CLI: `npm install -g @angular/cli`

## 2. Add Olist CSV files

Copy the Kaggle CSV files into:

```text
data/raw/
```

Required files:

```text
olist_orders_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_customers_dataset.csv
olist_sellers_dataset.csv
olist_products_dataset.csv
olist_geolocation_dataset.csv
product_category_name_translation.csv
```

## 3. Create Python environment

```bash
cd logistics-analytics-platform
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## 4. Build master event stream

```bash
python scripts/build_master_event_stream.py
```

This generates:

```text
data/processed/master_event_stream.csv
```

The stream is sorted globally by `event_time`, not grouped by order ID.

## 5. Start infrastructure

```bash
docker compose up -d
```

RabbitMQ UI:

```text
http://localhost:15672
username: guest
password: guest
```

## 6. Initialize PostgreSQL tables

```bash
python scripts/init_db.py
```

## 7. Start backend API

```bash
uvicorn backend.app.main:app --reload --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

## 8. Start consumers

Open two terminals:

```bash
python -m backend.app.consumers.postgres_consumer
```

```bash
python -m backend.app.consumers.mongo_timeline_consumer
```

## 9. Start event replay producer

```bash
python -m backend.app.producers.replay_producer --delay 2 --batch-size 1
```

For faster demo:

```bash
python -m backend.app.producers.replay_producer --delay 2 --batch-size 50
```

## Run before a fresh replay:
python scripts/reset_demo_data.py
Then start consumers and producer again.

## Then run:
python scripts/start_demo.py

This starts:
FastAPI
PostgreSQL consumer
MongoDB consumer
in one terminal.

## Then use another terminal only for replay:
python -m backend.app.producers.replay_producer --delay 2 --batch-size 1


## 10. Run Spark analytics

```bash
python spark/jobs/delivery_analytics.py
```

This reads the master event stream and writes aggregated CSV files to:

```text
spark/output/
```

It also attempts to insert KPI results into PostgreSQL.


## 11. Start Angular frontend

```bash
cd frontend
npm install
npm start
```

Open:

```text
http://localhost:4200
```

## Project story

> I built an event-driven logistics analytics platform that converts historical e-commerce data into a replayable shipment event stream. Events are published into RabbitMQ, consumed into PostgreSQL for operational state, stored in MongoDB for shipment timelines, analyzed using Spark, and visualized through an Angular dashboard.

