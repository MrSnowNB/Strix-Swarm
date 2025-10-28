import numpy as np
from dataclasses import dataclass
from collections import deque
from typing import Optional, Deque

@dataclass
class DeltaPayload:
    """A delta payload to be held and passed"""
    id: str  # Unique identifier for tracking
    vector: np.ndarray  # 384-D delta vector (float16)
    l2_norm: float  # Magnitude for validation
    created_tick: int  # When payload was created

    def __post_init__(self):
        assert self.vector.shape == (384,), f"Expected 384-D vector, got {self.vector.shape}"
        assert self.vector.dtype == np.float16, f"Expected float16, got {self.vector.dtype}"


class EmbeddingState:
    """Per-cell embedding state with delta hold/pass capability"""

    def __init__(self, cell_idx: int, dim: int = 384):
        self.cell_idx = cell_idx
        self.dim = dim

        # Current embedding vector (normalized)
        self.vector = np.zeros(dim, dtype=np.float16)

        # History for change detection
        self.history: Deque[np.ndarray] = deque(maxlen=4)
        self.history.append(self.vector.copy())

        # Pending delta (if holding)
        self.pending_delta: Optional[DeltaPayload] = None

        # Pass statistics
        self.deltas_received = 0
        self.deltas_passed = 0

    def hold_delta(self, payload: DeltaPayload):
        """Hold a delta payload for next pass"""
        assert self.pending_delta is None, \
            f"Cell {self.cell_idx} already holding delta {self.pending_delta.id}"
        self.pending_delta = payload

    def pass_delta(self) -> Optional[DeltaPayload]:
        """Release held delta and return it"""
        payload = self.pending_delta
        self.pending_delta = None
        if payload:
            self.deltas_passed += 1
        return payload

    def receive_delta(self, payload: DeltaPayload, alpha: float = 0.1):
        """Apply incoming delta to embedding vector"""
        # Save old vector to history
        self.history.append(self.vector.copy())

        # Apply delta with learning rate
        self.vector = self.vector + alpha * payload.vector

        # Normalize
        norm = np.linalg.norm(self.vector)
        if norm > 1e-8:
            self.vector = self.vector / norm

        self.deltas_received += 1

    def get_hash(self) -> str:
        """Get short hash of current vector for validation"""
        # Use xxhash or simple hash for quick comparison
        hash_val = hash(self.vector.tobytes())
        return f"{hash_val & 0xFFFFFF:06x}"  # Last 6 hex digits

    def cosine_similarity(self, other_vector: np.ndarray) -> float:
        """Compute cosine similarity with another vector"""
        dot = np.dot(self.vector, other_vector)
        norm_self = np.linalg.norm(self.vector)
        norm_other = np.linalg.norm(other_vector)

        if norm_self < 1e-8 or norm_other < 1e-8:
            return 0.0

        return float(dot / (norm_self * norm_other))

    def cosine_with_previous(self) -> float:
        """Cosine similarity with previous vector in history"""
        if len(self.history) < 2:
            return 1.0

        prev = self.history[-2]
        return self.cosine_similarity(prev)
