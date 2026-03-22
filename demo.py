#!/usr/bin/env python3
"""
LexiData-Sentinel Demonstration Script
Runs all examples and shows the analyzer in action.
"""

import subprocess
import sys


def run_analysis(source_file, schema_file, description):
    """Run analysis and display results."""
    print("\n" + "=" * 80)
    print(f"DEMO: {description}")
    print("=" * 80)
    print(f"Analyzing: {source_file}")
    print(f"Schema: {schema_file}")
    print()
    
    result = subprocess.run(
        [sys.executable, "main.py", source_file, schema_file],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


def main():
    """Run all demonstrations."""
    print("=" * 80)
    print("LexiData-Sentinel: Complete Demonstration")
    print("=" * 80)
    print()
    print("This script demonstrates the static analyzer on various code examples.")
    print("Watch how it catches errors WITHOUT executing any code!")
    print()
    
    demos = [
        ("test_example.py", "schema.json", "Test File with Intentional Errors"),
        ("valid_example.py", "schema.json", "Valid Code with Minimal Issues"),
        ("edge_cases.py", "schema.json", "Edge Cases and Complex Scenarios"),
    ]
    
    results = []
    
    for source, schema, description in demos:
        returncode = run_analysis(source, schema, description)
        results.append((description, returncode))
        input("\nPress Enter to continue to next demo...")
    
    # Summary
    print("\n" + "=" * 80)
    print("DEMONSTRATION SUMMARY")
    print("=" * 80)
    print()
    
    for description, returncode in results:
        status = "✓ No errors" if returncode == 0 else "✗ Errors found"
        print(f"{status}: {description}")
    
    print()
    print("=" * 80)
    print("Run unit tests:")
    print("  python test_suite.py")
    print()
    print("Analyze your own code:")
    print("  python main.py <your_file.py> <your_schema.json>")
    print()
    print("For help:")
    print("  python main.py --help")
    print("=" * 80)


if __name__ == "__main__":
    main()
