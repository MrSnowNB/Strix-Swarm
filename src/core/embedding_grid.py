from src.core.embedding_layer import EmbeddingState, DeltaPayload
from src.core.conway_grid import ConwayGrid
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PassEvent:
    """Record of a delta pass from one cell to another"""
    def __init__(self, tick: int, from_idx: int, to_idx: int,
                 payload_id: str, payload_norm: float,
                 similarity: float, seed: Optional[int] = None):
        self.tick = tick
        self.from_idx = from_idx
        self.to_idx = to_idx
        self.payload_id = payload_id
        self.payload_norm = payload_norm
        self.similarity = similarity
        self.seed = seed

    def to_dict(self):
        """Convert to dict for WebSocket/logging"""
        from_x = self.from_idx % 8
        from_y = self.from_idx // 8
        to_x = self.to_idx % 8
        to_y = self.to_idx // 8

        return {
            'tick': self.tick,
            'from': {'x': from_x, 'y': from_y},
            'to': {'x': to_x, 'y': to_y},
            'payload_id': self.payload_id,
            'norm': round(self.payload_norm, 4),
            'sim': round(self.similarity, 4)
        }


class EmbeddingGrid:
    """Grid of embedding states with delta routing"""

    def __init__(self, size: int = 8, embedding_dim: int = 384):
        self.size = size
        self.embedding_dim = embedding_dim

        # Create embedding state for each cell
        self.states = []
        for i in range(size * size):
            self.states.append(EmbeddingState(cell_idx=i, dim=embedding_dim))

        # Routing policy weights
        self.alpha_cosine = 0.7
        self.alpha_energy = 0.3

        # Pass event log
        self.pass_events: List[PassEvent] = []

        # Tick counter
        self.tick = 0

    def idx_to_xy(self, idx: int) -> Tuple[int, int]:
        """Convert flat index to (x, y)"""
        return (idx % self.size, idx // self.size)

    def xy_to_idx(self, x: int, y: int) -> int:
        """Convert (x, y) to flat index"""
        return y * self.size + x

    def get_neighbors(self, idx: int) -> List[int]:
        """Get Moore neighborhood indices (8-connected with wraparound)"""
        x, y = self.idx_to_xy(idx)
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.size
                ny = (y + dy) % self.size
                neighbors.append(self.xy_to_idx(nx, ny))

        return neighbors

    def route_delta(self, from_idx: int, payload: DeltaPayload,
                    energy_field: Optional[np.ndarray] = None) -> Tuple[int, float]:
        """
        Choose best neighbor to receive delta.

        Policy: score = alpha_cosine * cos_sim + alpha_energy * energy
        """
        neighbor_indices = self.get_neighbors(from_idx)
        scores = []

        for neighbor_idx in neighbor_indices:
            neighbor_state = self.states[neighbor_idx]

            # Cosine similarity between payload and neighbor embedding
            cos_sim = neighbor_state.cosine_similarity(payload.vector)

            # Energy from field (if provided)
            if energy_field is not None:
                nx, ny = self.idx_to_xy(neighbor_idx)
                energy = energy_field[ny, nx]
            else:
                energy = 0.5  # Default neutral energy

            # Weighted score
            score = self.alpha_cosine * cos_sim + self.alpha_energy * energy
            scores.append(score)

        # Pick best neighbor
        best_idx = np.argmax(scores)
        chosen_neighbor = neighbor_indices[best_idx]

        # Log similarity for tracking
        chosen_state = self.states[chosen_neighbor]
        similarity = chosen_state.cosine_similarity(payload.vector)

        return chosen_neighbor, similarity

    def step(self, energy_field: Optional[np.ndarray] = None) -> List[PassEvent]:
        """
        Execute one routing step: pass all pending deltas.

        Returns list of pass events for this tick.
        """
        tick_events = []

        # Find all cells with pending deltas
        pending_cells = [i for i, state in enumerate(self.states)
                        if state.pending_delta is not None]

        # Pass each delta
        for from_idx in pending_cells:
            from_state = self.states[from_idx]
            payload = from_state.pass_delta()

            if payload is None:
                continue

            # Route to best neighbor
            to_idx, similarity = self.route_delta(from_idx, payload, energy_field)
            to_state = self.states[to_idx]

            # Deliver delta
            to_state.receive_delta(payload)

            # Log event
            event = PassEvent(
                tick=self.tick,
                from_idx=from_idx,
                to_idx=to_idx,
                payload_id=payload.id,
                payload_norm=payload.l2_norm,
                similarity=similarity
            )
            tick_events.append(event)
            self.pass_events.append(event)

            logger.debug(f"Tick {self.tick}: Pass {payload.id} from cell {from_idx} "
                        f"to cell {to_idx} (sim={similarity:.3f})")

        self.tick += 1
        return tick_events

    def inject_delta(self, cell_idx: int, vector: np.ndarray, payload_id: str):
        """Inject a new delta payload at a specific cell"""
        payload = DeltaPayload(
            id=payload_id,
            vector=vector.astype(np.float16),
            l2_norm=float(np.linalg.norm(vector)),
            created_tick=self.tick
        )

        self.states[cell_idx].hold_delta(payload)
        logger.info(f"Injected delta {payload_id} at cell {cell_idx}")

    def get_grid_state(self) -> List[dict]:
        """Get current state of all embedding cells for validation"""
        return [
            {
                'cell_idx': i,
                'hash': state.get_hash(),
                'has_pending': state.pending_delta is not None,
                'deltas_received': state.deltas_received,
                'deltas_passed': state.deltas_passed
            }
            for i, state in enumerate(self.states)
        ]
