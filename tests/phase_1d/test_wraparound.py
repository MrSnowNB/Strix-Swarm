import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.core.conway_grid import ConwayGrid


def test_wraparound_top_bottom():
    """Verify neighbor counting wraps from top to bottom"""
    grid = ConwayGrid(size=8)

    # Place live cells at top and bottom edges
    grid.grid[0, 3] = 1  # Top edge, column 3
    grid.grid[7, 3] = 1  # Bottom edge, column 3

    # Count neighbors of top cell (should see bottom cell)
    neighbors_top = grid.get_neighbors(0, 3)

    # Count neighbors of bottom cell (should see top cell)
    neighbors_bottom = grid.get_neighbors(7, 3)

    # Each should see the other as neighbor
    assert neighbors_top >= 1, "Top cell should see bottom cell as neighbor (wraparound)"
    assert neighbors_bottom >= 1, "Bottom cell should see top cell as neighbor (wraparound)"


def test_wraparound_left_right():
    """Verify neighbor counting wraps from left to right"""
    grid = ConwayGrid(size=8)

    # Place live cells at left and right edges
    grid.grid[3, 0] = 1  # Left edge, row 3
    grid.grid[3, 7] = 1  # Right edge, row 3

    neighbors_left = grid.get_neighbors(3, 0)
    neighbors_right = grid.get_neighbors(3, 7)

    assert neighbors_left >= 1, "Left cell should see right cell (wraparound)"
    assert neighbors_right >= 1, "Right cell should see left cell (wraparound)"


def test_wraparound_corner():
    """Verify corner cell sees opposite corner as neighbor"""
    grid = ConwayGrid(size=8)

    # Place live cells at opposite corners
    grid.grid[0, 0] = 1  # Top-left
    grid.grid[7, 7] = 1  # Bottom-right

    # Top-left should see bottom-right as diagonal neighbor
    neighbors = grid.get_neighbors(0, 0)

    assert neighbors >= 1, \
        "Corner wraparound failed: (0,0) should see (7,7) as diagonal neighbor"


def test_glider_survives_edge_crossing():
    """Glider should survive crossing edges"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(r_offset=6, c_offset=1)  # Place near right edge

    # Count initial cells
    initial_count = np.sum(grid.grid)
    assert initial_count == 5, f"Initial glider should have 5 cells, has {initial_count}"

    # Run until glider crosses edge
    for _ in range(20):
        grid.step()

    # Glider should still exist
    live_count = np.sum(grid.grid)
    assert live_count >= 5, \
        f"Glider died crossing edge: only {live_count} cells remain"


def test_wraparound_preserves_pattern():
    """Pattern shape should be preserved through wraparound"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(r_offset=6, c_offset=6)  # Near bottom-right corner

    # Track cell count through multiple steps
    counts = []
    for _ in range(30):
        counts.append(np.sum(grid.grid))
        grid.step()

    # Cell count should remain 5 (allowing brief fluctuations during phase transitions)
    stable_counts = [c for c in counts if c == 5]

    assert len(stable_counts) > 20, \
        f"Glider unstable during wraparound: counts were {set(counts)}"


def test_wraparound_neighborhood_complete():
    """Verify all 8 toroidal neighbors are counted correctly"""
    grid = ConwayGrid(size=8)

    # Set all cells around a center cell to alive (using toroidal wraparound)
    center_r, center_c = 4, 4

    # Set all 8 neighbors (accounting for wraparound)
    neighbors_pos = [
        ((center_r-1) % 8, (center_c-1) % 8),  # North-west
        ((center_r-1) % 8, center_c),          # North
        ((center_r-1) % 8, (center_c+1) % 8),  # North-east
        (center_r, (center_c-1) % 8),          # West
        (center_r, (center_c+1) % 8),          # East
        ((center_r+1) % 8, (center_c-1) % 8),  # South-west
        ((center_r+1) % 8, center_c),          # South
        ((center_r+1) % 8, (center_c+1) % 8),  # South-east
    ]

    for nr, nc in neighbors_pos:
        grid.grid[nr, nc] = 1

    neighbors_count = grid.get_neighbors(center_r, center_c)
    assert neighbors_count == 8, \
        f"Center cell should have 8 neighbors in toroidal space, got {neighbors_count}"


def test_edge_cell_neighbor_count():
    """Edge cells should count neighbors that wrap around"""
    grid = ConwayGrid(size=8)

    # Test top-left corner (0,0) neighbor count
    # Should see: (7,7), (7,0), (7,1), (0,7), (0,1), (1,7), (1,0), (1,1)
    # Set some of these to alive
    grid.grid[7, 7] = 1  # opposite corner
    grid.grid[7, 0] = 1  # bottom same column
    grid.grid[0, 7] = 1  # right same row
    grid.grid[1, 1] = 1  # down-right adjacent

    neighbors_00 = grid.get_neighbors(0, 0)
    assert neighbors_00 == 4, \
        f"Corner cell (0,0) should have 4 live neighbors (considering only set ones), got {neighbors_00}"
