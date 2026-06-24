import json
import uuid
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
MAPS = OUT / "id_maps"

OUT.mkdir(parents=True, exist_ok=True)
MAPS.mkdir(parents=True, exist_ok=True)

REQUIRED = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
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


def make_id_map(values, prefix: str) -> dict:
    unique_values = sorted({str(v) for v in values if pd.notna(v) and str(v).strip()})
    return {old: f"{prefix}-{i + 1:06d}" for i, old in enumerate(unique_values)}


def save_map(mapping: dict, filename: str, original_col: str, readable_col: str):
    df = pd.DataFrame([
        {original_col: old, readable_col: new}
        for old, new in mapping.items()
    ])
    df.to_csv(MAPS / filename, index=False)


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
    customers = read_csv("olist_customers_dataset.csv")
    sellers = read_csv("olist_sellers_dataset.csv")
    products = read_csv("olist_products_dataset.csv")
    translations = read_csv("product_category_name_translation.csv")

    order_map = make_id_map(orders["order_id"], "ORD")
    customer_map = make_id_map(customers["customer_id"], "CUST")
    customer_unique_map = make_id_map(customers["customer_unique_id"], "CU")
    seller_map = make_id_map(sellers["seller_id"], "SEL")
    product_map = make_id_map(products["product_id"], "PROD")
    review_map = make_id_map(reviews["review_id"], "REV")

    save_map(order_map, "order_id_map.csv", "original_order_id", "order_id")
    save_map(customer_map, "customer_id_map.csv", "original_customer_id", "customer_id")
    save_map(customer_unique_map, "customer_unique_id_map.csv", "original_customer_unique_id", "customer_unique_id")
    save_map(seller_map, "seller_id_map.csv", "original_seller_id", "seller_id")
    save_map(product_map, "product_id_map.csv", "original_product_id", "product_id")
    save_map(review_map, "review_id_map.csv", "original_review_id", "review_id")

    customers_enriched = customers.copy()
    customers_enriched["readable_customer_id"] = customers_enriched["customer_id"].map(customer_map)
    customers_enriched["readable_customer_unique_id"] = customers_enriched["customer_unique_id"].map(customer_unique_map)

    sellers_enriched = sellers.copy()
    sellers_enriched["readable_seller_id"] = sellers_enriched["seller_id"].map(seller_map)

    products_enriched = products.merge(translations, on="product_category_name", how="left")
    products_enriched["readable_product_id"] = products_enriched["product_id"].map(product_map)

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

    df = (
        orders
        .merge(payment_summary, on="order_id", how="left")
        .merge(item_summary, on="order_id", how="left")
        .merge(customers_enriched, on="customer_id", how="left")
        .merge(sellers_enriched, on="seller_id", how="left")
        .merge(products_enriched, on="product_id", how="left")
    )

    events = []

    for _, row in df.iterrows():
        readable_order_id = order_map.get(str(row["order_id"]))

        base = {
            "order_id": readable_order_id,
            "customer_id": row.get("readable_customer_id"),
            "customer_unique_id": row.get("readable_customer_unique_id"),
            "seller_id": row.get("readable_seller_id"),
            "product_id": row.get("readable_product_id"),

            "customer_city": row.get("customer_city"),
            "customer_state": row.get("customer_state"),
            "seller_city": row.get("seller_city"),
            "seller_state": row.get("seller_state"),

            "product_category": row.get("product_category_name_english") or row.get("product_category_name"),

            "original_order_id": row.get("order_id"),
            "original_customer_id": row.get("customer_id"),
            "original_seller_id": row.get("seller_id"),
            "original_product_id": row.get("product_id"),

            "original_order_status": row.get("order_status"),
            "estimated_delivery_date": row.get("order_estimated_delivery_date"),
            "total_price": row.get("total_price"),
            "total_freight": row.get("total_freight"),
            "item_count": row.get("item_count"),
        }

        add_event(events, row.get("order_purchase_timestamp"), "ORDER_CREATED", readable_order_id, base)

        add_event(events, row.get("order_approved_at"), "PAYMENT_APPROVED", readable_order_id, {
            **base,
            "payment_type": row.get("payment_type"),
            "payment_value": row.get("payment_value"),
            "payment_installments": row.get("payment_installments"),
        })

        add_event(events, row.get("shipping_limit_date"), "SELLER_SHIPPING_DEADLINE_SET", readable_order_id, base)
        add_event(events, row.get("order_delivered_carrier_date"), "SHIPPED_TO_CARRIER", readable_order_id, base)
        add_event(events, row.get("order_delivered_customer_date"), "DELIVERED_TO_CUSTOMER", readable_order_id, base)

        if row.get("order_status") in {"canceled", "unavailable"}:
            add_event(events, row.get("order_purchase_timestamp"), "ORDER_TERMINATED", readable_order_id, {
                **base,
                "terminal_status": row.get("order_status"),
            })

    for _, row in reviews.iterrows():
        readable_order_id = order_map.get(str(row["order_id"]))
        readable_review_id = review_map.get(str(row["review_id"]))

        add_event(events, row.get("review_creation_date"), "REVIEW_CREATED", readable_order_id, {
            "review_id": readable_review_id,
            "original_review_id": row.get("review_id"),
            "review_score": row.get("review_score"),
        })

        add_event(events, row.get("review_answer_timestamp"), "REVIEW_ANSWERED", readable_order_id, {
            "review_id": readable_review_id,
            "original_review_id": row.get("review_id"),
        })

    event_df = pd.DataFrame(events)
    event_df = event_df.sort_values(["event_time", "event_type", "order_id"]).reset_index(drop=True)

    out_path = OUT / "master_event_stream.csv"
    event_df.to_csv(out_path, index=False)

    print(f"Created {out_path}")
    print(f"Total events: {len(event_df):,}")
    print(f"ID maps saved to {MAPS}")
    print(event_df.head(10).to_string(index=False))
    print(event_df.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()