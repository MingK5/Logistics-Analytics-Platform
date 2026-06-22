@echo off
call .venv\Scripts\activate
uvicorn backend.app.main:app --reload --port 8000
