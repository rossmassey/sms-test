#!/usr/bin/env python3
"""
Test runner script for the SMS Outreach Backend.
Provides different test execution options.
"""

import subprocess
import sys
import argparse

def run_tests(test_type="all", verbose=True, coverage=False):
    """Run tests based on the specified type."""
    
    base_cmd = ["python", "-m", "pytest"]
    
    if verbose:
        base_cmd.append("-v")
    
    if coverage:
        base_cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    # Test type configurations
    test_configs = {
        "unit": {
            "paths": ["tests/test_main.py", "tests/test_unit_mocked.py", "tests/test_utils.py"],
            "markers": []
        },
        "integration": {
            "paths": ["tests/test_integration_real.py"],
            "markers": []
        },
        "performance": {
            "paths": ["tests/test_performance.py"],
            "markers": []
        },
        "all": {
            "paths": ["tests/test_main.py", "tests/test_unit_mocked.py", "tests/test_utils.py", "tests/test_integration_real.py"],
            "markers": []
        },
        "quick": {
            "paths": ["tests/test_main.py", "tests/test_unit_mocked.py", "tests/test_utils.py"],
            "markers": []
        },
        "api": {
            "paths": ["tests/test_main.py"],
            "markers": ["-k", "test_customer or test_message or test_health"]
        }
    }
    
    if test_type not in test_configs:
        print(f"Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_configs.keys())}")
        return False
    
    config = test_configs[test_type]
    cmd = base_cmd + config["paths"] + config["markers"]
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="SMS Outreach Backend Test Runner")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="quick",
        choices=["unit", "integration", "performance", "all", "quick", "api"],
        help="Type of tests to run (default: quick)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default: True)"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet output (overrides verbose)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running"
    )
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    verbose = args.verbose and not args.quiet
    
    success = run_tests(
        test_type=args.test_type,
        verbose=verbose,
        coverage=args.coverage
    )
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
