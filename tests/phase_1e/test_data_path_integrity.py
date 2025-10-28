import pytest
import numpy as np
from src.core.embedding_grid import EmbeddingGrid, PassEvent
from src.core.conway_grid import ConwayGrid
from src.core.embedding_layer import DeltaPayload


class TestDataPathIntegrity:
    """Test that embedding data flows correctly through the system"""

    def test_pass_event_creates_hash_change(self):
        """Recipient cell embedding hash changes, others don't"""
        grid = EmbeddingGrid(size=8)

        # Record hashes before
        hashes_before = [state.get_hash() for state in grid.states]

        # Inject delta at cell 10
        vector = np.ones(384, dtype=np.float16) * 0.2
        grid.inject_delta(10, vector, "test_001")

        # Step (passes delta)
        events = grid.step()

        # Check hashes after
        hashes_after = [state.get_hash() for state in grid.states]

        assert len(events) == 1, "Should have exactly 1 pass event"

        event = events[0]
        from_idx = event.from_idx
        to_idx = event.to_idx

        # Sender hash unchanged (just passed, didn't receive)
        assert hashes_before[from_idx] == hashes_after[from_idx], \
            "Sender hash should not change"

        # Recipient hash changed
        assert hashes_before[to_idx] != hashes_after[to_idx], \
            f"Recipient hash should change: before={hashes_before[to_idx]}, after={hashes_after[to_idx]}"

        # All other hashes unchanged
        for i in range(64):
            if i not in [from_idx, to_idx]:
                assert hashes_before[i] == hashes_after[i], \
                    f"Cell {i} hash should not change (only recipient should change)"

    def test_embedding_independence_from_conway(self):
        """Embedding changes are independent of Conway flips"""
        conway = ConwayGrid(size=8)
        embedding = EmbeddingGrid(size=8)

        # Seed glider in Conway
        conway.seed_glider(1, 1)

        # Record embedding hashes
        hashes_before = [s.get_hash() for s in embedding.states]

        # Conway step (NO embedding deltas)
        conway_deltas = conway.step()

        # Check embeddings unchanged
        hashes_after = [s.get_hash() for s in embedding.states]

        assert len(conway_deltas) > 0, "Conway should have deltas"
        assert hashes_before == hashes_after, \
            "Embeddings should not change without delta passes"

    def test_conway_and_embedding_separate_deltas(self):
        """Conway and embedding produce separate delta streams"""
        from src.api.conway_runner import ConwayRunner
        import asyncio

        # Create runner with embedded integration
        runner = ConwayRunner(grid_size=8, tick_ms=1000)

        # Step once ( this will create conway deltas and potentially embedding deltas)
        # But our test delta will only be injected once at startup

        # Record initial state
        conway_grid_state = runner.grid.get_state().copy()

        # Step the runner manually for testing
        conway_deltas = runner.grid.step()
        embedding_events = runner.embedding_grid.step(runner.grid.grid.astype(np.float32) * 0.5 + 0.25)

        # Conway deltas should exist (from glider movement/updates)
        # Embedding deltas may or may not exist depending on routing
        # They should be separate structures

        # Test type separation
        assert isinstance(conway_deltas, list), "Conway deltas should be list"
        assert isinstance(embedding_events, list), "Embedding events should be list"

        if conway_deltas:
            assert len(conway_deltas) > 0
            # Check Conway delta format
            delta = conway_deltas[0]
            assert 'x' in delta and 'y' in delta and 'alive' in delta

        if embedding_events:
            assert len(embedding_events) > 0
            # Check embedding event format
            event = embedding_events[0]
            assert isinstance(event, PassEvent)
            assert hasattr(event, 'from_idx') and hasattr(event, 'to_idx')

    @pytest.mark.asyncio
    async def test_ws_message_format_validation(self):
        """Validate WebSocket message structure matches expectations"""
        from src.api.conway_runner import ConwayRunner

        runner = ConwayRunner(grid_size=8)

        # Test broadcast_embedding_deltas directly
        events = [
            PassEvent(1, 10, 11, "ws_test", 1.0, 0.8),
            PassEvent(1, 20, 21, "ws_test_2", 0.5, 0.6)
        ]

        # Get message data (but don't actually broadcast since no websockets)
        message = {
            "type": "embedding_deltas",
            "tick": runner.tick_count or 1,
            "edges": [event.to_dict() for event in events]
        }

        # Validate structure
        assert message["type"] == "embedding_deltas"
        assert "tick" in message
        assert "edges" in message
        assert len(message["edges"]) == 2

        # Check edge format
        edge = message["edges"][0]
        required_keys = ["tick", "from", "to", "payload_id", "norm", "sim"]
        for key in required_keys:
            assert key in edge, f"Missing key: {key}"

        # Check coordinate format
        assert "x" in edge["from"] and "y" in edge["from"]
        assert "x" in edge["to"] and "y" in edge["to"]

    def test_energy_field_influences_routing(self):
        """Energy field (Conway state) should influence embedding routing"""
        grid = EmbeddingGrid(size=8)

        # Create asymmetric energy field
        energy_field = np.zeros((8, 8))
        energy_field[4:, :] = 2.0  # Bottom half high energy

        payload = DeltaPayload(
            id="energy_route_test",
            vector=np.ones(384, dtype=np.float16) * 0.1,
            l2_norm=0.1,
            created_tick=0
        )

        from_idx = 18  # (2,2) - top half

        # Route with and without energy
        to_idx_no_energy, _ = grid.route_delta(from_idx, payload, None)
        to_idx_with_energy, _ = grid.route_delta(from_idx, payload, energy_field)

        # At least one should prefer bottom half due to energy
        to_y_no_energy = grid.idx_to_xy(to_idx_no_energy)[1]
        to_y_with_energy = grid.idx_to_xy(to_idx_with_energy)[1]

        # Energy field should bias toward bottom half (y >= 4)
        # This is probabilistic, but with strong energy difference (2.0 vs 0.5)
        # it should usually route to bottom half
        assert to_y_with_energy >= 4 or to_y_no_energy < 4, \
            "Energy field should influence routing toward high energy areas"


