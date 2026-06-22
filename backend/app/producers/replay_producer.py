import argparse
import time
from pathlib import Path
import pandas as pd
from backend.app.messaging.rabbitmq import get_connection, declare_topology, publish_event

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STREAM = ROOT / "data" / "processed" / "master_event_stream.csv"


def main():
    parser = argparse.ArgumentParser(description="Replay historical Olist events into RabbitMQ.")
    parser.add_argument("--stream", default=str(DEFAULT_STREAM))
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between batches.")
    parser.add_argument("--batch-size", type=int, default=1, help="Events per batch.")
    parser.add_argument("--limit", type=int, default=0, help="Limit events for testing. 0 means all.")
    args = parser.parse_args()

    stream_path = Path(args.stream)
    if not stream_path.exists():
        raise FileNotFoundError(f"Missing stream file: {stream_path}. Run scripts/build_master_event_stream.py first.")

    df = pd.read_csv(stream_path)
    df = df.sort_values("event_time")
    if args.limit > 0:
        df = df.head(args.limit)

    connection = get_connection()
    channel = connection.channel()
    declare_topology(channel)

    records = df.to_dict(orient="records")
    print(f"Publishing {len(records):,} events from {stream_path}")
    print(f"Batch size: {args.batch_size}, delay: {args.delay}s")

    for i in range(0, len(records), args.batch_size):
        batch = records[i:i + args.batch_size]
        for event in batch:
            publish_event(channel, event)
        print(f"Published {min(i + args.batch_size, len(records)):,}/{len(records):,} | last event time: {batch[-1]['event_time']}")
        time.sleep(args.delay)

    connection.close()
    print("Replay complete.")


if __name__ == "__main__":
    main()
