#!/usr/bin/env python3
"""
Test runner script for the SMS Outreach Backend.
Runs test suites based on category flags or all tests by default.
"""

import subprocess
import sys
import time
import argparse
from typing import List, Tuple


def run_command(cmd: List[str], suite_name: str) -> Tuple[bool, float]:
    """Run a command and return success status and execution time."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {suite_name}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=False)
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ {suite_name} PASSED ({execution_time:.2f}s)")
            return True, execution_time
        else:
            print(f"\n❌ {suite_name} FAILED ({execution_time:.2f}s)")
            return False, execution_time
            
    except KeyboardInterrupt:
        print(f"\n⚠️  {suite_name} interrupted by user")
        return False, time.time() - start_time
    except Exception as e:
        print(f"\n💥 {suite_name} crashed: {e}")
        return False, time.time() - start_time


def get_test_suites():
    """Define all available test suites."""
    return {
        "unit": [
            {
                "name": "Unit Tests (Core API & Auth)",
                "cmd": ["python3", "-m", "pytest", "tests/test_main.py", "-v"]
            },
            {
                "name": "Unit Tests (New SMS Endpoints)",
                "cmd": ["python3", "-m", "pytest", "tests/test_unit_mocked.py", "-v"]
            }
        ],
        "integration": [
            {
                "name": "Integration Tests (Graceful)",
                "cmd": ["python3", "-m", "pytest", "tests/test_integration.py", "-v"]
            },
            {
                "name": "Integration Tests (Real Services)",
                "cmd": ["python3", "-m", "pytest", "tests/test_integration_real.py", "-v"]
            }
        ],
        "utils": [
            {
                "name": "Utility and Validation Tests",
                "cmd": ["python3", "-m", "pytest", "tests/test_utils.py", "-v"]
            }
        ],
        "performance": [
            {
                "name": "Performance Tests",
                "cmd": ["python3", "-m", "pytest", "tests/test_performance.py", "-v"]
            }
        ]
    }

def main():
    """Run test suites based on arguments."""
    parser = argparse.ArgumentParser(description="SMS Outreach Backend Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only (fast, mocked)")
    parser.add_argument("--integration-graceful", action="store_true", help="Run graceful integration tests (works without external services)")
    parser.add_argument("--integration-real", action="store_true", help="Run real integration tests (requires API keys)")
    parser.add_argument("--utils", action="store_true", help="Run utility tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed test output")
    
    args = parser.parse_args()
    
    # Determine which test suites to run
    all_suites = get_test_suites()
    selected_suites = []
    
    if args.unit:
        selected_suites.extend(all_suites["unit"])
    if args.integration_graceful:
        selected_suites.append(all_suites["integration"][0])  # Graceful only
    if args.integration_real:
        selected_suites.append(all_suites["integration"][1])  # Real only
    if args.utils:
        selected_suites.extend(all_suites["utils"])
    if args.performance:
        selected_suites.extend(all_suites["performance"])
    
    # If no specific flags, run a sensible default for development
    if not any([args.unit, args.integration_graceful, args.integration_real, args.utils, args.performance]):
        print("🚀 SMS Outreach Backend Test Runner")
        print("Running default development suite: Unit + Graceful Integration + Utils")
        print("(Use --help for specific categories)")
        selected_suites.extend(all_suites["unit"])
        selected_suites.append(all_suites["integration"][0])  # Graceful only
        selected_suites.extend(all_suites["utils"])
    else:
        print("🚀 SMS Outreach Backend Test Runner")
        categories = []
        if args.unit: categories.append("Unit")
        if args.integration_graceful: categories.append("Integration (Graceful)")
        if args.integration_real: categories.append("Integration (Real)")
        if args.utils: categories.append("Utils")
        if args.performance: categories.append("Performance")
        print(f"Running {', '.join(categories)} tests only")
    
    results = []
    total_start_time = time.time()
    
    # Run each test suite separately
    for suite in selected_suites:
        success, execution_time = run_command(suite["cmd"], suite["name"])
        results.append({
            "name": suite["name"],
            "success": success,
            "time": execution_time
        })
    
    total_time = time.time() - total_start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status:<10} {result['name']:<35} ({result['time']:.2f}s)")
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"🎯 FINAL RESULTS:")
    print(f"   Total Suites: {len(results)}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"{'='*60}")
    
    if failed == 0:
        print("🎉 ALL TEST SUITES PASSED! 🎉")
        return 0
    else:
        print(f"💥 {failed} TEST SUITE(S) FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 