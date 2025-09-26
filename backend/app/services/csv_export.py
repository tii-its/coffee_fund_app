import csv
import io
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Consumption, MoneyMove, User, Product
from datetime import datetime


class CSVExportService:
    @staticmethod
    def export_consumptions(db: Session, limit: int = 1000) -> str:
        """Export consumptions to CSV string"""
        consumptions = (
            db.query(Consumption)
            .join(User, Consumption.user_id == User.id)
            .join(Product, Consumption.product_id == Product.id)
            .order_by(desc(Consumption.at))
            .limit(limit)
            .all()
        )

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'User', 'Product', 'Quantity', 
            'Unit Price (€)', 'Total Amount (€)', 'Created By'
        ])
        
        # Write data
        for consumption in consumptions:
            writer.writerow([
                consumption.at.strftime('%Y-%m-%d %H:%M:%S'),
                consumption.user.display_name,
                consumption.product.name,
                consumption.qty,
                f"{consumption.unit_price_cents / 100:.2f}",
                f"{consumption.amount_cents / 100:.2f}",
                consumption.creator.display_name
            ])
        
        return output.getvalue()

    @staticmethod
    def export_money_moves(db: Session, limit: int = 1000) -> str:
        """Export money moves to CSV string"""
        money_moves = (
            db.query(MoneyMove)
            .join(User, MoneyMove.user_id == User.id)
            .order_by(desc(MoneyMove.created_at))
            .limit(limit)
            .all()
        )

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Created Date', 'Type', 'User', 'Amount (€)', 
            'Status', 'Note', 'Created By', 'Confirmed Date', 'Confirmed By'
        ])
        
        # Write data
        for move in money_moves:
            writer.writerow([
                move.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                move.type.value.title(),
                move.user.display_name,
                f"{move.amount_cents / 100:.2f}",
                move.status.value.title(),
                move.note or '',
                move.creator.display_name,
                move.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if move.confirmed_at else '',
                move.confirmer.display_name if move.confirmer else ''
            ])
        
        return output.getvalue()

    @staticmethod
    def export_user_balances(db: Session, balances: List[Dict[str, Any]]) -> str:
        """Export user balances to CSV string"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['User', 'Balance (€)', 'Role', 'Active'])
        
        # Write data
        for balance in balances:
            writer.writerow([
                balance['user']['display_name'],
                f"{balance['balance_cents'] / 100:.2f}",
                balance['user']['role'].title(),
                'Yes' if balance['user']['is_active'] else 'No'
            ])
        
        return output.getvalue()