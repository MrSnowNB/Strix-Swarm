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
        self.embedding_grid = EmbeddingGrid(size=grid_size)
        self.tick_ms = tick_ms
        self.running = False
        self.websockets = set()
        self.tick_count = 0
        
        # Interactive mode
        self.mesh_mode = "coupled"  # or "decoupled"
        self.couple_policy = "birth"  # or "alive"
        
        # Command queue for atomic updates
        self.command_queue = []

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

    async def broadcast_conway_deltas(self, deltas):
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

    async def handle_command(self, websocket: WebSocket, data: dict):
        """Handle interactive commands from dashboard"""
        cmd_type = data.get("type")
        
        if cmd_type == "toggle_cell":
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None and 0 <= x < 8 and 0 <= y < 8:
                self.command_queue.append({"type": "toggle", "x": x, "y": y})
                logger.info(f"Queued toggle cell ({x}, {y})")
        
        elif cmd_type == "set_mode":
            self.mesh_mode = data.get("mesh_mode", "coupled")
            self.couple_policy = data.get("policy", "birth")
            logger.info(f"Set mode: {self.mesh_mode}, policy: {self.couple_policy}")
            await websocket.send_json({
                "type": "mode_changed",
                "mesh_mode": self.mesh_mode,
                "policy": self.couple_policy
            })
        
        elif cmd_type == "randomize_dead_embeddings":
            self.command_queue.append({"type": "randomize"})
            logger.info("Queued randomize dead embeddings")
        
        elif cmd_type == "reset":
            self.command_queue.append({"type": "reset"})
            logger.info("Queued reset")

    def process_commands(self):
        """Process queued commands at tick boundary"""
        for cmd in self.command_queue:
            if cmd["type"] == "toggle":
                x, y = cmd["x"], cmd["y"]
                self.grid.grid[y, x] = 1 - self.grid.grid[y, x]
                logger.info(f"Toggled cell ({x}, {y})")
            
            elif cmd["type"] == "randomize":
                for i, state in enumerate(self.embedding_grid.states):
                    x, y = i % 8, i // 8
                    if self.grid.grid[y, x] == 0:  # Dead cell
                        rand_vec = np.random.randn(state.dim).astype(np.float16)
                        rand_vec /= np.linalg.norm(rand_vec) + 1e-8
                        state.vector = rand_vec
                logger.info("Randomized dead cell embeddings")
            
            elif cmd["type"] == "reset":
                self.grid.grid.fill(0)
                self.grid.seed_glider(1, 1)
                logger.info("Reset grid with glider")
        
        self.command_queue.clear()
    
    async def run_loop(self):
        """Main loop with command processing"""
        self.running = True
        self.grid.seed_glider(1, 1)
        
        while self.running:
            tick_start = time.perf_counter()
            
            # Process queued commands
            self.process_commands()
            
            # Conway step
            conway_deltas = self.grid.step()
            
            # Embedding step (if mode allows)
            # ... existing embedding logic
            
            self.tick_count += 1
            
            # Broadcast
            await self.broadcast_conway_deltas(conway_deltas)
            # ... other broadcasts
            
            # Maintain tick rate
            elapsed = time.perf_counter() - tick_start
            sleep_time = (self.tick_ms / 1000.0) - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def stop(self):
        """Stop the Conway loop"""
        self.running = False
        logger.info("Conway runner stopped")
