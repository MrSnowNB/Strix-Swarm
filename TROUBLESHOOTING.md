# Phase 1A: Conway Grid Troubleshooting Guide

## Common Issues and Solutions

### Neighbor Calculation Errors
**Symptom:** Conway rules not applying correctly, patterns not evolving as expected.
**Cause:** Off-by-one errors in neighbor counting or wraparound logic.
**Solution:**
- Verify `get_neighbors` method correctly sums 8 surrounding cells
- Check toroidal wraparound: `(r + dr) % self.size`
- Test edge cases: corner cells should wrap to opposite side
- Run unit tests: `pytest tests/phase_1a/test_conway_core.py::TestConwayGrid::test_get_neighbors_wraparound`

### Glider Pattern Issues
**Symptom:** Glider doesn't move or evolves incorrectly.
**Cause:** Incorrect glider position seeding or evolution logic.
**Solution:**
- Confirm standard glider positions: relative (0,1),(1,2),(2,0),(2,1),(2,2)
- Verify offset application: `rr = (r + r_offset) % size`
- Check after evolution matches expected pattern
- Run: `pytest tests/phase_1a/test_glider_physics.py::TestGliderPhysics::test_glider_evolution_no_wraparound`

### Performance Below 100 steps/second
**Symptom:** Hardware validation fails with low steps/second.
**Cause:** Inefficient implementation or slow hardware.
**Solution:**
- Ensure numpy arrays used correctly
- Avoid Python loops over large ranges if possible
- Check CPU usage during run (should be <<50%)
- Run on physical hardware (not virtualized environment)
- Baseline environment: Windows 11, >3GHz CPU

### Memory Usage >50MB
**Symptom:** Hardware validation reports peak memory >50MB.
**Cause:** Memory leak or large data structures.
**Solution:**
- Verify only one ConwayGrid instance used
- Check numpy array cleanup in tests
- Memory leak test: `pytest tests/phase_1a/test_glider_physics.py::TestGliderPhysics::test_memory_leak_detection`
- Expected usage: ~29-30MB for process

### CPU Usage >50%
**Symptom:** System becomes sluggish during validation run.
**Cause:** Intensive computation blocking system.
**Solution:**
- Check for infinite loops in step() method
- Verify grid size is 8x8 (not accidentally larger)
- Run on idle system (close other CPU-intensive apps)
- Expected usage: <1% CPU (background process)

### Memory Leak >5MB
**Symptom:** Memory increases significantly over time.
**Cause:** Objects not garbage collected or cyclic references.
**Solution:**
- Ensure grid.reset() or new instances in loops (not reusing objects)
- Check for module-level global variables holding references
- Run memory tests: `pytest -m "memory"` if tagged

### Pytest Test Failures
**Symptom:** `pytest` reports failed tests (17 total).
**Common Causes:**
- Import path issues: run from project root
- Missing dependencies: `pip install numpy psutil pytest`
- Grid state not reset between tests
- Edge case wraparound: 8x8 toroidal boundary

**Solution:**
- `python -m pytest tests/phase_1a/ -v`
- Fix assertion errors based on output
- Common: glider positions after step incorrect

### Ruff Linting Errors
**Symptom:** `ruff check` reports unused imports/variables, syntax issues.
**Solution:**
- Remove unused `import pytest` in test files
- Remove unused variables (`delta = step()` -> `step()`)
- Run `ruff check --fix` to auto-fix safe issues

### MyPy Type Errors
**Symptom:** `mypy` reports type annotation issues.
**Common Causes:**
- Numpy array types not recognized
- Missing Optional/List/Set imports

**Solution:**
- Basic implementation uses int/numpy arrays, should pass
- If errors, add `# type: ignore` comments
- Run `mypy src/core/conway_grid.py`

### Hardware Validation Script Issues
**Symptom:** Script exits with code 1 or hangs.
**Cause:** Monitoring libraries incompatible or psutil errors.
**Solution:**
- Verify psutil works: `python -c "import psutil; print(psutil.virtual_memory())"`
- Check log file: `logs/phase_1a_validation.log`
- Ensure 30-second runtime completes without interruption
- Manual benchmark: run small loops and measure

### Import Errors
**Symptom:** `ModuleNotFoundError: No module named 'src'`
**Cause:** Running from wrong directory or PYTHONPATH unset.
**Solution:**
- Run commands from project root (`CPU Swarm/` folder)
- Set path in scripts: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))`

### Environment Validation
**Symptom:** Results not replicable on different hardware.
**Cause:** Virtual machines, containers, or insufficient hardware.
**Solution:**
- Must run on physical Windows 11 machine
- Minimum specs: 4GB RAM, 2GHz CPU
- No background processes interfering with CPU/memory monitoring

### Delta Tracking Issues
**Symptom:** `step()` method delta not tracking changes correctly.
**Cause:** Logic error in which cells are marked changed.
**Solution:**
- Delta should include cells that became alive or died
- Track before/after state comparison
- Used for optimization but not functional requirement

### Grid Initialization Problems
**Symptom:** Grid not starting in all-zero state or wrong size.
**Cause:** Default parameters or numpy version issues.
**Solution:**
- Check `np.zeros((size, size), dtype=int)`
- Ensure size=8 default
- `assert np.all(grid.grid == 0)`

### Pattern Seeding with Wraparound
**Symptom:** Glider offset not wrapping correctly at edges.
**Cause:** Arithmetic error in `(r + offset) % size`.
**Solution:**
- Verify modulo handles negative values correctly (Python ok)
- Test edge case: `r_offset=7, c_offset=7` on 8x8 grid
- Expected: wraps to opposite corners

## Escalation and Support
If all troubleshooting steps fail:
1. Verify exact Python version (3.12+)
2. Check Windows security/antivirus not blocking process monitoring
3. Ensure no power-saving modes interfering with performance
4. Capture full error logs and environment details
5. Review against REPLICATION-NOTES.md baseline metrics
