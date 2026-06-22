CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    seller_id TEXT,
    product_id TEXT,
    status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    shipping_limit_date TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    payment_type TEXT,
    payment_value NUMERIC,
    total_price NUMERIC,
    total_freight NUMERIC,
    review_score INTEGER,
    last_event_time TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS live_events (
    event_id TEXT PRIMARY KEY,
    event_time TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    order_id TEXT NOT NULL,
    payload_json JSONB,
    consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_daily_kpi (
    event_date DATE PRIMARY KEY,
    orders_created INTEGER DEFAULT 0,
    orders_delivered INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    avg_delivery_days NUMERIC,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_seller_performance (
    seller_id TEXT PRIMARY KEY,
    shipped_orders INTEGER DEFAULT 0,
    delivered_orders INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    avg_delivery_days NUMERIC,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_region_delay (
    customer_state TEXT PRIMARY KEY,
    delivered_orders INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    avg_delivery_days NUMERIC,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