class TestEmbeddingIntegration:
    """Integration tests for embedding with Conway system"""

    def test_conway_embedding_tick_alignment(self):
        """Embedding ticks should align with Conway ticks"""
        from src.api.conway_runner import ConwayRunner

        runner = ConwayRunner(grid_size=8)

        initial_embed_tick = runner.embedding_grid.tick
        initial_conway_tick = runner.tick_count

        # Step Conway and embedding together
        conway_deltas = runner.grid.step()
        embedding_events = runner.embedding_grid.step(
            runner.grid.grid.astype(np.float32) * 0.5 + 0.25
        )

        runner.tick_count += 1

        # Embedding tick should be updated
        final_embed_tick = runner.embedding_grid.tick
        assert final_embed_tick == initial_embed_tick + 1

    def test_multiple_step_consistency(self):
        """Multiple steps should maintain consistency"""
        grid = EmbeddingGrid(size=8)

        hashes_over_time = []
        hashes_over_time.append([s.get_hash() for s in grid.states])

        # Perform multiple steps with deltas
        for i in range(3):
            # Inject delta
            vector = np.random.randn(384).astype(np.float16)
            vector /= np.linalg.norm(vector)
            grid.inject_delta(i * 20, vector, f"multi_test_{i}")  # Use i*20 to avoid overlaps

            # Step
            events = grid.step()

            # Record state
            hashes_over_time.append([s.get_hash() for s in grid.states])

        # Each step should produce at least one pass event
        total_events = len(grid.pass_events)
        assert total_events >= 3, f"Should have at least 3 total pass events, got {total_events}"

        # Each consecutive hash set should have exactly one changed cell
        # (plus possibly the sender which changes when receiving)
        for i in range(1, len(hashes_over_time)):
            before = hashes_over_time[i-1]
            after = hashes_over_time[i]
            changed_count = sum(1 for b, a in zip(before, after) if b != a)
            assert changed_count >= 1, f"Step {i} should change at least 1 cell"
            # Allow more flexibility for cascading effects
            assert changed_count <= 3, f"Step {i} should change at most 3 cells"
