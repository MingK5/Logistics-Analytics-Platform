import json
import uuid
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

REQUIRED = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
]


def read_csv(name: str) -> pd.DataFrame:
    path = RAW / name
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Copy Olist CSV files into data/raw first.")
    return pd.read_csv(path)


def clean_value(v):
    if pd.isna(v):
        return None
    return v


def clean_payload(d: dict) -> dict:
    return {k: clean_value(v) for k, v in d.items()}


def add_event(events, event_time, event_type, order_id, payload):
    if pd.isna(event_time) or event_time == "":
        return
    parsed_time = pd.to_datetime(event_time, errors="coerce")
    if pd.isna(parsed_time):
        return
    events.append({
        "event_id": str(uuid.uuid4()),
        "event_time": parsed_time,
        "event_type": event_type,
        "order_id": order_id,
        "payload_json": json.dumps(clean_payload(payload), ensure_ascii=False, default=str),
    })


def main():
    for name in REQUIRED:
        if not (RAW / name).exists():
            raise FileNotFoundError(f"Missing required file: {RAW / name}")

    orders = read_csv("olist_orders_dataset.csv")
    items = read_csv("olist_order_items_dataset.csv")
    payments = read_csv("olist_order_payments_dataset.csv")
    reviews = read_csv("olist_order_reviews_dataset.csv")

    payment_summary = (
        payments.groupby("order_id")
        .agg(
            payment_value=("payment_value", "sum"),
            payment_type=("payment_type", lambda x: ",".join(sorted(set(x.astype(str))))),
            payment_installments=("payment_installments", "max"),
        )
        .reset_index()
    )

    item_summary = (
        items.groupby("order_id")
        .agg(
            seller_id=("seller_id", "first"),
            product_id=("product_id", "first"),
            shipping_limit_date=("shipping_limit_date", "min"),
            item_count=("order_item_id", "count"),
            total_price=("price", "sum"),
            total_freight=("freight_value", "sum"),
        )
        .reset_index()
    )

    df = orders.merge(payment_summary, on="order_id", how="left").merge(item_summary, on="order_id", how="left")

    events = []

    for _, row in df.iterrows():
        base = {
            "customer_id": row.get("customer_id"),
            "seller_id": row.get("seller_id"),
            "product_id": row.get("product_id"),
            "original_order_status": row.get("order_status"),
            "estimated_delivery_date": row.get("order_estimated_delivery_date"),
            "total_price": row.get("total_price"),
            "total_freight": row.get("total_freight"),
        }

        add_event(events, row.get("order_purchase_timestamp"), "ORDER_CREATED", row["order_id"], base)
        add_event(events, row.get("order_approved_at"), "PAYMENT_APPROVED", row["order_id"], {
            **base,
            "payment_type": row.get("payment_type"),
            "payment_value": row.get("payment_value"),
            "payment_installments": row.get("payment_installments"),
        })
        add_event(events, row.get("shipping_limit_date"), "SELLER_SHIPPING_DEADLINE_SET", row["order_id"], base)
        add_event(events, row.get("order_delivered_carrier_date"), "SHIPPED_TO_CARRIER", row["order_id"], base)
        add_event(events, row.get("order_delivered_customer_date"), "DELIVERED_TO_CUSTOMER", row["order_id"], base)

        # If an order never reaches delivery/approval, still expose terminal business status.
        if row.get("order_status") in {"canceled", "unavailable"}:
            add_event(events, row.get("order_purchase_timestamp"), "ORDER_TERMINATED", row["order_id"], {
                **base,
                "terminal_status": row.get("order_status"),
            })

    for _, row in reviews.iterrows():
        add_event(events, row.get("review_creation_date"), "REVIEW_CREATED", row["order_id"], {
            "review_id": row.get("review_id"),
            "review_score": row.get("review_score"),
        })
        add_event(events, row.get("review_answer_timestamp"), "REVIEW_ANSWERED", row["order_id"], {
            "review_id": row.get("review_id"),
        })

    event_df = pd.DataFrame(events)
    event_df = event_df.sort_values(["event_time", "event_type", "order_id"]).reset_index(drop=True)

    out_path = OUT / "master_event_stream.csv"
    event_df.to_csv(out_path, index=False)

    print(f"Created {out_path}")
    print(f"Total events: {len(event_df):,}")
    print(event_df.head(10).to_string(index=False))
    print(event_df.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
