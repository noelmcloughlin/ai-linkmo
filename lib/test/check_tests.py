#!/usr/bin/env python3
"""Quick sanity check for test infrastructure.

This script validates that the test files are properly structured
without running the full test suite.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def check_imports():
    """Verify all test modules can be imported."""
    print("Checking test module imports...")
    
    try:
        # Check conftest can be imported
        import lib.test.conftest as conftest
        print("✓ conftest.py imports successfully")
        
        # Verify fixtures are defined
        assert hasattr(conftest, 'api_server'), "api_server fixture not found"
        assert hasattr(conftest, 'cli_command'), "cli_command fixture not found"
        print("✓ Test fixtures defined correctly")
        
    except ImportError as e:
        print(f"✗ Failed to import conftest: {e}")
        return False
    
    try:
        # Check test file can be imported
        import lib.test.test_cli_examples as tests
        print("✓ test_cli_examples.py imports successfully")
        
        # Verify test cases are defined
        assert hasattr(tests, 'CLI_TEST_CASES'), "CLI_TEST_CASES not found"
        assert len(tests.CLI_TEST_CASES) > 0, "No test cases defined"
        print(f"✓ Found {len(tests.CLI_TEST_CASES)} test cases")
        
    except ImportError as e:
        print(f"✗ Failed to import test_cli_examples: {e}")
        return False
    
    return True


def check_dependencies():
    """Check if required dependencies are available."""
    print("\nChecking dependencies...")
    
    required = ['pytest', 'requests', 'yaml']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"✓ {module} available")
        except ImportError:
            missing.append(module)
            print(f"✗ {module} not installed")
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: uv sync --extra test")
        return False
    
    return True


def check_cli():
    """Verify CLI script exists and is executable."""
    print("\nChecking CLI script...")
    
    cli_script = project_root / "ai"
    
    if not cli_script.exists():
        print(f"✗ CLI script not found at {cli_script}")
        return False
    
    print(f"✓ CLI script found at {cli_script}")
    
    if not cli_script.stat().st_mode & 0o111:
        print("⚠ CLI script not executable (run: chmod +x ai)")
    else:
        print("✓ CLI script is executable")
    
    return True


def check_openapi():
    """Verify OpenAPI spec exists."""
    print("\nChecking OpenAPI specification...")
    
    openapi_path = project_root / "lib" / "api" / "openapi.yaml"
    
    if not openapi_path.exists():
        print(f"✗ OpenAPI spec not found at {openapi_path}")
        return False
    
    print(f"✓ OpenAPI spec found at {openapi_path}")
    
    return True


def main():
    """Run all checks."""
    print("=" * 60)
    print("Test Infrastructure Sanity Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Imports", check_imports),
        ("Dependencies", check_dependencies),
        ("CLI Script", check_cli),
        ("OpenAPI Spec", check_openapi),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} check failed with exception: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✓ All checks passed! Test infrastructure is ready.")
        print("\nRun tests with:")
        print("  ,/tests.sh fast       # Quick API mode tests")
        print("  ,/tests.sh full       # Full test suite")
        return 0
    else:
        print("✗ Some checks failed. Review errors above.")
        print("\nQuick fix:")
        print("  uv sync --extra test")
        return 1


if __name__ == "__main__":
    sys.exit(main())
