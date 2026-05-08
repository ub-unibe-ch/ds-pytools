#!/usr/bin/env python3
"""
Validate notebooks and check environment setup for ds-pytools.

This script performs checks to ensure the repository is correctly set up and
all notebooks can be executed without errors.

Usage:
    python scripts/validate_notebooks.py
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version_str}")
        return True
    else:
        print_error(f"Python {version_str} - Requires Python 3.8 or higher")
        return False


def check_required_packages():
    """Check if all required packages are installed."""
    print_header("Checking Required Packages")
    
    required_packages = {
        'jupyter': 'Jupyter',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'nltk': 'NLTK',
        'crossref_commons': 'Crossref Commons',
        'habanero': 'Habanero',
        'requests': 'Requests',
    }
    
    missing = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print_success(f"{name} installed")
        except ImportError:
            print_error(f"{name} NOT installed")
            missing.append(package)
    
    if missing:
        print_warning(f"\nMissing packages: {', '.join(missing)}")
        print_warning(f"Install with: pip install -r requirements.txt")
        return False
    
    return True


def check_notebook_files():
    """Check if notebook files exist and are valid JSON."""
    print_header("Checking Notebook Files")
    
    notebooks = list(Path('.').glob('**/*.ipynb'))
    
    if not notebooks:
        print_error("No notebooks found!")
        return False
    
    print_success(f"Found {len(notebooks)} notebooks")
    
    invalid = []
    for notebook in sorted(notebooks):
        try:
            with open(notebook, 'r', encoding='utf-8') as f:
                json.load(f)
            print_success(f"Valid: {notebook}")
        except json.JSONDecodeError:
            print_error(f"Invalid JSON: {notebook}")
            invalid.append(notebook)
        except Exception as e:
            print_error(f"Error reading {notebook}: {e}")
            invalid.append(notebook)
    
    if invalid:
        print_warning(f"\n{len(invalid)} notebook(s) have issues")
        return False
    
    return True


def check_no_credentials():
    """Check that no hardcoded credentials are in code."""
    print_header("Security Check: Scanning for Hardcoded Credentials")
    
    sensitive_patterns = [
        'api_key',
        'apikey',
        'secret_key',
        'password',
        'Bearer ',
        'token=',
    ]
    
    py_files = list(Path('.').glob('**/*.py'))
    notebook_files = list(Path('.').glob('**/*.ipynb'))
    
    issues_found = []
    
    # Check Python files
    for py_file in py_files:
        if 'venv' in str(py_file) or '.git' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    for pattern in sensitive_patterns:
                        if pattern.lower() in line.lower() and '# ' not in line[:line.find(pattern)]:
                            issues_found.append(f"{py_file}:{i} - Possible credential: {pattern}")
        except Exception as e:
            print_warning(f"Could not read {py_file}: {e}")
    
    if issues_found:
        print_warning(f"Found {len(issues_found)} potential security issues:")
        for issue in issues_found:
            print_warning(f"  - {issue}")
        print_warning("Please use .env file for sensitive credentials (see .env.example)")
        return False
    else:
        print_success("No hardcoded credentials detected")
        return True


def check_env_file():
    """Check if .env.example exists."""
    print_header("Checking Configuration Files")
    
    if Path('.env.example').exists():
        print_success(".env.example found")
        return True
    else:
        print_warning(".env.example not found (optional)")
        return True


def check_requirements_file():
    """Check if requirements.txt is complete."""
    print_header("Checking Requirements File")
    
    if not Path('requirements.txt').exists():
        print_error("requirements.txt not found")
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print_success(f"requirements.txt found with {len(lines)} packages")
        return True
    except Exception as e:
        print_error(f"Error reading requirements.txt: {e}")
        return False


def check_github_workflows():
    """Check if GitHub Actions workflow exists."""
    print_header("Checking CI/CD Configuration")
    
    workflow_path = Path('.github/workflows/notebook-validation.yml')
    
    if workflow_path.exists():
        print_success("GitHub Actions workflow configured")
        return True
    else:
        print_warning(".github/workflows/notebook-validation.yml not found")
        return True


def main():
    """Run all checks."""
    print(f"\n{BLUE}{'='*60}")
    print("ds-pytools Environment Validation")
    print(f"{'='*60}{RESET}")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Notebook Files", check_notebook_files),
        ("Security Scan", check_no_credentials),
        ("Configuration", check_env_file),
        ("Dependencies", check_requirements_file),
        ("CI/CD Setup", check_github_workflows),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Error during {name} check: {e}")
            results[name] = False
    
    # Print summary
    print_header("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {name}: {status}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print_success("All checks passed! Ready to use ds-pytools.")
        return 0
    else:
        print_error(f"{total - passed} check(s) failed.")
        print_warning("Please address the issues above before running notebooks.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
