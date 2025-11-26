from fastapi import FastAPI

from .routers import display


app = FastAPI(title="ESP32 MTA Display Backend")


@app.on_event("startup")
async def startup_event() -> None:
    # Minimal startup hook so we know the app booted.
    print("[esp32-mta-display] FastAPI backend starting up...")


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}


app.include_router(display.router, prefix="/display", tags=["display"])
