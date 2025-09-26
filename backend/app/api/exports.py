from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.csv_export import CSVExportService
from app.services.balance import BalanceService
from app.core.config import settings

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/consumptions")
def export_consumptions(
    response: Response,
    limit: int = settings.csv_export_limit,
    db: Session = Depends(get_db)
):
    """Export consumptions to CSV"""
    csv_data = CSVExportService.export_consumptions(db, limit)
    
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=consumptions.csv"
    
    return Response(content=csv_data, media_type="text/csv")


@router.get("/money-moves")
def export_money_moves(
    response: Response,
    limit: int = settings.csv_export_limit,
    db: Session = Depends(get_db)
):
    """Export money moves to CSV"""
    csv_data = CSVExportService.export_money_moves(db, limit)
    
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=money_moves.csv"
    
    return Response(content=csv_data, media_type="text/csv")


@router.get("/balances")
def export_balances(
    response: Response,
    db: Session = Depends(get_db)
):
    """Export user balances to CSV"""
    balances = BalanceService.get_all_user_balances(db)
    balances_dict = [
        {
            "user": balance.user.dict(),
            "balance_cents": balance.balance_cents
        }
        for balance in balances
    ]
    
    csv_data = CSVExportService.export_user_balances(db, balances_dict)
    
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=balances.csv"
    
    return Response(content=csv_data, media_type="text/csv")