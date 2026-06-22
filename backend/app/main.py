from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.dashboard import router as dashboard_router

app = FastAPI(title="Event-Driven Logistics Analytics Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "app": "Event-Driven Logistics Analytics Platform",
        "status": "running",
        "docs": "/docs",
        "dashboard_api": "/api/dashboard"
    }

app.include_router(dashboard_router)
