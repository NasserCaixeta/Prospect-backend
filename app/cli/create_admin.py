import argparse

from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.services.users import create_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        create_user(
            db,
            email=args.email,
            password=args.password,
            name=args.name,
            role=UserRole.ADMIN,
        )
    except HTTPException as exc:
        raise SystemExit(str(exc.detail)) from exc
    finally:
        db.close()

    print(f"Admin user created: {args.email.lower()}")


if __name__ == "__main__":
    main()
