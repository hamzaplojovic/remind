#!/usr/bin/env python3
"""Create a new user with a valid license token.

Usage:
    python create_user.py --email user@example.com --plan indie
    python create_user.py --email user@example.com --plan pro --expires 2026-12-31
    python create_user.py --email user@example.com --plan free --database-url sqlite:///./remind.db
"""

import argparse
import secrets
import sys
from datetime import datetime, timezone


VALID_PLANS = ("free", "indie", "pro", "team")


def generate_token(plan_tier: str) -> str:
    """Generate a license token: remind_{tier}_{random_hex}."""
    return f"remind_{plan_tier}_{secrets.token_hex(12)}"


def create_user(
    database_url: str,
    email: str,
    plan_tier: str,
    expires_at: datetime | None = None,
) -> dict:
    """Insert a new user into the database and return their details."""
    from sqlalchemy import create_engine, text

    is_sqlite = "sqlite" in database_url
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine = create_engine(database_url, connect_args=connect_args)

    token = generate_token(plan_tier)
    now = datetime.now(timezone.utc)

    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO users (token, email, plan_tier, created_at, expires_at, active) "
                "VALUES (:token, :email, :plan_tier, :created_at, :expires_at, :active)"
            ),
            {
                "token": token,
                "email": email,
                "plan_tier": plan_tier,
                "created_at": now,
                "expires_at": expires_at,
                "active": True,
            },
        )
        conn.commit()

    return {
        "email": email,
        "token": token,
        "plan_tier": plan_tier,
        "expires_at": expires_at.isoformat() if expires_at else "never",
    }


def main():
    parser = argparse.ArgumentParser(description="Create a new Remind user with a license token.")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--plan", required=True, choices=VALID_PLANS, help="Plan tier")
    parser.add_argument("--expires", default=None, help="Expiration date (YYYY-MM-DD), omit for no expiration")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Database URL (defaults to DATABASE_URL env var, then sqlite:///./remind.db)",
    )
    args = parser.parse_args()

    # Resolve database URL
    import os

    # Default to the backend database relative to monorepo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    monorepo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    default_db = f"sqlite:///{os.path.join(monorepo_root, 'apps', 'backend', 'remind.db')}"
    database_url = args.database_url or os.getenv("DATABASE_URL", default_db)

    # Parse expiration
    expires_at = None
    if args.expires:
        try:
            expires_at = datetime.strptime(args.expires, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: invalid date format '{args.expires}', expected YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    try:
        user = create_user(database_url, args.email, args.plan, expires_at)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nUser created successfully!\n")
    print(f"  Email:   {user['email']}")
    print(f"  Plan:    {user['plan_tier']}")
    print(f"  Expires: {user['expires_at']}")
    print(f"  Token:   {user['token']}")
    print(f"\nLogin with:")
    print(f"  remind login {user['token']}")


if __name__ == "__main__":
    main()
