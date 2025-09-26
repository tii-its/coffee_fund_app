from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.csv_export import CSVExportService
from app.services.balance import BalanceService
from app.core.config import settings

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/consumptions")
def export_consumptions(
    limit: int = settings.csv_export_limit,
    db: Session = Depends(get_db)
):
    """Export consumptions to CSV"""
    csv_data = CSVExportService.export_consumptions(db, limit)
    
    return Response(
        content=csv_data, 
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=consumptions.csv"}
    )


@router.get("/money-moves")
def export_money_moves(
    limit: int = settings.csv_export_limit,
    db: Session = Depends(get_db)
):
    """Export money moves to CSV"""
    csv_data = CSVExportService.export_money_moves(db, limit)
    
    return Response(
        content=csv_data, 
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=money_moves.csv"}
    )


@router.get("/balances")
def export_balances(
    db: Session = Depends(get_db)
):
    """Export user balances to CSV"""
    balances = BalanceService.get_all_user_balances(db)
    balances_dict = [
        {
            "user": balance.user.model_dump(),
            "balance_cents": balance.balance_cents
        }
        for balance in balances
    ]
    
    csv_data = CSVExportService.export_user_balances(db, balances_dict)
    
    return Response(
        content=csv_data, 
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=balances.csv"}
    )