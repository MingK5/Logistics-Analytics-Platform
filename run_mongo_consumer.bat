@echo off
call .venv\Scripts\activate
python -m backend.app.consumers.mongo_timeline_consumer
