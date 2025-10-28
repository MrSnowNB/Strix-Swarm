import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.core.conway_grid import ConwayGrid


def test_birth_rule_exactly_three_neighbors():
    """
    Conway Rule: Dead cell with exactly 3 live neighbors becomes alive

    Setup:
      . X .
      X . X
      . . .

    Center cell (1,1) has 3 neighbors, should become alive
    """
    grid = ConwayGrid(size=5)

    # Dead center with 3 neighbors
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    grid.grid[1, 2] = 1  # East
    grid.grid[1, 1] = 0  # Center (dead)

    # Step
    grid.step()

    # Center should now be alive
    assert grid.grid[1, 1] == 1, \
        "Birth rule failed: dead cell with 3 neighbors should become alive"


def test_birth_rule_not_two_neighbors():
    """Dead cell with 2 neighbors should stay dead"""
    grid = ConwayGrid(size=5)

    # Dead center with 2 neighbors
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    grid.grid[1, 1] = 0  # Center (dead)

    grid.step()

    # Center should stay dead
    assert grid.grid[1, 1] == 0, \
        "Cell with 2 neighbors should not be born"


def test_survival_rule_two_neighbors():
    """Live cell with 2 neighbors survives"""
    grid = ConwayGrid(size=5)

    # Live center with 2 neighbors
    grid.grid[1, 1] = 1  # Center (alive)
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West

    grid.step()

    # Center should survive
    assert grid.grid[1, 1] == 1, \
        "Survival rule failed: live cell with 2 neighbors should survive"


def test_survival_rule_three_neighbors():
    """Live cell with 3 neighbors survives"""
    grid = ConwayGrid(size=5)

    # Live center with 3 neighbors
    grid.grid[1, 1] = 1  # Center (alive)
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    grid.grid[1, 2] = 1  # East

    grid.step()

    # Center should survive
    assert grid.grid[1, 1] == 1, \
        "Survival rule failed: live cell with 3 neighbors should survive"


def test_death_underpopulation_zero_neighbors():
    """Live cell with 0 neighbors dies (underpopulation)"""
    grid = ConwayGrid(size=5)

    # Single live cell, isolated
    grid.grid[2, 2] = 1

    grid.step()

    # Should die
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: isolated cell should die from underpopulation"


def test_death_underpopulation_one_neighbor():
    """Live cell with 1 neighbor dies (underpopulation)"""
    grid = ConwayGrid(size=5)

    # Live cell with 1 neighbor
    grid.grid[2, 2] = 1  # Center
    grid.grid[2, 3] = 1  # One neighbor

    grid.step()

    # Both should die (each has only 1 neighbor)
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: cell with 1 neighbor should die"
    assert grid.grid[2, 3] == 0, \
        "Death rule failed: cell with 1 neighbor should die"


def test_death_overpopulation_four_neighbors():
    """Live cell with 4 neighbors dies (overpopulation)"""
    grid = ConwayGrid(size=5)

    # Center with 4 neighbors
    grid.grid[2, 2] = 1  # Center
    grid.grid[1, 2] = 1  # North
    grid.grid[3, 2] = 1  # South
    grid.grid[2, 1] = 1  # West
    grid.grid[2, 3] = 1  # East

    grid.step()

    # Center should die from overpopulation
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: cell with 4 neighbors should die from overpopulation"


def test_death_overpopulation_eight_neighbors():
    """Live cell with 8 neighbors (surrounded) dies"""
    grid = ConwayGrid(size=8)

    # Center surrounded by 8 neighbors (need larger grid)
    center_y, center_x = 4, 4
    grid.grid[center_y, center_x] = 1
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            grid.grid[center_y + dy, center_x + dx] = 1

    grid.step()

    # Center should die
    assert grid.grid[center_y, center_x] == 0, \
        "Death rule failed: cell with 8 neighbors should die"


def test_stable_block_pattern():
    """
    Block pattern (2x2) should be stable (still life)

    XX
    XX

    Each cell has 3 neighbors, all survive
    """
    grid = ConwayGrid(size=6)

    # Create block at center
    grid.grid[2, 2] = 1
    grid.grid[2, 3] = 1
    grid.grid[3, 2] = 1
    grid.grid[3, 3] = 1

    initial = grid.grid.copy()

    # Step multiple times
    for _ in range(5):
        grid.step()

    # Block should be unchanged
    assert np.array_equal(grid.grid, initial), \
        "Block pattern should be stable (still life), but changed"


def test_no_false_birth():
    """Dead cells should not be born unless exactly 3 neighbors"""
    grid = ConwayGrid(size=5)

    # Set up dead cell with 4 neighbors (too many)
    dead_y, dead_x = 2, 2
    grid.grid[dead_y, dead_x] = 0  # Ensure dead

    # Give it 4 neighbors (should not be born)
    grid.grid[1, 2] = 1  # North
    grid.grid[3, 2] = 1  # South
    grid.grid[2, 1] = 1  # West
    grid.grid[2, 3] = 1  # East

    grid.step()

    # Should stay dead
    assert grid.grid[dead_y, dead_x] == 0, \
        "Dead cell with 4 neighbors should not be born"


def test_death_by_overpopulation_six_neighbors():
    """Live cell with 6 neighbors dies (overpopulation)"""
    grid = ConwayGrid(size=5)

    # Center cell with 6 neighbors (hexagon pattern)
    grid.grid[2, 2] = 1  # Center
    grid.grid[1, 2] = 1  # North
    grid.grid[3, 2] = 1  # South
    grid.grid[2, 1] = 1  # West
    grid.grid[2, 3] = 1  # East
    grid.grid[1, 1] = 1  # Northwest
    grid.grid[1, 3] = 1  # Northeast

    grid.step()

    # Center should die from overpopulation
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: cell with 6 neighbors should die from overpopulation"
