import asyncio
import time
import json
from typing import Set
from fastapi import WebSocket
from src.core.conway_grid import ConwayGrid
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

    async def broadcast_deltas(self, deltas):
        """Broadcast delta updates to all clients"""
        if not self.websockets or not deltas:
            return

        message = {
            "type": "delta",
            "tick": self.tick_count,
            "deltas": deltas
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
        self.grid.seed_glider(r_offset=1, c_offset=1)
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
