from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv

from app.routes.automation_route import router as automation_router
from app.routes.dashboard_route import router as dashboard_router
from app.routes.runner_route import router as runner_router

# Load environment variables
load_dotenv()

app = FastAPI(title="UiPath Automation Server")

@app.on_event("startup")
async def startup_event():
    from app.controller.unit_controller import register_unit
    await register_unit()

# Include the routes
app.include_router(automation_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(runner_router, prefix="/api/v1")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"message": "Server is running", "env": os.getenv("ENV", "unknown")}

# Mount assets directory
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the frontend SPA for any undefined route."""
    # Prevent API 404s from returning HTML
    if full_path.startswith("api"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse("frontend/dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=2026, reload=True)
