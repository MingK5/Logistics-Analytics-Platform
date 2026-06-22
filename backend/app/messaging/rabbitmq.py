import json
import pika
from backend.app.core.config import settings


def get_connection():
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
    params = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)


def declare_topology(channel):
    channel.exchange_declare(exchange=settings.rabbitmq_exchange, exchange_type="fanout", durable=True)
    for queue in ["postgres_order_queue", "mongo_timeline_queue"]:
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_bind(queue=queue, exchange=settings.rabbitmq_exchange)


def publish_event(channel, event: dict):
    body = json.dumps(event, ensure_ascii=False, default=str)
    channel.basic_publish(
        exchange=settings.rabbitmq_exchange,
        routing_key="",
        body=body.encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
    )
