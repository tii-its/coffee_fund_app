from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    TREASURER = "treasurer"
    ADMIN = "admin"


class MoneyMoveType(str, Enum):
    DEPOSIT = "deposit"
    PAYOUT = "payout"


class MoneyMoveStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CONFIRM = "confirm"
    REJECT = "reject"