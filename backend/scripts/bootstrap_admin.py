"""Bootstrap an initial admin user with PIN 9999.

Creates a single admin user (display_name='admin') with PIN 9999 IFF no admin user
currently exists. If one or more admin users already exist, the script exits
without changes.

Usage (inside backend container or with project venv):
  python -m scripts.bootstrap_admin
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.users import User
from app.core.enums import UserRole
from app.services.pin import PinService


def main() -> None:
    db: Session = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing_admin:
            print(f"Admin already present (id={existing_admin.id}, display_name={existing_admin.display_name}). Nothing to do.")
            return
        # Create admin
        admin_user = User(
            id=uuid4(),
            display_name="admin",
            role=UserRole.ADMIN,
            pin_hash=PinService.hash_pin("9999"),
            qr_code=None,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Created admin user {admin_user.id} with display_name='admin' and PIN 9999.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    main()
