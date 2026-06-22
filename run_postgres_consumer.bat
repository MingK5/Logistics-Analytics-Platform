@echo off
call .venv\Scripts\activate
python -m backend.app.consumers.postgres_consumer
