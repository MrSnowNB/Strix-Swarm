import pytest
import numpy as np
from src.core.embedding_grid import EmbeddingGrid, DeltaPayload, PassEvent


class TestEmbeddingGrid:
    """Test cases for EmbeddingGrid class"""

    def test_grid_initialization(self):
        """Test basic grid initialization"""
        grid = EmbeddingGrid(size=8)

        assert grid.size == 8
        assert grid.embedding_dim == 384
        assert len(grid.states) == 64  # 8x8
        assert grid.tick == 0
        assert len(grid.pass_events) == 0

    def test_neighbor_calculation(self):
        """Test Moore neighborhood calculation with toroidal wraparound"""
        grid = EmbeddingGrid(size=8)

        # Corner cell (0,0) = index 0 - has 8 neighbors due to wraparound
        neighbors = grid.get_neighbors(0)
        assert len(neighbors) == 8  # All 8 neighbors with toroidal wraparound

        # Edge cell (1,0) = index 8
        neighbors = grid.get_neighbors(8)
        assert len(neighbors) == 8  # All 8 neighbors with toroidal wraparound

        # Center cell (4,4) = index 36
        neighbors = grid.get_neighbors(36)
        assert len(neighbors) == 8  # All 8 neighbors

    def test_inject_delta(self):
        """Test delta injection at specific cell"""
        grid = EmbeddingGrid(size=8)

        # Inject at cell 10 (2,1)
        vector = np.random.randn(384).astype(np.float16)
        vector /= np.linalg.norm(vector)
        grid.inject_delta(10, vector, 'inject_test')

        assert grid.states[10].pending_delta is not None
        assert grid.states[10].pending_delta.id == 'inject_test'

        # Other cells should have no pending delta
        for i in range(64):
            if i != 10:
                assert grid.states[i].pending_delta is None

    def test_route_delta_chooses_best(self):
        """Test that routing chooses neighbor with highest similarity"""
        grid = EmbeddingGrid(size=8)

        # Create a payload
        payload_vector = np.ones(384, dtype=np.float16) * 0.5
        payload = DeltaPayload(
            id='route_test',
            vector=payload_vector,
            l2_norm=float(np.linalg.norm(payload_vector)),
            created_tick=0
        )

        from_idx = 36  # Center cell (4,4)

        # Set specific neighbor similarities
        neighbors = grid.get_neighbors(from_idx)
        for neighbor_idx in neighbors:
            # Make cell 44 (5,4) have highest similarity
            if neighbor_idx == 44:
                grid.states[neighbor_idx].vector = np.ones(384, dtype=np.float16) * 0.1
            else:
                grid.states[neighbor_idx].vector = -np.ones(384, dtype=np.float16) * 0.1

        # Route delta
        to_idx, similarity = grid.route_delta(from_idx, payload)

        # Should choose the neighbor with highest similarity
        assert to_idx == 44, "Should route to highest similarity neighbor"
        assert similarity > 0.9, f"Similarity {similarity} should be high"

    def test_step_passes_all_deltas(self):
        """Test that step processes all pending deltas"""
        grid = EmbeddingGrid(size=8)

        # Inject deltas at multiple cells
        cells_with_deltas = [10, 20, 30]
        for i, cell_idx in enumerate(cells_with_deltas):
            vector = np.random.randn(384).astype(np.float16)
            vector /= np.linalg.norm(vector)
            grid.inject_delta(cell_idx, vector, f'step_test_{i}')

        # Verify deltas are pending
        for cell_idx in cells_with_deltas:
            assert grid.states[cell_idx].pending_delta is not None

        # Step
        events = grid.step()

        # Should have 3 pass events
        assert len(events) == 3
        assert len(grid.pass_events) == 3

        # Event IDs should match injected payloads
        event_ids = [e.payload_id for e in events]
        assert 'step_test_0' in event_ids
        assert 'step_test_1' in event_ids
        assert 'step_test_2' in event_ids

        # No deltas should remain pending
        for cell_idx in range(64):
            assert grid.states[cell_idx].pending_delta is None

    def test_pass_events_logged(self):
        """Test that pass events are properly logged"""
        grid = EmbeddingGrid(size=8)

        # Inject and step
        vector = np.random.randn(384).astype(np.float16)
        vector /= np.linalg.norm(vector)
        grid.inject_delta(10, vector, 'log_test')

        events = grid.step()

        assert len(events) == 1
        event = events[0]

        assert isinstance(event, PassEvent)
        assert event.tick == 0  # Tick increments after step
        assert event.from_idx == 10
        assert event.payload_id == 'log_test'
        assert event.payload_norm > 0

    def test_recipient_embeddings_change(self):
        """Test that recipient embeddings change after receiving deltas"""
        grid = EmbeddingGrid(size=8)

        # Record initial hashes
        initial_hashes = [state.get_hash() for state in grid.states]

        # Inject delta
        vector = np.ones(384, dtype=np.float16) * 0.2
        grid.inject_delta(10, vector, 'recipient_test')

        # Step (delta passes)
        events = grid.step()

        assert len(events) == 1
        event = events[0]

        # Check hashes after
        final_hashes = [state.get_hash() for state in grid.states]

        # Sender hash unchanged (only passed, didn't receive)
        assert initial_hashes[event.from_idx] == final_hashes[event.from_idx]

        # Recipient hash changed
        assert initial_hashes[event.to_idx] != final_hashes[event.to_idx]

        # All others unchanged
        for i in range(64):
            if i not in [event.from_idx, event.to_idx]:
                assert initial_hashes[i] == final_hashes[i]

    def test_routing_with_energy_field(self):
        """Test routing with energy field influence"""
        grid = EmbeddingGrid(size=8)

        # Create energy field favoring right side
        energy_field = np.zeros((8, 8))
        energy_field[:, 4:] = 1.0  # Right half has high energy

        payload = DeltaPayload(
            id='energy_test',
            vector=np.ones(384, dtype=np.float16) * 0.1,
            l2_norm=0.1,
            created_tick=0
        )

        from_idx = 36  # (4,4)

        # Route with energy field
        to_idx, similarity = grid.route_delta(from_idx, payload, energy_field)

        # Should prefer right side due to energy
        to_x, to_y = grid.idx_to_xy(to_idx)
        assert to_x >= 4, "Should route to high energy side (x >= 4)"

    def test_get_grid_state(self):
        """Test grid state summary"""
        grid = EmbeddingGrid(size=8)

        # Inject delta at cell 10
        vector = np.ones(384, dtype=np.float16) * 0.5
        grid.inject_delta(10, vector, 'state_test')

        # Get state
        state = grid.get_grid_state()

        assert len(state) == 64
        assert state[10]['has_pending'] is True
        assert state[10]['cell_idx'] == 10

        # Test after step
        grid.step()
        state_after = grid.get_grid_state()
        assert state_after[10]['has_pending'] is False

    def test_pass_event_dict_format(self):
        """Test PassEvent.to_dict() format"""
        event = PassEvent(
            tick=5,
            from_idx=10,
            to_idx=18,
            payload_id='dict_test',
            payload_norm=1.23,
            similarity=0.85
        )

        event_dict = event.to_dict()

        expected = {
            'tick': 5,
            'from': {'x': 2, 'y': 1},  # 10 = 1*8 + 2
            'to': {'x': 2, 'y': 2},    # 18 = 2*8 + 2
            'payload_id': 'dict_test',
            'norm': 1.23,
            'sim': 0.85
        }

        assert event_dict == expected
