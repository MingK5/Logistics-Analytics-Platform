import json
from datetime import datetime


def parse_event(raw_body: bytes) -> dict:
    event = json.loads(raw_body.decode("utf-8"))
    if isinstance(event.get("payload_json"), str):
        event["payload"] = json.loads(event["payload_json"])
    else:
        event["payload"] = event.get("payload_json", {})
    return event


def status_from_event(event_type: str) -> str | None:
    return {
        "ORDER_CREATED": "CREATED",
        "PAYMENT_APPROVED": "APPROVED",
        "SELLER_SHIPPING_DEADLINE_SET": "SELLER_DEADLINE_SET",
        "SHIPPED_TO_CARRIER": "SHIPPED",
        "DELIVERED_TO_CUSTOMER": "DELIVERED",
        "ORDER_TERMINATED": "TERMINATED",
    }.get(event_type)


def event_time(event: dict) -> str:
    return str(event["event_time"])
