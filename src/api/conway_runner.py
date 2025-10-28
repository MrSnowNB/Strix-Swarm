import asyncio
import time
import json
from typing import Set, Optional
from fastapi import WebSocket
from src.core.conway_grid import ConwayGrid
from src.core.embedding_grid import EmbeddingGrid
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ConwayRunner:
    """Manages Conway grid execution and WebSocket broadcasting"""

    def __init__(self, grid_size: int = 8, tick_ms: int = 500):
        self.grid = ConwayGrid(size=grid_size)
        self.embedding_grid = EmbeddingGrid(size=grid_size)  # NEW
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

    async def broadcast_embedding_deltas(self, pass_events):
        """Broadcast embedding pass events to all clients"""
        if not self.websockets or not pass_events:
            return

        message = {
            "type": "embedding_deltas",
            "tick": self.tick_count,
            "edges": [event.to_dict() for event in pass_events]
        }

        # Check message size
        msg_size = len(json.dumps(message))
        if msg_size > 1024:
            logger.warning(f"Embedding delta message {msg_size} bytes exceeds 1KB")

        # Broadcast
        disconnected = set()
        for ws in self.websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send embedding deltas: {e}")
                disconnected.add(ws)

        self.websockets -= disconnected
        return msg_size

    async def handle_command(self, command_data: dict) -> Optional[str]:
        """Handle interactive commands from dashboard"""
        cmd_type = command_data.get("type")
        response = None

        if cmd_type == "toggle_cell":
            x = command_data.get("x")
            y = command_data.get("y")
            if x is not None and y is not None and 0 <= x < 8 and 0 <= y < 8:
                self.grid.grid[y, x] = 1 - self.grid.grid[y, x]
                logger.info(f"Toggled cell ({x}, {y}) to {self.grid.grid[y, x]}")

        elif cmd_type == "set_mode":
            mesh_mode = command_data.get("mesh_mode", "coupled")
            policy = command_data.get("policy", "birth")
            # Store mode settings for future use
            logger.info(f"Set mode: {mesh_mode}, policy: {policy}")
            response = f"Mode set to {mesh_mode} with {policy} policy"

        elif cmd_type == "randomize_dead_embeddings":
            # Randomize embeddings for dead cells
            import numpy as np
            for i, state in enumerate(self.embedding_grid.states):
                x, y = i % 8, i // 8
                if self.grid.grid[y, x] == 0:  # Dead cell
                    rand_vec = np.random.randn(state.dim).astype(np.float16)
                    rand_vec /= np.linalg.norm(rand_vec) + 1e-8
                    state.vector = rand_vec
            logger.info("Randomized embeddings for dead cells")

        elif cmd_type == "reset":
            self.grid.grid.fill(0)
            self.grid.seed_glider(1, 1)
            logger.info("Reset grid with glider")

        else:
            logger.warning(f"Unknown command type: {cmd_type}")

        return response

    async def run_loop(self):
        """Main Conway loop at 500ms ticks with embedding integration"""
        self.running = True

        # Seed glider at startup
        self.grid.seed_glider(r_offset=1, c_offset=1)
        logger.info("Glider seeded at (1,1)")

        # Inject test delta for validation
        test_vector = np.random.randn(384).astype(np.float16)
        test_vector /= np.linalg.norm(test_vector)
        self.embedding_grid.inject_delta(
            cell_idx=10,  # Cell (2, 1)
            vector=test_vector,
            payload_id=f"test_delta_0"
        )
        logger.info("Test delta injected at cell (2,1)")

        # Send initial state to any connected clients
        for ws in list(self.websockets):
            await self.send_full_state(ws)

        while self.running:
            tick_start = time.perf_counter()

            # Step 1: Conway evolution
            conway_deltas = self.grid.step()

            # Step 2: Embedding delta passes (using Conway energy field)
            energy_field = self.grid.grid.astype(np.float32) * 0.5 + 0.25
            pass_events = self.embedding_grid.step(energy_field)

            self.tick_count += 1

            # Inject test delta every 10 ticks for continuous validation
            if self.tick_count % 10 == 0:
                test_vector = np.random.randn(384).astype(np.float16)
                test_vector /= np.linalg.norm(test_vector)
                cell_idx = self.tick_count % 64  # Vary injection location
                self.embedding_grid.inject_delta(
                    cell_idx=cell_idx,
                    vector=test_vector,
                    payload_id=f"periodic_delta_{self.tick_count}"
                )
                logger.debug(f"Injected periodic delta at cell {cell_idx}")

            # Step 3: Broadcast both types of deltas
            if self.websockets:
                conway_msg_size = await self.broadcast_deltas(conway_deltas)
                embedding_msg_size = await self.broadcast_embedding_deltas(pass_events)

                if self.tick_count % 10 == 0:
                    logger.info(f"Tick {self.tick_count}: Conway={len(conway_deltas)} deltas "
                              f"({conway_msg_size or 0} bytes), "
                              f"Embedding={len(pass_events)} passes "
                              f"({embedding_msg_size or 0} bytes), "
                              f"{len(self.websockets)} clients")

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
