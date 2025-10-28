import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.core.conway_grid import ConwayGrid


def test_glider_canonical_shape():
    """
    Verify glider matches canonical Conway glider:
      .X.
      ..X
      XXX

    At offset (1,1), this means cells at:
    (1,2), (2,3), (3,1), (3,2), (3,3)
    """
    grid = ConwayGrid(size=8)
    grid.seed_glider(r_offset=1, c_offset=1)

    # Expected live cells (row, col coordinates)
    expected = {
        (1, 2),  # 0+1, 1+1 = (1,2)
        (2, 3),  # 1+1, 2+1 = (2,3)
        (3, 1),  # 2+1, 0+1 = (3,1)
        (3, 2),  # 2+1, 1+1 = (3,2)
        (3, 3),  # 2+1, 2+1 = (3,3)
    }

    # Get actual live cells
    actual = set()
    for r in range(8):
        for c in range(8):
            if grid.grid[r, c] == 1:
                actual.add((r, c))

    assert actual == expected, \
        f"Glider shape incorrect.\nExpected: {expected}\nActual: {actual}"


def test_glider_has_five_cells():
    """Glider should always have exactly 5 cells"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(r_offset=2, c_offset=2)

    live_count = np.sum(grid.grid)
    assert live_count == 5, \
        f"Glider should have 5 cells, has {live_count}"


def test_glider_period_four():
    """
    Glider returns to same shape after 4 steps (period-4)
    but shifted by (+1, +1)
    """
    grid = ConwayGrid(size=16)  # Larger grid to prevent edge effects
    grid.seed_glider(r_offset=4, c_offset=4)

    # Get initial live cells (relative positions)
    initial_cells = set()
    for r in range(16):
        for c in range(16):
            if grid.grid[r, c] == 1:
                initial_cells.add((c, r))  # x,y = col,row

    # Calculate center of mass
    initial_cx = np.mean([c[0] for c in initial_cells])
    initial_cy = np.mean([c[1] for c in initial_cells])

    # Run 4 steps
    for _ in range(4):
        grid.step()

    # Get cells after 4 steps
    final_cells = set()
    for r in range(16):
        for c in range(16):
            if grid.grid[r, c] == 1:
                final_cells.add((c, r))  # x,y = col,row

    # Calculate new center of mass
    final_cx = np.mean([c[0] for c in final_cells])
    final_cy = np.mean([c[1] for c in final_cells])

    # Should have moved by approximately (+1, +1)
    dx = final_cx - initial_cx
    dy = final_cy - initial_cy

    assert 0.8 < dx < 1.2, f"Glider should move +1 in x after 4 steps, moved {dx}"
    assert 0.8 < dy < 1.2, f"Glider should move +1 in y after 4 steps, moved {dy}"

    # Should still have 5 cells
    assert len(final_cells) == 5, \
        f"Glider should maintain 5 cells, has {len(final_cells)}"


def test_glider_trajectory_diagonal():
    """Glider should move diagonally (down-right)"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(r_offset=2, c_offset=2)

    # Track center of mass over 20 steps
    positions = []
    for i in range(20):
        live_cells = np.argwhere(grid.grid == 1)
        if len(live_cells) > 0:
            cx = np.mean(live_cells[:, 1])  # x coordinate
            cy = np.mean(live_cells[:, 0])  # y coordinate
            positions.append((cx, cy))
        grid.step()

    # Verify consistent diagonal movement
    initial = positions[0]
    final = positions[-1]

    dx = final[0] - initial[0]
    dy = final[1] - initial[1]

    # Should move diagonally: dx ≈ dy and both positive
    assert dx > 2, f"Glider should move right, dx={dx}"
    assert dy > 2, f"Glider should move down, dy={dy}"
    assert 0.8 < dx/dy < 1.2, \
        f"Glider should move diagonally (dx≈dy), but dx={dx}, dy={dy}"


def test_glider_survives_50_generations():
    """Glider should survive at least 50 generations without dying"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(r_offset=4, c_offset=4)

    for i in range(50):
        live_count = np.sum(grid.grid)
        assert live_count > 0, \
            f"Glider died at generation {i}"
        grid.step()

    # Final check
    final_count = np.sum(grid.grid)
    assert final_count == 5, \
        f"Glider should have 5 cells after 50 steps, has {final_count}"


def test_glider_never_exceeds_five_cells():
    """During evolution, glider should never have more than 5 cells"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(r_offset=4, c_offset=4)

    for i in range(100):
        live_count = np.sum(grid.grid)
        assert live_count <= 5, \
            f"Glider has {live_count} cells at step {i}, should never exceed 5"
        grid.step()
