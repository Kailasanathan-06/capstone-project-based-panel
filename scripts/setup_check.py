#!/usr/bin/env python3
"""SecureDT System Installation Checker.

Verifies that all required components are available for the
Intelligent and Secure Task Scheduling system.

Reports actual status - do not modify to hide failures.
"""

import os
import sys

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = BASE_DIR


def check_python():
    """Check Python version."""
    version = sys.version_info
    major, minor = version.major, version.minor
    ok = major >= 3 and minor >= 9
    msg = f"Python {major}.{minor}.{version.micro}"
    return ok, msg


def check_pip():
    """Check pip is available."""
    try:
        import subprocess
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, check=True,
        )
        return True, "pip available"
    except Exception as e:
        return False, f"pip failed: {e}"


def check_django():
    """Check Django is installed."""
    try:
        import django
        version = django.VERSION
        ok = version[0] >= 4
        msg = f"Django {version[0]}.{version[1]}.{version[2]}"
        return ok, msg
    except ImportError:
        return False, "Django not installed"


def check_mysql():
    """Check MySQL connector is available."""
    try:
        import pymysql
        return True, "PyMySQL available"
    except ImportError:
        try:
            import mysql.connector
            return True, "mysql-connector-python available"
        except ImportError:
            return False, "No MySQL connector installed"


def check_redis():
    """Check Redis is available (optional)."""
    try:
        import redis
        return True, "redis-py available"
    except ImportError:
        return True, "Redis (optional) - not installed, will use fallback"


def check_celery():
    """Check Celery is available (optional)."""
    try:
        import celery
        return True, f"Celery {celery.__version__} available"
    except ImportError:
        return True, "Celery (optional) - not installed, will use fallback"


def check_groq():
    """Check Groq SDK is available."""
    try:
        import groq
        return True, f"Groq SDK {groq.__version__} available"
    except ImportError:
        return False, "Groq SDK not installed (optional - local AI mode will be used)"


def check_ai_deps():
    """Check AI/ML dependencies."""
    import importlib
    deps = {
        "numpy": "numpy",
        "pandas": "pandas",
        "scikit-learn": "sklearn",
    }
    results = []
    all_ok = True
    for name, import_name in deps.items():
        try:
            importlib.import_module(import_name)
            results.append(f"OK {name}")
        except ImportError:
            all_ok = False
            results.append(f"FAIL {name} - missing")
    msg = "; ".join(results)
    if all_ok:
        return True, msg
    else:
        return False, msg


def check_groq_model_dir():
    """Check Groq model directory existence (not actual key)."""
    model_dir = os.path.join(BASE_DIR, "models")
    if os.path.isdir(model_dir):
        files = os.listdir(model_dir)
        return True, f"Model directory exists with {len(files)} file(s)"
    return False, "Model directory not found"


def check_dataset_dir():
    """Check dataset directories."""
    dataset_dir = os.path.join(BASE_DIR, "datasets")
    if os.path.isdir(dataset_dir):
        files = [f for f in os.listdir(dataset_dir) if f.endswith(".csv")]
        return True, f"Dataset directory exists with {len(files)} CSV file(s)"
    return False, "Dataset directory not found"


def check_pdf_deps():
    """Check PDF generation dependencies."""
    try:
        import reportlab
        return True, f"ReportLab {reportlab.__version__} available"
    except ImportError:
        return False, "ReportLab not available - PDF generation impaired"


def check_env_vars():
    """Check critical environment variables."""
    issues = []
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        issues.append("GROQ_API_KEY not set (optional - local AI mode active)")
    
    dj_key = os.environ.get("SECRET_KEY", "").strip()
    if not dj_key:
        issues.append("SECRET_KEY not set (using default)")
    
    if issues:
        return False, ". ".join(issues)
    return True, "All critical environment variables set"


def main():
    """Run all checks and display results."""
    checks = [
        ("Python", check_python),
        ("pip", check_pip),
        ("Django", check_django),
        ("MySQL", check_mysql),
        ("Redis", check_redis),
        ("Celery", check_celery),
        ("Groq SDK", check_groq),
        ("AI dependencies", check_ai_deps),
        ("Model directory", check_groq_model_dir),
        ("Dataset directory", check_dataset_dir),
        ("PDF dependencies", check_pdf_deps),
        ("Environment variables", check_env_vars),
    ]
    
    print("=" * 50)
    print("SYSTEM INSTALLATION CHECK")
    print("=" * 50)
    
    passed = 0
    failed = 0
    optional_failed = 0
    
    for name, check_func in checks:
        ok, message = check_func()
        
        # Optional checks: don't mark as failure
        if name in ("Redis", "Celery"):
            if not ok:
                optional_failed += 1
                print(f"  {name}: {message}")
            else:
                passed += 1
                print(f"  {name}: {message}")
        else:
            if ok:
                passed += 1
                print(f"  {name}: {message}")
            else:
                failed += 1
                print(f"  {name}: {message}")
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed, {optional_failed} optional issues")
    print("=" * 50)
    
    # Count only non-optional failures
    critical_failed = 0
    for name, check_func in checks:
        ok, message = check_func()
        if name in ("Redis", "Celery"):
            continue  # always optional
        if name == "Environment variables":
            # GROQ_API_KEY and SECRET_KEY are optional; local AI mode works without them
            continue
        if not ok:
            critical_failed += 1
    
    if critical_failed > 0:
        print("\nPlease fix the failed checks before proceeding.")
        return 1
    
    print("\nAll critical checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())