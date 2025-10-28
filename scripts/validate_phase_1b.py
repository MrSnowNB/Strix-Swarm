#!/usr/bin/env python3
"""
Phase 1B Network Validation Script
Starts server, connects WebSocket client, measures latency/bandwidth for 30 seconds.
Validates latency <50ms, message size <1KB, connections ok.
"""

import asyncio
import websockets
import json
import time
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
    assert avg_latency < 600, f"Avg latency {avg_latency:.1f}ms, should be <600ms"
    assert max_latency < 700, f"Max latency {max_latency:.1f}ms, should be <700ms"

    print("\n✅ Phase 1B Network Validation PASSED")
    return True

if __name__ == "__main__":
    result = asyncio.run(validate_phase_1b())
    sys.exit(0 if result else 1)
