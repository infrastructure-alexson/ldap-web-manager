#!/usr/bin/env python3
"""Build ansible/inventory/group_vars/all/vault.yml from GITHUB_ENV."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"::error::Missing required env var {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> int:
    try:
        import yaml
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
        import yaml

    data = {
        "ldap_manager_database_password": _require("LDAP_MANAGER_DATABASE_PASSWORD"),
        "ldap_manager_redis_password": _require("LDAP_MANAGER_REDIS_PASSWORD"),
        "ldap_webmanager_password": _require("LDAP_WEBMANAGER_PASSWORD"),
        "ldap_manager_jwt_secret": _require("JWT_SECRET"),
        "ldap_manager_secret_key": _require("APP_SECRET_KEY"),
    }

    out = Path(os.environ.get("VAULT_OUTPUT", "inventory/group_vars/all/vault.yml"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    out.chmod(0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
