#!/usr/bin/env python3
"""Create (or promote) an admin user.

Usage:
    uv run python scripts/create_admin.py admin@example.com secret1234 --name "Admin"
"""
from __future__ import annotations

import argparse
import sys

from modules.users.domain.entities.user import UserRole
from modules.users.domain.exceptions import EmailAlreadyRegisteredError, UserNotFoundError
from modules.users.application.services.user_service import UserService


def create_admin(email: str, password: str, display_name: str = "") -> None:
    svc = UserService()
    try:
        user = svc.register(email, password, display_name)
    except EmailAlreadyRegisteredError:
        user = svc.repository.get_user_by_email(email)
        if user is None:
            raise
        print(f"User '{email}' already exists; promoting to admin.")
    user.role = UserRole.ADMIN
    svc.repository.update_user(user)
    print(f"Admin ready: {user.email} (id={user.id})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("email")
    ap.add_argument("password")
    ap.add_argument("--name", default="", help="Display name (defaults to the email's local part).")
    args = ap.parse_args()
    try:
        create_admin(args.email, args.password, args.name)
    except UserNotFoundError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
