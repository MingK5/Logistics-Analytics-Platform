import json
from psycopg2.extras import Json
from backend.app.db.postgres import get_pg_connection
from backend.app.messaging.rabbitmq import get_connection, declare_topology
from backend.app.services.event_processor import parse_event, status_from_event


def upsert_order(cur, event: dict):
    payload = event.get("payload", {}) or {}
    event_type = event["event_type"]
    status = status_from_event(event_type)

    # Always store the raw consumed event first.
    cur.execute(
        """
        INSERT INTO live_events (event_id, event_time, event_type, order_id, payload_json)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (event["event_id"], event["event_time"], event_type, event["order_id"], Json(payload)),
    )

    # Create/update order current state.
    cur.execute(
        """
        INSERT INTO orders (
            order_id, customer_id, seller_id, product_id, status,
            order_purchase_timestamp, order_estimated_delivery_date,
            total_price, total_freight, last_event_time
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id = COALESCE(orders.customer_id, EXCLUDED.customer_id),
            seller_id = COALESCE(orders.seller_id, EXCLUDED.seller_id),
            product_id = COALESCE(orders.product_id, EXCLUDED.product_id),
            order_estimated_delivery_date = COALESCE(orders.order_estimated_delivery_date, EXCLUDED.order_estimated_delivery_date),
            total_price = COALESCE(orders.total_price, EXCLUDED.total_price),
            total_freight = COALESCE(orders.total_freight, EXCLUDED.total_freight),
            status = COALESCE(EXCLUDED.status, orders.status),
            last_event_time = EXCLUDED.last_event_time,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            event["order_id"], payload.get("customer_id"), payload.get("seller_id"), payload.get("product_id"),
            status or "EVENT_RECEIVED",
            event["event_time"] if event_type == "ORDER_CREATED" else None,
            payload.get("estimated_delivery_date"), payload.get("total_price"), payload.get("total_freight"),
            event["event_time"],
        ),
    )

    # Update event-specific timestamp fields.
    timestamp_fields = {
        "PAYMENT_APPROVED": "order_approved_at",
        "SELLER_SHIPPING_DEADLINE_SET": "shipping_limit_date",
        "SHIPPED_TO_CARRIER": "order_delivered_carrier_date",
        "DELIVERED_TO_CUSTOMER": "order_delivered_customer_date",
    }
    if event_type in timestamp_fields:
        cur.execute(f"UPDATE orders SET {timestamp_fields[event_type]} = %s WHERE order_id = %s", (event["event_time"], event["order_id"]))

    if event_type == "PAYMENT_APPROVED":
        cur.execute(
            "UPDATE orders SET payment_type = %s, payment_value = %s WHERE order_id = %s",
            (payload.get("payment_type"), payload.get("payment_value"), event["order_id"]),
        )

    if event_type == "REVIEW_CREATED":
        cur.execute(
            "UPDATE orders SET review_score = %s WHERE order_id = %s",
            (payload.get("review_score"), event["order_id"]),
        )


def callback(ch, method, properties, body):
    event = parse_event(body)
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                upsert_order(cur, event)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[Postgres] {event['event_time']} {event['event_type']} {event['order_id']}")
    except Exception as exc:
        conn.rollback()
        print(f"[Postgres ERROR] {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        conn.close()


def main():
    connection = get_connection()
    channel = connection.channel()
    declare_topology(channel)
    channel.basic_qos(prefetch_count=20)
    channel.basic_consume(queue="postgres_order_queue", on_message_callback=callback)
    print("PostgreSQL consumer started.")
    channel.start_consuming()


if __name__ == "__main__":
    main()
