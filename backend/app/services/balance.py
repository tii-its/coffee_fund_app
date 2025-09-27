from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models import User, Consumption, MoneyMove
from app.core.enums import MoneyMoveStatus, MoneyMoveType
from app.schemas.users import UserBalance, UserResponse
from typing import List


class BalanceService:
    @staticmethod
    def get_user_balance(db: Session, user_id: str) -> int:
        """Calculate user's current balance in cents"""
        # Sum all consumptions (negative)
        consumption_total = db.query(
            func.coalesce(func.sum(Consumption.amount_cents), 0)
        ).filter(Consumption.user_id == user_id).scalar() or 0

        # Sum all confirmed deposits (positive) and payouts (negative)
        money_move_total = db.query(
            func.coalesce(func.sum(
                case(
                    (MoneyMove.type == MoneyMoveType.DEPOSIT, MoneyMove.amount_cents),
                    (MoneyMove.type == MoneyMoveType.PAYOUT, -MoneyMove.amount_cents),
                    else_=0
                )
            ), 0)
        ).filter(
            MoneyMove.user_id == user_id,
            MoneyMove.status == MoneyMoveStatus.CONFIRMED
        ).scalar() or 0

        return money_move_total - consumption_total

    @staticmethod
    def get_all_user_balances(db: Session) -> List[UserBalance]:
        """Get balance for all active users"""
        users = db.query(User).filter(User.is_active == True).all()
        balances = []
        
        for user in users:
            balance = BalanceService.get_user_balance(db, user.id)
            balances.append(UserBalance(
                user=UserResponse.model_validate(user),
                balance_cents=balance
            ))
        
        return balances

    @staticmethod
    def get_users_below_threshold(db: Session, threshold_cents: int) -> List[UserBalance]:
        """Get users with balance below threshold"""
        all_balances = BalanceService.get_all_user_balances(db)
        return [balance for balance in all_balances if balance.balance_cents < threshold_cents]