from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import asyncio
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
    """WebSocket endpoint for Conway grid updates"""
    await websocket.accept()
    await runner.add_client(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            # Handle client commands
            if data == "reset":
                runner.grid.grid.fill(0)
                runner.grid.seed_glider(r_offset=1, c_offset=1)
                await runner.send_full_state(websocket)
            elif data == "stop":
                runner.stop()
            elif data == "start":
                if not runner.running:
                    runner.running = True
                    asyncio.create_task(runner.run_loop())

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
