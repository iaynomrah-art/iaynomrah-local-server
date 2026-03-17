from fastapi import FastAPI
import os
from dotenv import load_dotenv

from app.routes.automation_route import router as automation_router
from app.routes.dashboard_route import router as dashboard_router
from app.routes.runner_route import router as runner_router
from app.routes.trade_route import router as trade_router

# Load environment variables
load_dotenv()

app = FastAPI(title="UiPath Automation Server")

@app.on_event("startup")
async def startup_event():
    import asyncio
    from app.controller.unit_controller import register_unit
    # Run registration in the background so it doesn't block startup
    asyncio.create_task(register_unit())

# Include the routes
app.include_router(automation_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(runner_router, prefix="/api/v1")
app.include_router(trade_router, prefix="/api/v1")

@app.get("/")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Server is running", "env": os.getenv("ENV", "unknown")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
