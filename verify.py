#!/usr/bin/env python3
"""
Final Verification Script for SecureDT
Runs all checks to verify the system is working correctly.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_cmd(cmd, cwd=None):
    """Run command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR, 
                               capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def check_django_setup():
    """Verify Django configuration."""
    print("Checking Django setup...")
    
    # Check settings
    settings_path = BASE_DIR / "securedt" / "settings.py"
    if not settings_path.exists():
        return False, "settings.py not found"
    
    # Check apps
    required_apps = ['mec_manager', 'tasks', 'cloud', 'digital_twin', 'analytics']
    with open(settings_path) as f:
        content = f.read()
        for app in required_apps:
            if f'"{app}"' not in content and f"'{app}'" not in content:
                return False, f"App {app} not in INSTALLED_APPS"
    
    print("  [OK] Django settings configured")
    return True, ""


def check_models():
    """Check model files exist."""
    print("Checking model files...")
    
    models = [
        "secure/mec_manager/models.py",
        "secure/tasks/models.py",
        "secure/cloud/models.py",
    ]
    
    for model in models:
        path = BASE_DIR / model
        if not path.exists():
            return False, f"Missing model: {model}"
    
    print("  [OK] Model files present")
    return True, ""


def check_views():
    """Check view files exist."""
    print("Checking view files...")
    
    views = [
        "secure/mec_manager/views.py",
        "secure/tasks/views.py",
        "secure/cloud/views.py",
        "secure/digital_twin/views.py",
        "secure/analytics/views.py",
    ]
    
    for view in views:
        path = BASE_DIR / view
        if not path.exists():
            return False, f"Missing view: {view}"
    
    print("  [OK] View files present")
    return True, ""


def check_urls():
    """Check URL configuration."""
    print("Checking URL configuration...")
    
    urls = [
        "secure/mec_manager/urls.py",
        "secure/tasks/urls.py",
        "secure/cloud/urls.py",
        "secure/digital_twin/urls.py",
        "secure/analytics/urls.py",
    ]
    
    for url in urls:
        path = BASE_DIR / url
        if not path.exists():
            return False, f"Missing URLs: {url}"
    
    print("  [OK] URL files present")
    return True, ""


def check_templates():
    """Check template files."""
    print("Checking templates...")
    
    templates = [
        "templates/base.html",
        "templates/dashboard.html",
        "templates/task_routing.html",
        "templates/mec_infrastructure.html",
        "templates/digital_twin.html",
        "templates/genetic_algorithm.html",
        "templates/analytics.html",
        "templates/energy_monitor.html",
        "templates/security_monitor.html",
        "templates/attack_simulation.html",
        "templates/storage_attack.html",
        "templates/dataset_manager.html",
        "templates/cloud_storage.html",
        "templates/data_flow.html",
        "templates/ai_intelligence.html",
        "templates/performance.html",
    ]
    
    for template in templates:
        path = BASE_DIR / template
        if not path.exists():
            return False, f"Missing template: {template}"
    
    print("  [OK] All templates present")
    return True, ""


def check_static():
    """Check static files."""
    print("Checking static files...")
    
    static_files = [
        "static/css/style.css",
        "static/js/app.js",
    ]
    
    for static_file in static_files:
        path = BASE_DIR / static_file
        if not path.exists():
            return False, f"Missing static file: {static_file}"
    
    print("  [OK] Static files present")
    return True, ""


def check_mec_agent():
    """Check MEC agent files."""
    print("Checking MEC Agent...")
    
    agent_files = [
        "mec_agent/agent.py",
        "mec_agent/__init__.py",
        "mec_agent.spec",
        "build_mec_agent.bat",
    ]
    
    for agent_file in agent_files:
        path = BASE_DIR / agent_file
        if not path.exists():
            return False, f"Missing MEC agent file: {agent_file}"
    
    print("  [OK] MEC Agent files present")
    return True, ""


