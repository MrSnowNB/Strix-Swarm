#!/usr/bin/env python3
"""
Phase 1A Hardware Validation Script
Runs Conway's Game of Life simulation for 30 seconds and monitors hardware metrics.
Validates memory <50MB, CPU <50%, >100 steps/sec, memory leak <5MB.
Generates validation log.
"""

import time
import psutil
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.conway_grid import ConwayGrid

def log_message(message, log_file):
    """Log message to console and file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    log_file.write(log_entry + "\n")

def main():
    log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'phase_1a_validation.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, 'w') as log_file:
        log_message("Starting Phase 1A Hardware Validation", log_file)
        log_message("Conway's Game of Life 8x8 Grid - Glider Pattern", log_file)

        # Get process for monitoring
        process = psutil.Process()
        initial_mem = process.memory_info().rss / (1024 * 1024)  # MB
        log_message(f"Initial memory: {initial_mem:.2f} MB", log_file)

        # Initialize grid
        grid = ConwayGrid()
        grid.seed_glider()
        log_message("Glider pattern seeded", log_file)

        # Validation parameters
        duration_sec = 30
        log_interval = 5  # log every 5 seconds

        # Tracking
        total_steps = 0
        peaks = {
            'memory_mb': 0,
            'cpu_percent': 0
        }
        last_log_time = time.time()

        start_time = time.time()
        end_time = start_time + duration_sec

        log_message(f"Running simulation for {duration_sec} seconds", log_file)

        while time.time() < end_time:
            # Perform step
            grid.step()
            total_steps += 1

            # Periodic logging
            current_time = time.time()
            if current_time - last_log_time >= log_interval:
                mem_mb = process.memory_info().rss / (1024 * 1024)
                cpu_pct = process.cpu_percent(interval=0.1)
                peaks['memory_mb'] = max(peaks['memory_mb'], mem_mb)
                peaks['cpu_percent'] = max(peaks['cpu_percent'], cpu_pct)

                log_message(f"Steps: {total_steps}, Memory: {mem_mb:.2f} MB, CPU: {cpu_pct:.2f}%", log_file)
                last_log_time = current_time

        # Final measurements
        final_time = time.time()
        elapsed = final_time - start_time
        steps_per_sec = total_steps / elapsed
        final_mem_mb = process.memory_info().rss / (1024 * 1024)
        memory_leak_mb = final_mem_mb - initial_mem

        log_message(f"Simulation completed: {total_steps} steps in {elapsed:.2f} seconds", log_file)
        log_message(f"Performance: {steps_per_sec:.2f} steps/second", log_file)
        log_message(f"Peak Memory: {peaks['memory_mb']:.2f} MB", log_file)
        log_message(f"Peak CPU: {peaks['cpu_percent']:.2f}%", log_file)
        log_message(f"Memory Leak: {memory_leak_mb:.2f} MB", log_file)

        # Validation checks
        failures = []
        if peaks['memory_mb'] >= 50.0:
            failures.append(".2f")
        if peaks['cpu_percent'] >= 50.0:
            failures.append(".2f")
        if steps_per_sec <= 100.0:
            failures.append(".2f")
        if memory_leak_mb >= 5.0:
            failures.append(".2f")

        if failures:
            log_message("VALIDATION FAILED:", log_file)
            for fail in failures:
                log_message(f"  - {fail}", log_file)
            return 1  # Exit code for failure
        else:
            log_message("VALIDATION PASSED: All metrics within limits", log_file)
            return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
