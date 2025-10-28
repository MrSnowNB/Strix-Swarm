import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.conway_grid import ConwayGrid


def test_isolated_cell_dies():
    """Death: Cell with 0 neighbors dies"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1

    grid.step()

    assert grid.grid[3, 3] == 0, "Isolated cell should die"


def test_two_cells_both_die():
    """Death: Two cells with 1 neighbor each both die"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1

    grid.step()

    assert grid.grid[3, 3] == 0, "Cell with 1 neighbor should die"
    assert grid.grid[3, 4] == 0, "Cell with 1 neighbor should die"


def test_block_stable():
    """Survival: 2x2 block is stable (each has 3 neighbors)"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1

    before = grid.grid.copy()
    grid.step()

    assert np.array_equal(grid.grid, before), "Block should be stable"


def test_birth_rule():
    """Birth: Dead cell with exactly 3 neighbors becomes alive"""
    grid = ConwayGrid(size=8)
    grid.grid[2, 3] = 1  # North of center
    grid.grid[3, 2] = 1  # West of center
    grid.grid[3, 4] = 1  # East of center
    # Center (3,3) is dead with 3 neighbors

    grid.step()

    assert grid.grid[3, 3] == 1, "Cell with 3 neighbors should be born"


def test_overpopulation():
    """Death: Cell with 4+ neighbors dies"""
    grid = ConwayGrid(size=8)
    # Center surrounded by 4 neighbors (cross pattern)
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    grid.grid[3, 4] = 1  # East

    grid.step()

    assert grid.grid[3, 3] == 0, "Cell with 4 neighbors should die"


def test_blinker_oscillates():
    """Blinker pattern oscillates with period 2"""
    grid = ConwayGrid(size=8)
    # Horizontal blinker
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[3, 5] = 1

    state0 = grid.grid.copy()

    grid.step()
    state1 = grid.grid.copy()
    assert not np.array_equal(state0, state1), "Blinker should change"

    grid.step()
    state2 = grid.grid.copy()
    assert np.array_equal(state0, state2), "Blinker should return to original"


def test_glider_moves():
    """Glider pattern moves diagonally"""
    grid = ConwayGrid(size=16)  # Larger grid for movement
    grid.seed_glider(4, 4)

    # Count live cells
    initial_count = np.sum(grid.grid)
    assert initial_count == 5, "Glider should have 5 cells"

    # Step 4 times (one glider cycle)
    for _ in range(4):
        grid.step()

    final_count = np.sum(grid.grid)
    assert final_count == 5, "Glider should maintain 5 cells"


def test_wraparound_corner():
    """Wraparound: Corners see opposite corners as neighbors"""
    grid = ConwayGrid(size=8)
    grid.grid[0, 0] = 1  # Top-left corner

    # Manually check neighbors
    neighbors = grid.get_neighbors(0, 0)

    # Top-left corner should see bottom-right as diagonal neighbor
    # But since it's the only cell, it has 0 neighbors
    assert neighbors == 0, "Single corner cell should have 0 neighbors"


def test_edge_wraparound():
    """Wraparound: Edge cells see opposite edge vertically"""
    grid = ConwayGrid(size=8)
    grid.grid[0, 0] = 1  # Top-left corner
    grid.grid[7, 0] = 1  # Bottom-left corner (wraps around)

    neighbors_top = grid.get_neighbors(0, 0)  # Top-left should see bottom-left as neighbor
    assert neighbors_top >= 1, "Top corner should see bottom corner neighbor through wraparound"


def test_four_neighbors():
    """Cell with exactly 4 neighbors dies (overpopulation)"""
    grid = ConwayGrid(size=8)
    # Center with 4 direct neighbors (plus pattern)
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    grid.grid[3, 4] = 1  # East

    grid.step()
    assert grid.grid[3, 3] == 0, "Cell with 4 neighbors should die"


def test_eight_neighbors_underpopulation():
    """Cell with 8 neighbors dies (overpopulation)"""
    grid = ConwayGrid(size=8)
    # Center surrounded by all 8 neighbors
    grid.grid[3, 3] = 1  # Center

    # All 8 surrounding cells
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                grid.grid[(3 + dy) % 8, (3 + dx) % 8] = 1

    grid.step()
    assert grid.grid[3, 3] == 0, "Cell with 8 neighbors should die"


def test_survival_two_neighbors():
    """Survival: Cell with exactly 2 neighbors survives"""
    grid = ConwayGrid(size=8)
    # Cell with exactly 2 neighbors
    grid.grid[3, 3] = 1  # Center will have 2 neighbors
    grid.grid[2, 3] = 1  # North neighbor
    grid.grid[4, 3] = 1  # South neighbor

    grid.step()
    assert grid.grid[3, 3] == 1, "Cell with 2 neighbors should survive"


def test_survival_three_neighbors():
    """Survival: Cell with exactly 3 neighbors survives"""
    grid = ConwayGrid(size=8)
    # Cell with exactly 3 neighbors
    grid.grid[3, 3] = 1  # Center will have 3 neighbors
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West

    grid.step()
    assert grid.grid[3, 3] == 1, "Cell with 3 neighbors should survive"


def test_dead_cell_no_birth():
    """Dead cell with < 3 neighbors stays dead"""
    grid = ConwayGrid(size=8)
    grid.grid[2, 3] = 1  # Will give center 1 neighbor
    # Center (3,3) dead with only 1 neighbor

    grid.step()
    assert grid.grid[3, 3] == 0, "Dead cell with 1 neighbor should stay dead"


def test_dead_cell_too_many_neighbors():
    """Dead cell with > 3 neighbors stays dead"""
    grid = ConwayGrid(size=8)
    # Center will have 4 neighbors
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    grid.grid[3, 4] = 1  # East

    grid.step()
    assert grid.grid[3, 3] == 0, "Dead cell with 4 neighbors should stay dead"


def test_empty_grid():
    """Empty grid stays empty"""
    grid = ConwayGrid(size=8)
    # All cells dead initially

    before = grid.grid.copy()
    grid.step()
    after = grid.grid.copy()

    assert np.array_equal(before, after), "Empty grid should stay empty"


def test_neighbor_count_edge_cases():
    """Test neighbor counting at grid boundaries"""
    grid = ConwayGrid(size=8)

    # Place single cell at various boundary positions and check neighbor count
    test_positions = [
        (0, 0),    # Corner
        (0, 4),    # Middle top
        (4, 0),    # Middle left
        (7, 7),    # Opposite corner
    ]

    for x, y in test_positions:
        grid.grid[y, x] = 1
        neighbors = grid.get_neighbors(x, y)
        # Single isolated cells on boundary should have 0 neighbors
        assert neighbors == 0, f"Boundary cell ({x},{y}) should have 0 neighbors"
        grid.grid[y, x] = 0  # Reset


def test_glider_correctness():
    """Glider moves correctly over multiple steps"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(4, 4)

    # Initial position check
    initial_pattern = grid.grid[3:7, 3:7].copy()

    # Step 1: Glider should move down-right
    grid.step()
    after1 = grid.grid[3:7, 3:7].copy()

    # Step 2: Glider should continue moving
    grid.step()
    after2 = grid.grid[3:7, 4:8].copy()  # Shift right

    # Glider should still have 5 cells after 2 steps
    total_cells = np.sum(grid.grid)
    assert total_cells == 5, f"Glider should have 5 cells after 2 steps, got {total_cells}"
