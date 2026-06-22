from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import psycopg2
from backend.app.core.config import settings

SQL_PATH = ROOT / "infra" / "postgres" / "init.sql"


def main():
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(SQL_PATH.read_text(encoding="utf-8"))
    conn.close()
    print("PostgreSQL tables initialized.")


if __name__ == "__main__":
    main()
