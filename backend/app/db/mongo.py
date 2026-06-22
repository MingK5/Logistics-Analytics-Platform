from pymongo import MongoClient, DESCENDING
from backend.app.core.config import settings

_client = MongoClient(settings.mongo_uri)
db = _client[settings.mongo_db]
order_events = db["order_events"]
live_events = db["live_events"]

order_events.create_index("order_id", unique=True)
live_events.create_index([("event_time", DESCENDING)])
live_events.create_index("order_id")
