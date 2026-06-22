from pathlib import Path
import sys
import os
import time
import argparse

JAVA17_HOME = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"

if Path(JAVA17_HOME).exists():
    os.environ["JAVA_HOME"] = JAVA17_HOME
    os.environ["PATH"] = str(Path(JAVA17_HOME) / "bin") + os.pathsep + os.environ["PATH"]

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import pandas as pd
import psycopg2

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_timestamp, to_date, count, avg, when, datediff
)
from pyspark.sql.types import StructType, StructField, StringType

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.app.core.config import settings

OUT = ROOT / "spark" / "output"
OUT.mkdir(parents=True, exist_ok=True)


def get_pg_connection():
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def clear_analytics_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE
                analytics_daily_kpi,
                analytics_seller_performance
            RESTART IDENTITY CASCADE;
        """)


def run_once():
    print("Using JAVA_HOME:", os.environ.get("JAVA_HOME"))

    conn = get_pg_connection()
    conn.autocommit = True

    query = """
        SELECT
            order_id,
            seller_id,
            order_purchase_timestamp,
            order_delivered_customer_date,
            order_estimated_delivery_date
        FROM orders;
    """

    orders_pd = pd.read_sql_query(query, conn)

    if orders_pd.empty:
        clear_analytics_tables(conn)
        pd.DataFrame().to_csv(OUT / "daily_kpi.csv", index=False)
        pd.DataFrame().to_csv(OUT / "seller_performance.csv", index=False)
        pd.DataFrame().to_csv(OUT / "order_delivery_metrics.csv", index=False)
        conn.close()
        print("No orders found. Analytics tables cleared.")
        return

    spark = (
        SparkSession.builder
        .appName("LogisticsDeliveryAnalyticsFromPostgres")
        .master("local[*]")
        .getOrCreate()
    )

    orders_pd = orders_pd.fillna("").astype(str)

    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("seller_id", StringType(), True),
        StructField("order_purchase_timestamp", StringType(), True),
        StructField("order_delivered_customer_date", StringType(), True),
        StructField("order_estimated_delivery_date", StringType(), True),
    ])

    df = spark.createDataFrame(orders_pd, schema=schema)

    df = (
        df
        .withColumn("created_ts", to_timestamp(col("order_purchase_timestamp")))
        .withColumn("delivered_ts", to_timestamp(col("order_delivered_customer_date")))
        .withColumn("estimated_ts", to_timestamp(col("order_estimated_delivery_date")))
        .withColumn("created_date", to_date(col("created_ts")))
        .withColumn("delivered_date", to_date(col("delivered_ts")))
        .withColumn("delivery_days", datediff(col("delivered_ts"), col("created_ts")))
        .withColumn(
            "is_late",
            when(
                col("estimated_ts").isNotNull()
                & col("delivered_ts").isNotNull()
                & (col("delivered_ts") > col("estimated_ts")),
                1
            ).otherwise(0)
        )
    )

    daily_created = (
        df.groupBy("created_date")
        .agg(count("order_id").alias("orders_created"))
        .withColumnRenamed("created_date", "event_date")
    )

    daily_delivered = (
        df.filter(col("delivered_ts").isNotNull())
        .groupBy("delivered_date")
        .agg(
            count("order_id").alias("orders_delivered"),
            count(when(col("is_late") == 1, True)).alias("late_deliveries")
        )
        .withColumnRenamed("delivered_date", "event_date")
    )

    daily = (
        daily_created
        .join(daily_delivered, "event_date", "full")
        .fillna(0)
        .filter(col("event_date").isNotNull())
        .orderBy(col("event_date").desc())
    )

    delivered_orders = df.filter(col("delivered_ts").isNotNull())

    seller = (
        delivered_orders
        .filter(col("seller_id").isNotNull())
        .groupBy("seller_id")
        .agg(
            count("order_id").alias("delivered_orders"),
            count(when(col("is_late") == 1, True)).alias("late_deliveries"),
            avg("delivery_days").alias("avg_delivery_days"),
        )
        .orderBy(col("late_deliveries").desc(), col("delivered_orders").desc())
    )

    order_delivery = delivered_orders.select(
        "order_id",
        "seller_id",
        "created_ts",
        "delivered_ts",
        "estimated_ts",
        "delivery_days",
        "is_late",
    )

    daily_pd = daily.toPandas()
    print("Daily rows:", len(daily_pd))
    print(daily_pd.head())
    seller_pd = seller.toPandas()
    order_delivery_pd = order_delivery.toPandas()

    daily_pd.to_csv(OUT / "daily_kpi.csv", index=False)
    seller_pd.to_csv(OUT / "seller_performance.csv", index=False)
    order_delivery_pd.to_csv(OUT / "order_delivery_metrics.csv", index=False)

    clear_analytics_tables(conn)

    with conn.cursor() as cur:
        for _, r in daily_pd.iterrows():
            cur.execute(
                """
                INSERT INTO analytics_daily_kpi
                    (event_date, orders_created, orders_delivered, late_deliveries)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    r["event_date"],
                    int(r["orders_created"]),
                    int(r["orders_delivered"]),
                    int(r["late_deliveries"]),
                ),
            )

        for _, r in seller_pd.head(500).iterrows():
            cur.execute(
                """
                INSERT INTO analytics_seller_performance
                    (seller_id, delivered_orders, late_deliveries, avg_delivery_days)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    r["seller_id"],
                    int(r["delivered_orders"]),
                    int(r["late_deliveries"]),
                    float(r["avg_delivery_days"]) if pd.notna(r["avg_delivery_days"]) else 0.0,
                ),
            )

    conn.close()
    spark.stop()

    print(f"Spark analytics refreshed from PostgreSQL. Output written to {OUT}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=120)
    args = parser.parse_args()

    if args.loop:
        while True:
            run_once()
            time.sleep(args.interval)
    else:
        run_once()


if __name__ == "__main__":
    main()