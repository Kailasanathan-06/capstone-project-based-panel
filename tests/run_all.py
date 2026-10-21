"""Runs the SecureDT test suite via Django's test runner.

Requires the MySQL service and a working database connection:
    python tests/run_all.py
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    env = os.environ.copy()
    env.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,127.0.0.1,localhost")
    rc = subprocess.call([sys.executable, "manage.py", "test", "tests", "-v", "2"], cwd=ROOT, env=env)
    return rc


if __name__ == "__main__":
    sys.exit(main())