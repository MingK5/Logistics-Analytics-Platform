from datetime import datetime, timezone
from backend.app.db.mongo import order_events, live_events
from backend.app.messaging.rabbitmq import get_connection, declare_topology
from backend.app.services.event_processor import parse_event


def callback(ch, method, properties, body):
    event = parse_event(body)
    event_doc = {
        "event_id": event["event_id"],
        "event_time": event["event_time"],
        "event_type": event["event_type"],
        "order_id": event["order_id"],
        "payload": event.get("payload", {}),
        "consumed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        live_events.insert_one(event_doc.copy())
        order_events.update_one(
            {"order_id": event["order_id"]},
            {
                "$setOnInsert": {"order_id": event["order_id"]},
                "$push": {"events": event_doc},
                "$set": {"last_event_time": event["event_time"], "last_event_type": event["event_type"]},
            },
            upsert=True,
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[Mongo] {event['event_time']} {event['event_type']} {event['order_id']}")
    except Exception as exc:
        print(f"[Mongo ERROR] {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    connection = get_connection()
    channel = connection.channel()
    declare_topology(channel)
    channel.basic_qos(prefetch_count=20)
    channel.basic_consume(queue="mongo_timeline_queue", on_message_callback=callback)
    print("MongoDB timeline consumer started.")
    channel.start_consuming()


if __name__ == "__main__":
    main()
