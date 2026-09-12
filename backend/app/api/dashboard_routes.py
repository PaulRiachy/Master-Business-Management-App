from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Project, ProjectStatus, Role, User
from app.schemas.schemas import DashboardOut
from app.services.project_service import project_summary

router = APIRouter()


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Project).options(
            joinedload(Project.customer),
            joinedload(Project.owner),
            joinedload(Project.financials),
        )
    ).unique().all()

    active_projects = [project for project in rows if project.status != ProjectStatus.CLOSED]
    attention = []
    payments_due = Decimal("0")
    shipment_holds = 0

    for project in active_projects:
        financial = project.financials
        overdue = bool(project.due_date and project.due_date < date.today())
        missing_next_action = not project.next_action
        low_margin = (
            user.role == Role.ADMIN
            and financial is not None
            and financial.margin_percent < 20
        )
        shipment_hold = (
            project.status == ProjectStatus.SHIPPING
            and financial is not None
            and financial.customer_balance_due > 0
        )

        if financial is not None and user.role in (Role.ADMIN, Role.SALES):
            payments_due += financial.customer_balance_due

        if shipment_hold:
            shipment_holds += 1

        if overdue or missing_next_action or low_margin or shipment_hold:
            attention.append(project_summary(project, user.role))

    return {
        "attention": attention,
        "active_rfqs": sum(project.status == ProjectStatus.RFQ for project in rows),
        "pending_quotes": sum(project.status == ProjectStatus.QUOTED for project in rows),
        "active_orders": sum(
            project.status in (ProjectStatus.ORDERED, ProjectStatus.SHIPPING)
            for project in rows
        ),
        "payments_due": payments_due,
        "shipment_holds": shipment_holds,
    }
