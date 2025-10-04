"""Utility script to set all admin user PINs to 9999.

Run inside backend container or with project venv active:
  python -m scripts.set_admin_pin
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.users import User
from app.core.enums import UserRole
from app.services.pin import PinService


def main():
    db: Session = SessionLocal()
    try:
        admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
        if not admins:
            print("No admin users found.")
            return
        new_hash = PinService.hash_pin("9999")
        for u in admins:
            u.pin_hash = new_hash
            print(f"Updated admin {u.id} ({u.display_name}) PIN -> 9999")
        db.commit()
        print(f"Updated {len(admins)} admin user(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()