def check_docs():
    """Check documentation PDFs."""
    print("Checking documentation...")
    
    docs = [
        "docs/COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf",
        "docs/MEC_AGENT_INSTALLATION_AND_CONNECTION_GUIDE.pdf",
        "docs/GOOGLE_DRIVE_CLOUD_SETUP_GUIDE.pdf",
        "docs/DATASET_UPLOAD_AND_PROCESSING_GUIDE.pdf",
        "docs/AI_MODEL_INSTALLATION_AND_USAGE.pdf",
        "docs/GENETIC_ALGORITHM_GUIDE.pdf",
        "docs/DIGITAL_TWIN_ARCHITECTURE.pdf",
        "docs/SECURITY_ARCHITECTURE.pdf",
        "docs/DATA_FLOW_AND_COMMUNICATION.pdf",
        "docs/REVIEW_0_DOCUMENTATION.pdf",
    ]
    
    missing = []
    for doc in docs:
        path = BASE_DIR / doc
        if not path.exists():
            missing.append(doc)
    
    if missing:
        return False, f"Missing docs: {', '.join(missing)}"
    
    print("  [OK] All documentation PDFs generated")
    return True, ""


def check_engine():
    """Check engine files."""
    print("Checking engine modules...")
    
    engine_files = [
        "engine/digital_twin.py",
        "engine/genetic_algorithm.py",
        "engine/scheduler.py",
        "engine/risk_engine.py",
        "engine/attack_simulator.py",
        "engine/security_monitor.py",
        "engine/telemetry.py",
    ]
    
    for engine_file in engine_files:
        path = BASE_DIR / engine_file
        if not path.exists():
            return False, f"Missing engine file: {engine_file}"
    
    print("  [OK] Engine modules present")
    return True, ""


def check_requirements():
    """Check requirements.txt."""
    print("Checking requirements...")
    
    req_path = BASE_DIR / "requirements.txt"
    if not req_path.exists():
        return False, "requirements.txt not found"
    
    with open(req_path) as f:
        content = f.read()
        required = ['Django', 'djangorestframework', 'mysqlclient', 
                   'google-api-python-client', 'psutil', 'requests',
                   'chart.js', 'three']
        for req in required:
            if req.lower() not in content.lower():
                print(f"  [WARN] {req} not in requirements.txt")
    
    print("  [OK] Requirements file present")
    return True, ""


def check_env_example():
    """Check .env.example."""
    print("Checking .env.example...")
    
    env_path = BASE_DIR / ".env.example"
    if not env_path.exists():
        return False, ".env.example not found"
    
    print("  [OK] .env.example present")
    return True, ""


def check_readme():
    """Check README."""
    print("Checking README...")
    
    readme_path = BASE_DIR / "README.md"
    if not readme_path.exists():
        return False, "README.md not found"
    
    print("  [OK] README present")
    return True, ""


def run_django_check():
    """Run Django system check."""
    print("Running Django system check...")
    
    success, stdout, stderr = run_cmd("python manage.py check")
    if not success:
        return False, f"Django check failed: {stderr}"
    
    print("  [OK] Django check passed")
    return True, ""


def run_migrations_check():
    """Check migrations can be created."""
    print("Checking migrations...")
    
    success, stdout, stderr = run_cmd("python manage.py makemigrations --dry-run")
    if not success:
        return False, f"Migrations check failed: {stderr}"
    
    print("  [OK] Migrations check passed")
    return True, ""


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("SecureDT Final Verification")
    print("=" * 60)
    
    checks = [
        check_django_setup,
        check_models,
        check_views,
        check_urls,
        check_templates,
        check_static,
        check_mec_agent,
        check_docs,
        check_engine,
        check_requirements,
        check_env_example,
        check_readme,
        run_django_check,
        run_migrations_check,
    ]
    
    passed = 0
    failed = 0
    
    for check in checks:
        try:
            success, msg = check()
            if success:
                passed += 1
            else:
                failed += 1
                print(f"  [FAIL] {msg}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {check.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n[SUCCESS] All verification checks passed!")
        return 0
    else:
        print(f"\n[FAILURE] {failed} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())