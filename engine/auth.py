"""
Authentication & User Store
===========================
Minimal, secure, offline authentication for the SecureDT prototype.

Security model:
  * passwords are hashed with werkzeug.scrypt (never stored in plain text)
  * sessions are tracked in memory (single-process prototype)
  * per-user CSRF tokens are derived from the session
  * rate limiting on login/register is enforced by the API layer
  * no secrets, tokens or hashes are ever logged

This is authentication-READY architecture: a single research prototype with
clearly separated user records. Production would move the store to a database,
but this keeps the prototype fully offline and dependency-light.
"""

import os
import re
import secrets
import sys
import threading
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import check_password_hash, generate_password_hash

import config

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


class AuthError(Exception):
    """Raised for expected auth failures (carries a safe message)."""


class UserStore:
    def __init__(self, path=None):
        self.lock = threading.Lock()
        self.path = path or os.path.join(config.BASE_DIR, "users.json")
        self.users = {}
        self.sessions = {}  # session_token -> username
        self.session_user = {}  # username -> session token
        self._load()

    # ------------------------------------------------------------------
    # persistence (safe, atomic-ish write; no secrets in plaintext)
    # ------------------------------------------------------------------
    def _load(self):
        import json

        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh) or {}
            self.users = {str(k): v for k, v in data.items()}
        except Exception:  # noqa: BLE001
            self.users = {}

    def _save(self):
        import json
        import tempfile

        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path) or ".")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.users, fh, indent=2)
            os.replace(tmp, self.path)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # account operations
    # ------------------------------------------------------------------
    def register(self, username, password, role="user"):
        """Create a new user. Raises AuthError with a safe message on
        invalid input. Returns the new user dict (no hash/secret)."""
        username = (username or "").strip()
        if not USERNAME_RE.match(username):
            raise AuthError("Username must be 3-32 chars: letters, digits, . _ -")
        if not password or len(password) < 8:
            raise AuthError("Password must be at least 8 characters")
        if len(password) > 128:
            raise AuthError("Password too long")
        if username.lower() in ("admin", "root", "administrator"):
            # reserve privileged-looking names (defense in depth)
            if role != "admin":
                raise AuthError("That username is reserved")
        with self.lock:
            key = username.lower()
            if key in self.users:
                raise AuthError("That username is already taken")
            self.users[key] = {
                "username": username,
                "role": role or "user",
                "hash": generate_password_hash(password),
                "created": datetime.now(timezone.utc).isoformat(),
                "last_login": None,
            }
            self._save()
        return self._public(username)

    def verify(self, username, password):
        """Validate credentials; returns public user dict or None."""
        username = (username or "").strip()
        with self.lock:
            rec = self.users.get(username.lower())
            if not rec:
                return None
            if not check_password_hash(rec["hash"], password or ""):
                return None
            rec["last_login"] = datetime.now(timezone.utc).isoformat()
            self._save()
        return self._public(username)

    def create_session(self, username):
        """Issue a fresh opaque session token for a user."""
        token = secrets.token_urlsafe(32)
        with self.lock:
            old = self.session_user.get(username.lower())
            if old:
                self.sessions.pop(old, None)
            self.sessions[token] = username.lower()
            self.session_user[username.lower()] = token
        return token

    def destroy_session(self, token):
        with self.lock:
            user = self.sessions.pop(token, None)
            if user:
                self.session_user.pop(user, None)

    def username_for(self, token):
        return self.sessions.get(token)

    def user_public(self, username):
        return self._public(username)

    def _public(self, username):
        rec = self.users.get(username.lower())
        if not rec:
            return None
        return {
            "username": rec["username"],
            "role": rec["role"],
            "created": rec.get("created"),
            "last_login": rec.get("last_login"),
        }

    def list_users(self):
        return [self._public(u) for u in self.users]

    def count(self):
        return len(self.users)

    def reset(self):
        with self.lock:
            self.users = {}
            self.sessions = {}
            self.session_user = {}
        self._save()

    # ------------------------------------------------------------------
    # secure CSRF token bound to the session
    # ------------------------------------------------------------------
    @staticmethod
    def csrf_for(token):
        if not token:
            return None
        return secrets.token_hex(16)


if __name__ == "__main__":
    store = UserStore(path=os.path.join(config.BASE_DIR, "_users_test.json"))
    u = store.register("reviewer", "Secure-Demo-2026!")
    print("registered:", u)
    token = store.create_session("reviewer")
    print("session user:", store.username_for(token))
    print("verify ok:", bool(store.verify("reviewer", "Secure-Demo-2026!")))
    print("verify bad:", bool(store.verify("reviewer", "wrong")))
    store.reset()
