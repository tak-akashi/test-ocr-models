"""Timing and benchmarking utilities."""

import time
import json
from pathlib import Path
from datetime import datetime

from .logging import log, log_success


def measure_time(func, *args, **kwargs):
    """
    Measure execution time of a function.

    Args:
        func: Function to measure
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        tuple: (result, execution_time)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time


def save_timing_results(timing_data, output_dir="timing_results"):
    """
    Save timing results to JSON file.

    Args:
        timing_data: Dictionary containing timing data
        output_dir: Directory to save timing results

    Returns:
        Path: Path to saved JSON file
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"timing_results_{timestamp}.json"
    filepath = output_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(timing_data, f, ensure_ascii=False, indent=2)

    log_success(f"Timing results saved: {filepath}")
    return filepath


def print_timing_summary(timing_data):
    """
    Print summary of timing results.

    Args:
        timing_data: Dictionary containing timing data
    """
    log("=" * 60)
    log("Timing Summary")
    log("=" * 60)

    # Calculate statistics for each model
    model_stats = {}

    for result in timing_data["results"]:
        for model_name, model_data in result["models"].items():
            if model_name not in model_stats:
                model_stats[model_name] = {
                    "total_time": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "times": []
                }

            if model_data["status"] == "success":
                model_stats[model_name]["total_time"] += model_data["execution_time"]
                model_stats[model_name]["success_count"] += 1
                model_stats[model_name]["times"].append(model_data["execution_time"])
            else:
                model_stats[model_name]["error_count"] += 1

    # Display results
    for model_name, stats in model_stats.items():
        log(f"{model_name}:")
        log(f"  Success: {stats['success_count']} file(s)")
        log(f"  Errors: {stats['error_count']} file(s)")

        if stats["success_count"] > 0:
            avg_time = stats["total_time"] / stats["success_count"]
            min_time = min(stats["times"])
            max_time = max(stats["times"])
            log(f"  Average time: {avg_time:.2f}s")
            log(f"  Min time: {min_time:.2f}s")
            log(f"  Max time: {max_time:.2f}s")
            log(f"  Total time: {stats['total_time']:.2f}s")

    log("=" * 60)