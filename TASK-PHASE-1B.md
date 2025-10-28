---
title: "Phase 1B: WebSocket Backend Implementation"
phase: "1B"
objective: "FastAPI WebSocket server with delta-only updates for real-time Conway visualization"
assigned_to: "coding_agent"
status: "ready_for_execution"
hardware: "128GB Strix Halo HP ZBook, Windows 11"
dependencies: ["Phase 1A complete", "FastAPI", "uvicorn", "websockets"]
estimated_duration: "1.5 days"
validation_gates: ["unit", "lint", "type", "physical_network"]
---

# Phase 1B: WebSocket Backend Implementation

## Objective

Implement FastAPI WebSocket server that integrates Phase 1A ConwayGrid, broadcasts delta-only updates at 500ms tick rate, and supports multiple concurrent client connections with physical network validation.

## Prerequisites

- ✅ Phase 1A complete (ConwayGrid validated at 11,186 steps/sec)
- FastAPI 0.104+
- uvicorn 0.24+
- websockets package
- Windows Firewall configured to allow port 8000

## Task Breakdown

### Task 1B-1: Implement FastAPI Server with WebSocket Endpoint

**File**: `src/api/conway_server.py`

**Requirements**:
- FastAPI app with WebSocket route at `/ws`
- Static file serving for frontend (dashboard/)
- Root route serves `dashboard/index.html`
- CORS configuration for local development
- Graceful shutdown handling

**Acceptance Criteria**:
- Server starts on `0.0.0.0:8000`
- `/ws` endpoint accepts WebSocket connections
- Root `/` serves HTML file
- Server shuts down cleanly on Ctrl+C

**Implementation Template**:
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

app = FastAPI(title="CyberMesh Conway Server")

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
    logger.info(f"Client connected: {websocket.client}")
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Handle client commands if needed
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")

@app.on_event("startup")
async def startup():
    logger.info("Conway server starting...")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Conway server shutting down...")
```

**Validation**:
```bash
# Start server
python -m uvicorn src.api.conway_server:app --host 0.0.0.0 --port 8000

# Verify in separate terminal
netstat -an | findstr :8000
# Should show LISTENING

# Test WebSocket connection (Python client)
pytest tests/phase_1b/test_server_startup.py -v
```

**Physical Evidence Required**:
- `netstat` output showing port 8000 LISTENING
- Server log showing startup message
- Screenshot of Task Manager showing uvicorn process

---

### Task 1B-2: Implement ConwayRunner with Delta Broadcasting

**File**: `src/api/conway_runner.py`

**Requirements**:
- ConwayRunner class managing ConwayGrid instance
- 500ms tick loop (2 ticks/second)
- Delta-only message format (JSON)
- Full state broadcast on client connect
- Thread-safe WebSocket set management
- Graceful handling of disconnections

**Implementation**:
```python
import asyncio
import time
import json
from typing import Set
from fastapi import WebSocket
from src.core.conway_grid import ConwayGrid, CellDelta
import logging

logger = logging.getLogger(__name__)

