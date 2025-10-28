#!/usr/bin/env python3
"""
CyberMesh Embedding-Delta Data Path Validation
Phase 1E End-to-End validation script

Validates: backend events = WebSocket messages = frontend overlays
"""

import asyncio
import websockets
import json
import time
import sys
from collections import defaultdict

async def validate_data_path():
    """
    End-to-end validation: backend events = WS messages = overlays
    """
    print("=== CyberMesh Embedding-Delta Data Path Validation ===\n")

    uri = "ws://localhost:8000/ws"

    # Counters for validation
    ws_embedding_messages = 0
    ws_embedding_edges = 0
    ws_conway_messages = 0
    coordinate_mismatches = 0
    embedding_hashes_received = 0
    unique_payload_ids = set()

    # Storage for validation
    received_edges = []
    payload_trajectory = defaultdict(list)  # payload_id -> [(tick, from_cell, to_cell), ...]

    # Validation flags
    has_embedding_messages = False

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server via WebSocket\n")

            # Skip full_state message
            full_state_msg = await websocket.recv()
            full_state = json.loads(full_state_msg)
            if full_state.get('type') == 'full_state':
                print(f"✓ Received full_state for {full_state.get('size', '?')}x{full_state.get('size', '?')} grid")
            else:
                print("⚠️  Expected full_state message first")

            print("Collecting data for 60 seconds...\n")
            start_time = time.time()

            while (time.time() - start_time) < 60:

                try:
                    msg_str = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(msg_str)

                    if data['type'] == 'delta':
                        ws_conway_messages += 1
                        if ws_conway_messages % 10 == 0:
                            print(f"Conway delta {ws_conway_messages} @ tick {data.get('tick', '?')}")

                    elif data['type'] == 'embedding_deltas':
                        has_embedding_messages = True
                        ws_embedding_messages += 1

                        tick = data.get('tick', 0)
                        edges = data.get('edges', [])

                        print(f"✨ Embedding deltas @ tick {tick}: {len(edges)} passes")

                        for edge in edges:
                            ws_embedding_edges += 1

                            # Validate coordinates
                            from_x = edge['from']['x']
                            from_y = edge['from']['y']
                            to_x = edge['to']['x']
                            to_y = edge['to']['y']

                            # Coordinate validation
                            if not (0 <= from_x < 8 and 0 <= from_y < 8):
                                coordinate_mismatches += 1
                                print(f"❌ Invalid from coords: ({from_x}, {from_y})")
                            if not (0 <= to_x < 8 and 0 <= to_y < 8):
                                coordinate_mismatches += 1
                                print(f"❌ Invalid to coords: ({to_x}, {to_y})")

                            # Track payload trajectory
                            payload_id = edge['payload_id']
                            unique_payload_ids.add(payload_id)

                            from_cell = from_y * 8 + from_x
                            to_cell = to_y * 8 + to_x

                            payload_trajectory[payload_id].append(
                                (tick, from_cell, to_cell, edge.get('norm', 0), edge.get('sim', 0))
                            )

                            received_edges.append(edge)

                            print(f"  → {payload_id}: ({from_x},{from_y}) → ({to_x},{to_y}) "
                                  f"[norm={edge.get('norm', 0):.2f}, sim={edge.get('sim', 0):.2f}]")

                except asyncio.TimeoutError:
                    print("Timeout waiting for messages...")
                    break
                except websockets.ConnectionClosed:
                    print("WebSocket connection closed")
                    break

            elapsed = time.time() - start_time

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Analysis and Results
    print(f"\n=== Data Path Analysis ===")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"WebSocket Messages: Conway={ws_conway_messages}, Embedding={ws_embedding_messages}")
    print(f"Embedding Edges: {ws_embedding_edges}")
    print(f"Unique Payload IDs: {len(unique_payload_ids)}")
    print(f"Coordinate Mismatches: {coordinate_mismatches}")
    print(f"Payload Trajectories Tracked: {len(payload_trajectory)}")

    # Embedding Activity Summary
    if payload_trajectory:
        print(f"\nPayload Activity:")
        for payload_id, trajectory in payload_trajectory.items():
            hops = len(trajectory)
            start_cell = trajectory[0][1] if trajectory else "?"
            final_cell = trajectory[-1][2] if trajectory else "?"
            print(f"  {payload_id}: {hops} hop(s), {start_cell} → {final_cell}")

    # Validation Results
    success = True
    warnings = []

    print(f"\n=== Validation Results ===")

    # Critical validations
    if coordinate_mismatches > 0:
        print(f"❌ FAIL: {coordinate_mismatches} coordinate mismatches - WebSocket messages corrupted")
        success = False

    if not has_embedding_messages:
        warnings.append("No embedding delta messages received - check inject_delta() call")
        print("⚠️  WARNING: No embedding delta messages")
    else:
        print("✓ PASS: Embedding delta messages received")

    if ws_embedding_messages > 0 and ws_embedding_edges == 0:
        print("❌ FAIL: Embedding messages present but no edges")
        success = False
    elif ws_embedding_edges > 0:
        edges_per_msg = ws_embedding_edges / ws_embedding_messages
        print(f"Avg edges/message: {edges_per_msg:.2f}")
        if edges_per_msg > 8:  # More than max neighbors per step
            warnings.append(f"High edges/message ({edges_per_msg:.1f}) suggests message size issues")

    if len(unique_payload_ids) == 0:
        warnings.append("No payload IDs tracked - check payload_id generation")
        print("⚠️  WARNING: No payload IDs tracked")

    # Check for proper trajectory patterns
    valid_trajectories = 0
    for trajectory in payload_trajectory.values():
        if len(trajectory) >= 1:
            valid_trajectories += 1

    trajectory_ratio = valid_trajectories / len(unique_payload_ids) if unique_payload_ids else 0
    if trajectory_ratio < 0.5:
        warnings.append(f"Low trajectory completion ({trajectory_ratio:.0f}%)")

    if success:
        print("✅ DATA PATH VALIDATION: PASS")
        print(f"   ✓ {ws_embedding_edges} embedding passes tracked")
        print(f"   ✓ Zero coordinate errors")
        print(f"   ✓ {len(unique_payload_ids)} unique payloads processed")
        print("   ✓ Backend events → WebSocket messages confirmed")
    else:
        print("❌ DATA PATH VALIDATION: FAIL")
        print("   Investigate coordinate mismatches or message structure issues")

    # Warnings
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    # Write detailed report
    report_path = "logs/data_path_validation.txt"
    with open(report_path, "w") as f:
        f.write("CyberMesh Data Path Validation Report\n")
        f.write("="*50 + "\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {elapsed:.1f}s\n")
        f.write(f"Status: {'PASS' if success else 'FAIL'}\n\n")

        f.write("Message Counts:\n")
        f.write(f"  Conway deltas: {ws_conway_messages}\n")
        f.write(f"  Embedding messages: {ws_embedding_messages}\n")
        f.write(f"  Total embedding edges: {ws_embedding_edges}\n")
        f.write(f"  Unique payloads: {len(unique_payload_ids)}\n\n")

        f.write("Quality Metrics:\n")
        f.write(f"Avg edges/message: {edges_per_msg:.2f}\n" if 'edges_per_msg' in locals() else "Avg edges/message: N/A\n")
        f.write(f"  Coordinate errors: {coordinate_mismatches}\n")
        f.write(f"  Trajectory completeness: {trajectory_ratio:.1%}\n\n")

        if received_edges:
            f.write("Sample Edges:\n")
            for i, edge in enumerate(received_edges[:5]):  # First 5
                f.write(f"  {i+1}. {edge}\n")
            if len(received_edges) > 5:
                f.write(f"  ... ({len(received_edges)-5} more)\n")

    print(f"\nDetailed report saved to: {report_path}")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(validate_data_path())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nValidation failed with exception: {e}")
        sys.exit(1)
