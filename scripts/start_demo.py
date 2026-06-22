import subprocess
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000"],
    [sys.executable, "-m", "backend.app.consumers.postgres_consumer"],
    [sys.executable, "-m", "backend.app.consumers.mongo_timeline_consumer"],
    [sys.executable, "spark/jobs/delivery_analytics.py", "--loop", "--interval", "120"],
]

def main():
    processes = []

    try:
        for cmd in COMMANDS:
            print(f"Starting: {' '.join(cmd)}")
            p = subprocess.Popen(cmd, cwd=ROOT)
            processes.append(p)
            time.sleep(2)

        print("\nBackend + consumers + Spark analytics loop are running.")
        print("Press CTRL+C to stop all services.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping services...")

        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass

        time.sleep(3)

        for p in processes:
            if p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass

        print("Stopped.")


if __name__ == "__main__":
    main()