class ConwayRunner:
    """Manages Conway grid execution and WebSocket broadcasting"""
    
    def __init__(self, grid_size: int = 8, tick_ms: int = 500):
        self.grid = ConwayGrid(size=grid_size)
        self.tick_interval = tick_ms / 1000.0  # Convert to seconds
        self.running = False
        self.websockets: Set[WebSocket] = set()
        self.tick_count = 0
        
    async def add_client(self, websocket: WebSocket):
        """Add new client and send full state"""
        self.websockets.add(websocket)
        await self.send_full_state(websocket)
        logger.info(f"Client added, total: {len(self.websockets)}")
    
    def remove_client(self, websocket: WebSocket):
        """Remove disconnected client"""
        self.websockets.discard(websocket)
        logger.info(f"Client removed, total: {len(self.websockets)}")
    
    async def send_full_state(self, websocket: WebSocket):
        """Send complete grid state to single client"""
        state = self.grid.get_state().tolist()
        message = {
            "type": "full_state",
            "tick": self.tick_count,
            "grid": state,
            "size": self.grid.size
        }
        await websocket.send_json(message)
    
    async def broadcast_deltas(self, deltas: list[CellDelta]):
        """Broadcast delta updates to all clients"""
        if not self.websockets or not deltas:
            return
        
        message = {
            "type": "delta",
            "tick": self.tick_count,
            "deltas": [
                {"x": d.x, "y": d.y, "alive": d.alive}
                for d in deltas
            ]
        }
        
        # Calculate message size for monitoring
        msg_size = len(json.dumps(message))
        
        # Broadcast to all connected clients
        disconnected = set()
        for ws in self.websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(ws)
        
        # Clean up disconnected clients
        self.websockets -= disconnected
        
        return msg_size
    
    async def run_loop(self):
        """Main Conway loop at 500ms ticks"""
        self.running = True
        
        # Seed glider at startup
        self.grid.seed_glider(x=1, y=1)
        logger.info("Glider seeded at (1,1)")
        
        # Send initial state to any connected clients
        for ws in list(self.websockets):
            await self.send_full_state(ws)
        
        while self.running:
            tick_start = time.perf_counter()
            
            # Execute Conway step
            deltas = self.grid.step()
            self.tick_count += 1
            
            # Broadcast deltas if any clients connected
            if self.websockets:
                msg_size = await self.broadcast_deltas(deltas)
                if self.tick_count % 10 == 0:
                    logger.info(f"Tick {self.tick_count}: {len(deltas)} deltas, "
                              f"{msg_size} bytes, {len(self.websockets)} clients")
            
            # Sleep to maintain tick rate
            elapsed = time.perf_counter() - tick_start
            sleep_time = self.tick_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"Tick {self.tick_count} took {elapsed*1000:.1f}ms, "
                             f"exceeding {self.tick_interval*1000:.0f}ms target")
    
    def stop(self):
        """Stop the Conway loop"""
        self.running = False
        logger.info("Conway runner stopped")
```

**Validation**:
```bash
pytest tests/phase_1b/test_conway_runner.py -v
pytest tests/phase_1b/test_delta_broadcast.py -v
```

**Physical Evidence Required**:
- Log file showing tick messages every 500ms
- Message size measurements (<1KB per delta)
- Screenshot of server logs with tick counter

---

### Task 1B-3: Integrate ConwayRunner with FastAPI

**File**: `src/api/conway_server.py` (update)

**Requirements**:
- Initialize ConwayRunner on app startup
- Start Conway loop as background task
- Connect WebSocket clients to runner
- Handle client disconnections properly
- Stop runner on app shutdown

**Updated Implementation**:
```python
from src.api.conway_runner import ConwayRunner

