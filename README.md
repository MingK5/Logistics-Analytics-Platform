# Event-Driven Logistics Analytics Platform

A portfolio-grade software and data engineering project built using the Olist Brazilian E-Commerce dataset (Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

The platform converts historical e-commerce records into a replayable event stream and simulates a real-time logistics environment using RabbitMQ, PostgreSQL, MongoDB, FastAPI, Angular, and Spark.

## Architecture

```text
Olist CSV Dataset
        │
        ▼
master_event_stream.csv
        │
        ▼
RabbitMQ Exchange
        │
 ┌──────┴──────┐
 ▼             ▼
PostgreSQL   MongoDB
Consumer     Consumer
 ▼             ▼
Operational   Event Timeline
Database      Store
       │
       ▼
Spark Analytics
       │
       ▼
Analytics Tables (PostgreSQL)
       │
       ▼
FastAPI REST API
       │
       ▼
Angular Dashboard
```

This project demonstrates:

* Event-driven architecture
* Message queues (RabbitMQ)
* Relational databases (PostgreSQL)
* Document databases (MongoDB)
* FastAPI backend development
* Angular frontend development
* Spark batch analytics
* Real-time event replay and monitoring

No machine learning is used.

---

# Tech Stack

### Backend

* FastAPI
* Python
* RabbitMQ
* PostgreSQL
* MongoDB
* Apache Spark

### Frontend

* Angular
* TypeScript

### Infrastructure

* Docker Compose

---

# 1. Setup

Install:

* Docker Desktop
* Python 3.11+
* Node.js 20+
* Angular CLI

```bash
npm install -g @angular/cli
```

---

# 2. Add Dataset

Copy Olist CSV files into:

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

---

# 3. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

---

# 4. Build Event Stream

```bash
python scripts/build_master_event_stream.py
```

Output:

```text
data/processed/master_event_stream.csv
```

The stream is globally sorted by event timestamp.

---

# 5. Start Infrastructure

```bash
docker compose up -d
```

RabbitMQ UI:

```text
http://localhost:15672
username: guest
password: guest
```

---

# 6. Initialize PostgreSQL

```bash
python scripts/init_db.py
```

---

# 7. Reset Demo Data (Optional)

Before starting a fresh replay:

```bash
python scripts/reset_demo_data.py
```

This clears:

* PostgreSQL operational tables
* PostgreSQL analytics tables
* MongoDB event collections

This ensures replay results are reproducible.

---

# 8. Start Backend Services

```bash
python scripts/start_demo.py
```

This launches:

* FastAPI API
* PostgreSQL consumer
* MongoDB consumer

API Documentation:

```text
http://localhost:8000/docs
```

---

# 9. Start Spark Analytics

Run analytics once:

```bash
python spark/jobs/delivery_analytics.py
```

Or continuously refresh analytics every 2 minutes:

```bash
python spark/jobs/delivery_analytics.py --loop
```

Spark reads processed order data from PostgreSQL and updates:

```text
analytics_daily_kpi
analytics_seller_performance
```

as well as:

```text
spark/output/
```

---

# 10. Start Event Replay

Open a new terminal:

```bash
python -m backend.app.producers.replay_producer --delay 2 --batch-size 1
```

Faster replay:

```bash
python -m backend.app.producers.replay_producer --delay 2 --batch-size 50
```

Events will flow through:

```text
RabbitMQ
 → PostgreSQL Consumer
 → MongoDB Consumer
 → FastAPI APIs
 → Angular Dashboard
```

---

# 11. Start Angular Frontend

```bash
cd frontend

npm install
npm start
```

Open:

```text
http://localhost:4200
```

---

# Dashboard Features

### Manager Dashboard

* Total Orders
* Delivered Orders
* Late Deliveries
* Average Delivery Days
* Daily KPI Table

### Live Event Feed

Real-time event stream from MongoDB.

### Order Tracking

Order-level shipment history and status progression.

### Seller Performance

Spark-generated analytics including:

* Delivered Orders
* Late Deliveries
* Average Delivery Days

---

# Project Story

I built an event-driven logistics analytics platform that converts historical e-commerce transactions into a replayable logistics event stream.

Events are published through RabbitMQ, processed by PostgreSQL and MongoDB consumers, analyzed using Apache Spark, exposed through FastAPI APIs, and visualized through an Angular dashboard.

The project demonstrates modern software engineering concepts including event-driven systems, messaging infrastructure, operational and analytical data stores, API development, frontend dashboards, and large-scale data processing.
