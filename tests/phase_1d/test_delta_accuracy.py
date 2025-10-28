import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.core.conway_grid import ConwayGrid





def test_no_false_deltas():
    """Deltas should not report changes for unchanged cells"""
    grid = ConwayGrid(size=8)

    # Create stable block pattern
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1

    deltas = grid.step()

    # Block is stable, should have zero deltas
    assert len(deltas) == 0, \
        f"Stable pattern should have 0 deltas, got {len(deltas)}: {deltas}"


def test_delta_coordinates_valid():
    """All delta coordinates should be within grid bounds"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(r_offset=1, c_offset=1)

    for _ in range(10):
        deltas = grid.step()
        for delta in deltas:
            assert 0 <= delta['x'] < 8, f"Delta x-coordinate out of bounds: {delta['x']}"
            assert 0 <= delta['y'] < 8, f"Delta y-coordinate out of bounds: {delta['y']}"


def test_delta_structure_complete():
    """Delta objects should have all required attributes"""
    grid = ConwayGrid(size=8)
    grid.grid[1, 1] = 1  # Single cell to create a change

    deltas = grid.step()

    # There should be changes (center died, possibly neighbors were born)
    assert len(deltas) > 0, "Single live cell should produce state changes"

    for delta in deltas:
        # Check delta has required keys
        assert 'x' in delta, f"Delta missing x key: {delta}"
        assert 'y' in delta, f"Delta missing y key: {delta}"
        assert 'alive' in delta, f"Delta missing alive key: {delta}"

        # Check alive is boolean-like
        assert isinstance(delta['alive'], (int, bool)), f"Delta alive should be int/bool: {delta['alive']}"
        assert delta['alive'] in [0, 1, True, False], f"Delta alive should be 0/1: {delta['alive']}"


def test_empty_grid_no_deltas():
    """Empty grid should produce no deltas"""
    grid = ConwayGrid(size=8)

    deltas = grid.step()

    assert len(deltas) == 0, \
        f"Empty grid should have 0 deltas, got {len(deltas)}"


def test_full_grid_has_deltas():
    """Full grid should produce deltas (most cells die)"""
    grid = ConwayGrid(size=8)
    grid.grid.fill(1)  # All cells alive

    deltas = grid.step()

    # In a full 8x8 grid, most cells will die from overpopulation
    assert len(deltas) > 0, \
        f"Full grid should produce deltas (cells dying), got {len(deltas)}"

    # All deltas should be for death (alive=False/0)
    for delta in deltas:
        assert delta['alive'] == 0, \
            f"Full grid deltas should all be deaths (alive=0), got alive={delta['alive']}"