runner: ConwayRunner = None

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
    logger.info("Conway server shut down")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await runner.add_client(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Handle client commands
            if data == "reset":
                runner.grid.grid.fill(0)
                runner.grid.seed_glider(1, 1)
                await runner.send_full_state(websocket)
            elif data == "stop":
                runner.stop()
            elif data == "start":
                if not runner.running:
                    runner.running = True
                    asyncio.create_task(runner.run_loop())
                    
    except WebSocketDisconnect:
        runner.remove_client(websocket)
```

**Validation**:
```bash
# Start server
python -m uvicorn src.api.conway_server:app --reload

# Run integration tests
pytest tests/phase_1b/test_integration.py -v
```

---

### Task 1B-4: Physical Network Validation Tests

**File**: `tests/phase_1b/test_network_physical.py`

**Requirements**:
- Test actual WebSocket connection from Python client
- Measure round-trip latency
- Verify message format and content
- Test multiple concurrent connections
- Measure bandwidth usage

**Physical Tests**:
```python
import pytest
import asyncio
import websockets
import json
import time
import psutil

@pytest.mark.asyncio
async def test_websocket_connection_physical():
    """Physical test: Actual WebSocket connection"""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Should receive full_state on connect
        message = await websocket.recv()
        data = json.loads(message)
        
        assert data["type"] == "full_state"
        assert "grid" in data
        assert data["size"] == 8
        assert len(data["grid"]) == 8
        assert len(data["grid"][0]) == 8

@pytest.mark.asyncio
async def test_delta_message_physical():
    """Physical test: Receive delta messages"""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Skip full_state
        await websocket.recv()
        
        # Wait for delta message
        message = await websocket.recv()
        data = json.loads(message)
        
        assert data["type"] == "delta"
        assert "deltas" in data
        assert isinstance(data["deltas"], list)
        
        # Verify message size
        msg_size = len(message)
        assert msg_size < 1024, f"Message size {msg_size} bytes, should be <1KB"

@pytest.mark.asyncio
async def test_latency_physical():
    """Physical test: Round-trip latency measurement"""
    uri = "ws://localhost:8000/ws"
    
    latencies = []
    
    async with websockets.connect(uri) as websocket:
        await websocket.recv()  # Skip full_state
        
        for _ in range(10):
            start = time.perf_counter()
            
            # Send ping
            await websocket.send("ping")
            
            # Wait for next message (could be delta or pong)
            message = await websocket.recv()
            
            elapsed = (time.perf_counter() - start) * 1000  # ms
            latencies.append(elapsed)
            
            await asyncio.sleep(0.5)
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    assert avg_latency < 50, f"Average latency {avg_latency:.1f}ms, should be <50ms"
    assert max_latency < 100, f"Max latency {max_latency:.1f}ms, should be <100ms"

@pytest.mark.asyncio
async def test_concurrent_connections_physical():
    """Physical test: Multiple clients simultaneously"""
    uri = "ws://localhost:8000/ws"
    
    async def client_task():
        async with websockets.connect(uri) as ws:
            # Receive full state
            await ws.recv()
            # Receive 5 delta messages
            for _ in range(5):
                await ws.recv()
    
    # Connect 5 clients concurrently
    tasks = [client_task() for _ in range(5)]
    await asyncio.gather(*tasks)
    
    # All clients should complete without errors

def test_server_memory_physical():
    """Physical test: Server memory usage"""
    # Find uvicorn process
    for proc in psutil.process_iter(['name', 'cmdline']):
        if 'python' in proc.info['name'].lower():
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'uvicorn' in cmdline and 'conway_server' in cmdline:
                mem_mb = proc.memory_info().rss / 1024 / 1024
                assert mem_mb < 100, f"Server using {mem_mb:.1f}MB, should be <100MB"
                return
    
    pytest.skip("Server process not found")
```

**Validation**:
```bash
# Start server in one terminal
python -m uvicorn src.api.conway_server:app

# Run tests in another terminal
pytest tests/phase_1b/test_network_physical.py -v -s
```

**Physical Evidence Required**:
- Network packet capture showing WebSocket frames
- Browser Developer Tools Network tab screenshot
- Task Manager showing server memory usage
- Performance log: `logs/phase_1b_network_validation.txt`

---

### Task 1B-5: Hardware Validation Script

**File**: `scripts/validate_phase_1b.py`

**Requirements**:
- Start server programmatically
- Connect Python WebSocket client
- Monitor network metrics for 30 seconds
- Measure latency, bandwidth, CPU usage
- Generate validation report

**Implementation**:
```python
import asyncio
import websockets
import json
import time
import psutil
import subprocess
import signal
import sys
from pathlib import Path

async def validate_phase_1b():
    """Physical hardware validation for Phase 1B"""
    
    print("=== Phase 1B Network Validation ===\n")
    
    # Start server
    print("Starting Conway server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", 
         "src.api.conway_server:app", 
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    await asyncio.sleep(3)
    
    # Get baseline metrics
    try:
        server_psutil = psutil.Process(server_process.pid)
        baseline_mem = server_psutil.memory_info().rss / 1024 / 1024
        print(f"Server Baseline Memory: {baseline_mem:.2f} MB\n")
    except:
        print("Could not get server process metrics")
        baseline_mem = 0
    
    # Connect WebSocket client
    uri = "ws://localhost:8000/ws"
    messages_received = 0
    deltas_total = 0
    message_sizes = []
    latencies = []
    
    print("Connecting WebSocket client...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully\n")
            
            # Receive full state
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Received full_state: tick={data['tick']}, size={len(msg)} bytes\n")
            
            print("Receiving delta messages for 30 seconds...\n")
            start_time = time.time()
            
            while (time.time() - start_time) < 30:
                msg_start = time.perf_counter()
                
                msg = await websocket.recv()
                latency = (time.perf_counter() - msg_start) * 1000  # ms
                
                data = json.loads(msg)
                messages_received += 1
                deltas_total += len(data.get('deltas', []))
                message_sizes.append(len(msg))
                latencies.append(latency)
                
                if messages_received % 10 == 0:
                    avg_size = sum(message_sizes[-10:]) / 10
                    avg_lat = sum(latencies[-10:]) / 10
                    print(f"Messages: {messages_received}, "
                          f"Avg size: {avg_size:.0f} bytes, "
                          f"Avg latency: {avg_lat:.1f}ms")
            
            elapsed = time.time() - start_time
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        server_process.terminate()
        return False
    
    finally:
        # Stop server
        print("\nStopping server...")
        server_process.send_signal(signal.SIGTERM)
        server_process.wait(timeout=5)
    
    # Calculate metrics
    print(f"\n=== Results ===")
    print(f"Duration: {elapsed:.1f}s")
    print(f"Messages Received: {messages_received}")
    print(f"Total Deltas: {deltas_total}")
    print(f"Average Message Size: {sum(message_sizes)/len(message_sizes):.0f} bytes")
    print(f"Max Message Size: {max(message_sizes)} bytes")
    print(f"Average Latency: {sum(latencies)/len(latencies):.1f}ms")
    print(f"Max Latency: {max(latencies):.1f}ms")
    print(f"Messages/Second: {messages_received/elapsed:.1f}")
    
    # Write to log
    log_path = Path("logs/phase_1b_validation.txt")
    log_path.parent.mkdir(exist_ok=True)
    
    with open(log_path, "w") as f:
        f.write("Phase 1B Network Validation\n")
        f.write("="*50 + "\n")
        f.write(f"Hardware: 128GB Strix Halo HP ZBook, Windows 11\n")
        f.write("="*50 + "\n\n")
        f.write(f"Messages: {messages_received}\n")
        f.write(f"Duration: {elapsed:.1f}s\n")
        f.write(f"Msg/sec: {messages_received/elapsed:.1f}\n")
        f.write(f"Avg Size: {sum(message_sizes)/len(message_sizes):.0f} bytes\n")
        f.write(f"Max Size: {max(message_sizes)} bytes\n")
        f.write(f"Avg Latency: {sum(latencies)/len(latencies):.1f}ms\n")
        f.write(f"Max Latency: {max(latencies):.1f}ms\n")
    
    # Validation assertions
    avg_msg_size = sum(message_sizes) / len(message_sizes)
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    assert messages_received > 50, f"Should receive >50 messages in 30s, got {messages_received}"
    assert avg_msg_size < 1024, f"Avg message size {avg_msg_size:.0f} bytes, should be <1KB"
    assert avg_latency < 50, f"Avg latency {avg_latency:.1f}ms, should be <50ms"
    assert max_latency < 200, f"Max latency {max_latency:.1f}ms, should be <200ms"
    
    print("\n✅ Phase 1B Network Validation PASSED")
    return True

if __name__ == "__main__":
    result = asyncio.run(validate_phase_1b())
    sys.exit(0 if result else 1)
```

**Execution**:
```bash
python scripts/validate_phase_1b.py
```

**Physical Evidence**:
- `logs/phase_1b_validation.txt` generated
- netstat output showing active WebSocket connection
- Task Manager screenshot during test
- Wireshark capture (optional but recommended)

---

## Validation Gates

### Gate 1: Unit Tests
```bash
pytest tests/phase_1b/ -v --tb=short
# All tests must pass
```

### Gate 2: Linting
```bash
ruff check src/api/ tests/phase_1b/
# Must return exit code 0
```

### Gate 3: Type Checking
```bash
mypy src/api/ --strict
# Must return exit code 0
```

### Gate 4: Physical Network Validation
```bash
python scripts/validate_phase_1b.py
# Must complete successfully with all assertions passing
```

### Gate 5: Integration Test
```bash
# Start server
python -m uvicorn src.api.conway_server:app

# Open browser to http://localhost:8000
# Verify WebSocket connection in Developer Tools
# Observe Conway grid updates (manual verification)
```

---

## Failure Handling Protocol

If ANY gate fails:

1. **Capture logs and network traces**:
   ```powershell
   mkdir logs\failures\phase_1b_$(Get-Date -Format 'yyyyMMdd_HHmmss')
   copy logs\*.txt logs\failures\phase_1b_*\
   netstat -an | findstr :8000 > logs\failures\phase_1b_*\netstat.txt
   ```

2. **Update TROUBLESHOOTING.md**:
   ```markdown
   ### WebSocket Connection Refused
   **Context**: Client cannot connect to ws://localhost:8000/ws
   **Symptom**: `ConnectionRefusedError: [WinError 10061]`
   **Error Snippet**:
   \`\`\`
   websockets.exceptions.InvalidStatus: server rejected WebSocket connection: HTTP 404
   \`\`\`
   **Probable Cause**: Server not running or wrong endpoint
   **Quick Fix**: Verify server is running: `netstat -an | findstr :8000`
   **Permanent Fix**: Add health check endpoint, document startup procedure
   **Prevention**: Automated server startup in tests
   **Tags**: network, websocket, P1
   ```

3. **Update REPLICATION-NOTES.md** with environment-specific networking issues

4. **Create ISSUE.md** with network diagnostics

5. **Halt execution** and wait for human

---

## Success Criteria

Phase 1B is complete when:

- [ ] FastAPI server starts and binds to port 8000
- [ ] WebSocket endpoint accepts connections
- [ ] ConwayRunner broadcasts deltas every 500ms
- [ ] All validation gates pass
- [ ] Physical network tests pass
- [ ] Message size <1KB per delta
- [ ] Latency <50ms average
- [ ] Multiple concurrent clients supported
- [ ] Logs show stable operation for 30+ seconds
- [ ] Documentation updated

---

## Deliverables

1. **Code**:
   - `src/api/conway_server.py` (FastAPI + WebSocket)
   - `src/api/conway_runner.py` (Conway integration)
   - `tests/phase_1b/test_server_startup.py`
   - `tests/phase_1b/test_conway_runner.py`
   - `tests/phase_1b/test_network_physical.py`
   - `scripts/validate_phase_1b.py`

2. **Documentation**:
   - REPLICATION-NOTES.md updated with Phase 1B
   - TROUBLESHOOTING.md updated (if issues encountered)
   - `logs/phase_1b_validation.txt`

3. **Evidence**:
   - netstat output showing LISTENING port
   - Browser DevTools screenshot showing WebSocket
   - Task Manager screenshot showing server memory
   - Network validation log file

---

## Execution Command for Agent

```bash
# Agent executes this sequence atomically

# Step 1: Implement server and runner
# (agent writes src/api/*.py)

# Step 2: Implement tests
# (agent writes tests/phase_1b/*.py)

# Step 3: Run validation gates
pytest tests/phase_1b/ -v --tb=short || {
  echo "Unit tests failed"
  # agent updates docs, creates ISSUE, halts
}

ruff check src/api/ tests/phase_1b/ || {
  echo "Linting failed"
  # agent updates docs, creates ISSUE, halts
}

mypy src/api/ --strict || {
  echo "Type checking failed"
  # agent updates docs, creates ISSUE, halts
}

# Step 4: Physical validation
python scripts/validate_phase_1b.py || {
  echo "Physical validation failed"
  # agent updates docs, creates ISSUE, halts
}

# Step 5: Update docs
# (agent updates REPLICATION-NOTES.md)

echo "✅ Phase 1B complete - ready for human review"
```

---

## Notes for Coding Agent

- **Do not proceed to Phase 1C** until Phase 1B approved by human
- **Windows Firewall** may prompt for network access - document if occurs
- **Port 8000** must be available (check with netstat before starting)
- **WebSocket protocol** is `ws://` not `wss://` for local testing
- **Measure real network metrics**, not simulated values
- **Stop on any gate failure** and document thoroughly

This task is **ready for execution** by a coding agent following the Policy lifecycle.