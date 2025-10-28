from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import asyncio
import json
from typing import Optional

from src.api.conway_runner import ConwayRunner

logger = logging.getLogger(__name__)

app = FastAPI(title="CyberMesh Conway Server")

runner: Optional[ConwayRunner] = None

# Mount static files
dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_path / "static")), name="static")

@app.get("/")
async def root():
    """Serve main HTML page"""
    html_path = dashboard_path / "index.html"
    if html_path.exists():
        with open(html_path, "r") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await runner.add_client(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle commands
            await runner.handle_command(websocket, message)
            
    except WebSocketDisconnect:
        runner.remove_client(websocket)

@app.on_event("startup")
async def startup():
    global runner
    runner = ConwayRunner(grid_size=8, tick_ms=500)
    # Start Conway loop in background
    asyncio.create_task(runner.run_loop())
    logger.info("Conway server started with 8x8 grid at 500ms ticks")

@app.on_event("shutdown")
async def shutdown():
    global runner
    if runner:
        runner.stop()
    logger.info("Conway server shut down...")
