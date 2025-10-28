import asyncio
import websockets
import json
import time
import pytest
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
        # Skip full_state
        await websocket.recv()

        for _ in range(10):
            start = time.perf_counter()

            # Send ping (as text)
            await websocket.send("ping")

            # Wait for next message (could be delta or pong)
            await websocket.recv()

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
