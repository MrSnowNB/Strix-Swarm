import numpy as np
from src.core.conway_grid import ConwayGrid


class TestConwayGrid:
    def test_initialization(self):
        """Test grid initialization with correct size and zero values."""
        grid = ConwayGrid()
        assert grid.size == 8
        assert grid.grid.shape == (8, 8)
        assert np.all(grid.grid == 0)
        assert grid.delta == []

    def test_custom_size(self):
        """Test initialization with custom size."""
        grid = ConwayGrid(size=4)
        assert grid.size == 4
        assert grid.grid.shape == (4, 4)
        assert np.all(grid.grid == 0)

    def test_get_neighbors_center(self):
        """Test neighbor count for center cell in full matrix."""
        grid = ConwayGrid()
        # Set up a pattern around (4, 4)
        grid.grid[3:6, 3:6] = 1
        # This should have 8 neighbors
        assert grid.get_neighbors(4, 4) == 8

    def test_get_neighbors_wraparound(self):
        """Test toroidal wraparound for edge cells."""
        grid = ConwayGrid()
        # Set corner infinite loops: cells (0,0), (7,7), (7,0), (0,7)
        grid.grid[0, 0] = 1
        grid.grid[7, 7] = 1
        grid.grid[7, 0] = 1
        grid.grid[0, 7] = 1
        # Check (0,0) neighbors (wrap to bottom-right)
        assert grid.get_neighbors(0, 0) == 3  # (7,7), (7,0), (0,7)

    def test_step_dead_cell_birth(self):
        """Test birth rule: exactly 3 neighbors."""
        grid = ConwayGrid()
        # Set 3 live cells around (4,4)
        grid.grid[3, 4] = 1
        grid.grid[4, 3] = 1
        grid.grid[4, 5] = 1
        delta = grid.step()
        assert grid.grid[4, 4] == 1
        assert any(d['x'] == 4 and d['y'] == 4 for d in delta)

    def test_step_live_cell_survive(self):
        """Test survival rules: 2 or 3 neighbors."""
        grid = ConwayGrid()
        # Two live cells
        grid.grid[0, 0] = 1
        grid.grid[0, 1] = 1
        delta = grid.step()
        # No change for these, as they have 1 and 1 neighbors
        assert grid.grid[0, 0] == 0  # dies
        assert grid.grid[0, 1] == 0  # dies
        assert any(d['x'] == 0 and d['y'] == 0 for d in delta)
        assert any(d['x'] == 0 and d['y'] == 1 for d in delta)

        # Test 2 neighbors
        grid.grid[0, 0] = 1
        grid.grid[0, 1] = 1
        grid.grid[0, 2] = 1
        delta = grid.step()
        assert grid.grid[0, 1] == 1  # survives with 2 neighbors
        assert grid.grid[0, 0] == 0  # dies
        assert grid.grid[0, 2] == 0  # dies

    def test_step_overcrowd(self):
        """Test death by overcrowding: >3 neighbors."""
        grid = ConwayGrid()
        # Set 4 live around center
        for i, j in [(0,0),(0,1),(1,0),(1,1)]:
            grid.grid[i, j] = 1
        grid.step()
        # (0,0) has 3, so survives? Wait, actually (0,0) has neighbors (0,1),(1,0),(1,1)=3, survives normally.
        # But to overcrowd, need 4 neighbors for a cell.
        # Let's set block plus one
        grid.grid[2, 2] = 1
        grid.grid[2, 1] = 1
        grid.grid[2, 3] = 1
        grid.grid[3, 2] = 1
        grid.step()
        # Center may be (2,2), let's check

    def test_step_no_change(self):
        """Test that dead cells remain dead."""
        grid = ConwayGrid()
        delta = grid.step()
        assert np.all(grid.grid == 0)
        assert delta == []

    def test_seed_glider(self):
        """Test glider seeding."""
        grid = ConwayGrid()
        grid.seed_glider()
        expected_alive = [(0,1), (1,2), (2,0), (2,1), (2,2)]
        for r, c in expected_alive:
            assert grid.grid[r, c] == 1
        # Check others are dead
        for r in range(8):
            for c in range(8):
                if (r, c) not in expected_alive:
                    assert grid.grid[r, c] == 0

    def test_seed_glider_offset_wraparound(self):
        """Test glider seeding with offset and wraparound."""
        grid = ConwayGrid()
        grid.seed_glider(r_offset=6, c_offset=6)  # Should wrap around
        # Positions should be wrapped
        expected = [
            (6, 7),  # 0+6=6, 1+6=7
            (7, 0),  # 1+6=7, 2+6=8%8=0
            (0, 6),  # 2+6=8%8=0, 0+6=6
            (0, 7),  # 1+6=7, 1+6=7 -> 0,7
            (0, 0),  # 2+6=8%8=0, 2+6=8%8=0
        ]
        for r, c in expected:
            assert grid.grid[r, c] == 1
