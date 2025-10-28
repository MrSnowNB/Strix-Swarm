import pytest
import numpy as np
from src.core.embedding_layer import EmbeddingState, DeltaPayload


class TestEmbeddingState:
    """Test cases for EmbeddingState class"""

    def test_initialization(self):
        """Test basic initialization"""
        state = EmbeddingState(cell_idx=5)

        assert state.cell_idx == 5
        assert state.dim == 384
        assert state.vector.shape == (384,)
        assert state.pending_delta is None
        assert len(state.history) == 1
        assert state.deltas_received == 0
        assert state.deltas_passed == 0

    def test_hold_delta(self):
        """Test delta hold/pass mechanism"""
        state = EmbeddingState(cell_idx=0)

        # Create test payload
        vector = np.random.randn(384).astype(np.float16)
        vector /= np.linalg.norm(vector)
        payload = DeltaPayload(
            id='test_001',
            vector=vector,
            l2_norm=float(np.linalg.norm(vector)),
            created_tick=0
        )

        # Hold delta
        state.hold_delta(payload)
        assert state.pending_delta == payload

    def test_pass_delta(self):
        """Test delta pass mechanism"""
        state = EmbeddingState(cell_idx=0)

        # Hold then pass
        vector = np.random.randn(384).astype(np.float16)
        vector /= np.linalg.norm(vector)
        payload = DeltaPayload(
            id='test_002',
            vector=vector,
            l2_norm=float(np.linalg.norm(vector)),
            created_tick=1
        )

        state.hold_delta(payload)
        passed = state.pass_delta()

        assert passed == payload
        assert state.pending_delta is None
        assert state.deltas_passed == 1

    def test_no_double_hold(self):
        """Cannot hold two deltas simultaneously"""
        state = EmbeddingState(cell_idx=0)

        payload1 = DeltaPayload(
            id='test_003',
            vector=np.ones(384, dtype=np.float16),
            l2_norm=1.0,
            created_tick=0
        )
        payload2 = DeltaPayload(
            id='test_004',
            vector=np.ones(384, dtype=np.float16) * 0.5,
            l2_norm=0.5,
            created_tick=0
        )

        state.hold_delta(payload1)

        # Should raise assertion error
        with pytest.raises(AssertionError):
            state.hold_delta(payload2)

    def test_receive_delta(self):
        """Test delta receiving and embedding update"""
        state = EmbeddingState(cell_idx=0)

        # Record initial state
        initial_hash = state.get_hash()
        initial_cos = state.cosine_with_previous()

        # Create delta payload
        delta_vector = np.ones(384, dtype=np.float16) * 0.1
        payload = DeltaPayload(
            id='delta_001',
            vector=delta_vector,
            l2_norm=float(np.linalg.norm(delta_vector)),
            created_tick=1
        )

        # Receive delta
        state.receive_delta(payload)

        # Check changes
        final_hash = state.get_hash()
        final_cos = state.cosine_with_previous()

        assert initial_hash != final_hash, "Hash should change after delta"
        assert state.deltas_received == 1
        assert len(state.history) == 2  # Initial + after delta
        assert final_cos < 1.0, "Cosine should decrease (embedding changed)"

    def test_hash_consistency(self):
        """Hash should be different after delta application"""
        state1 = EmbeddingState(cell_idx=0)
        state2 = EmbeddingState(cell_idx=0)

        # Identical initial states
        assert state1.get_hash() == state2.get_hash()

        # Apply very different deltas to ensure hash difference
        delta1 = DeltaPayload(
            id='d1',
            vector=np.ones(384, dtype=np.float16) * 0.1,  # All positive small values
            l2_norm=0.1,
            created_tick=0
        )
        delta2 = DeltaPayload(
            id='d2',
            vector=np.ones(384, dtype=np.float16) * -0.5,  # All negative values
            l2_norm=0.5,
            created_tick=0
        )

        state1.receive_delta(delta1)
        state2.receive_delta(delta2)

        # Hashes should differ due to different vector directions/content
        assert state1.get_hash() != state2.get_hash(), \
            f"Hashes should be different: '{state1.get_hash()}' vs '{state2.get_hash()}'"

    def test_cosine_similarity(self):
        """Test cosine similarity computation"""
        state = EmbeddingState(cell_idx=0)

        vec1 = np.ones(384)  # All ones
        vec2 = np.ones(384) * 0.5  # Half magnitude
        vec3 = -np.ones(384)  # Opposite direction

        sim1 = state.cosine_similarity(vec1)
        sim2 = state.cosine_similarity(vec2)
        sim3 = state.cosine_similarity(vec3)

        # Initial state is zeros, so similarity with anything is 0
        assert sim1 == 0.0
        assert sim2 == 0.0
        assert sim3 == 0.0

    def test_vector_normalization(self):
        """Test that vectors are approximately normalized after delta application"""
        state = EmbeddingState(cell_idx=0)

        # Large delta to ensure magnitude > 1
        delta_vector = np.ones(384, dtype=np.float16) * 10.0
        payload = DeltaPayload(
            id='big_delta',
            vector=delta_vector,
            l2_norm=float(np.linalg.norm(delta_vector)),
            created_tick=1
        )

        state.receive_delta(payload)

        # Vector should be approximately normalized (magnitude close to 1)
        norm = np.linalg.norm(state.vector.astype(np.float32))
        # Allow for float16 precision issues (more lenient tolerance)
        assert abs(norm - 1.0) < 1e-3, f"Vector norm {norm} should be close to 1.0"
