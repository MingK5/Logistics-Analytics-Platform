from fastapi import APIRouter, HTTPException
from backend.app.db.postgres import get_pg_connection
from backend.app.db.mongo import order_events, live_events

router = APIRouter(prefix="/api", tags=["dashboard"])


def fetch_all(query: str, params: tuple = ()): 
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()): 
    rows = fetch_all(query, params)
    return rows[0] if rows else None


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/events/live")
def get_live_events(limit: int = 50):
    docs = list(live_events.find({}, {"_id": 0}).sort("event_time", -1).limit(limit))
    return docs


@router.get("/orders/recent")
def get_recent_orders(limit: int = 50):
    return fetch_all(
        """
        SELECT order_id, customer_id, seller_id, status, last_event_time, payment_value, review_score
        FROM orders
        ORDER BY last_event_time DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )


@router.get("/orders/{order_id}")
def get_order(order_id: str):
    order = fetch_one("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    timeline = order_events.find_one({"order_id": order_id}, {"_id": 0}) or {"order_id": order_id, "events": []}
    return {"order": order, "timeline": timeline}


@router.get("/kpis/summary")
def get_summary():
    return fetch_one(
        """
        SELECT
            COUNT(*) AS total_orders,
            COUNT(*) FILTER (WHERE status = 'DELIVERED') AS delivered_orders,
            COUNT(*) FILTER (WHERE status = 'SHIPPED') AS shipped_orders,
            COUNT(*) FILTER (WHERE status = 'APPROVED') AS approved_orders,
            COUNT(*) FILTER (WHERE status = 'CREATED') AS created_orders,
            AVG(EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp))/86400.0)
                FILTER (WHERE order_delivered_customer_date IS NOT NULL AND order_purchase_timestamp IS NOT NULL) AS avg_delivery_days,
            COUNT(*) FILTER (
                WHERE order_delivered_customer_date IS NOT NULL
                AND order_estimated_delivery_date IS NOT NULL
                AND order_delivered_customer_date > order_estimated_delivery_date
            ) AS late_deliveries
        FROM orders
        """
    )


@router.get("/kpis/daily")
def get_daily_kpi(limit: int = 30):
    return fetch_all("SELECT * FROM analytics_daily_kpi ORDER BY event_date DESC LIMIT %s", (limit,))


@router.get("/analytics/sellers")
def get_seller_performance(limit: int = 20):
    return fetch_all(
        """
        SELECT * FROM analytics_seller_performance
        ORDER BY late_deliveries DESC, delivered_orders DESC
        LIMIT %s
        """,
        (limit,),
    )
