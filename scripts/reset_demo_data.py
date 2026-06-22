from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import psycopg2
import pika
from pymongo import MongoClient

from backend.app.core.config import settings


def reset_postgres():
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE
                live_events,
                orders,
                analytics_daily_kpi,
                analytics_seller_performance,
                analytics_region_delay
            RESTART IDENTITY CASCADE;
        """)

    conn.close()
    print("PostgreSQL demo data cleared.")


def reset_mongo():
    client = MongoClient(settings.mongo_uri)
    db = client[settings.mongo_db]

    db.live_events.delete_many({})
    db.order_events.delete_many({})

    client.close()
    print("MongoDB demo data cleared.")


def reset_rabbitmq():
    credentials = pika.PlainCredentials(
        settings.rabbitmq_user,
        settings.rabbitmq_password,
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=credentials,
        )
    )

    channel = connection.channel()

    for queue in ["postgres_order_queue", "mongo_timeline_queue"]:
        try:
            channel.queue_purge(queue=queue)
            print(f"RabbitMQ queue cleared: {queue}")
        except Exception as exc:
            print(f"Could not clear queue {queue}: {exc}")

    connection.close()


def main():
    reset_postgres()
    reset_mongo()
    reset_rabbitmq()
    print("Demo reset complete.")


if __name__ == "__main__":
    main()