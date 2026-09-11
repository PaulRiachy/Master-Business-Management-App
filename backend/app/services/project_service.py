from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.models import Activity, ActivityType, Financial, Project, ProjectStatus, Role, User

ORDER = [ProjectStatus.RFQ, ProjectStatus.QUOTED, ProjectStatus.ORDERED, ProjectStatus.SHIPPING, ProjectStatus.CLOSED]


def project_margin(project: Project) -> Decimal:
    return project.financials.margin_percent if project.financials else Decimal("0")


def project_summary(project: Project, role: str) -> dict:
    margin = project_margin(project)
    hold = project.status == ProjectStatus.SHIPPING and bool(project.financials and project.financials.customer_balance_due > 0)
    data = {
        "id": project.id,
        "project_name": project.project_name,
        "status": project.status,
        "owner": project.owner.name,
        "customer": project.customer.name,
        "next_action": project.next_action,
        "due_date": project.due_date,
        "margin_percent": margin if role == Role.ADMIN else None,
        "balance_due": project.financials.customer_balance_due if project.financials and role in (Role.ADMIN, Role.SALES) else None,
        "hold": hold,
    }
    return data


def serialize_detail(project: Project, role: str) -> dict:
    financial = project.financials or Financial(project_id=project.id)
    activities = [
        {
            "id": a.id,
            "activity_type": a.activity_type,
            "message": a.message,
            "created_at": a.created_at,
            "user_name": a.user.name if a.user else None,
        }
        for a in project.activities
    ]
    f = {
        "estimated_revenue": financial.estimated_revenue if role in (Role.ADMIN, Role.SALES) else None,
        "actual_revenue": financial.actual_revenue if role in (Role.ADMIN, Role.SALES) else None,
        "estimated_supplier_cost": financial.estimated_supplier_cost if role in (Role.ADMIN, Role.PROCUREMENT) else None,
        "actual_supplier_cost": financial.actual_supplier_cost if role in (Role.ADMIN, Role.PROCUREMENT) else None,
        "estimated_expenses": financial.estimated_expenses if role in (Role.ADMIN, Role.PROCUREMENT) else None,
        "actual_expenses": financial.actual_expenses if role in (Role.ADMIN, Role.PROCUREMENT) else None,
        "customer_balance_due": financial.customer_balance_due if role in (Role.ADMIN, Role.SALES) else None,
        "actual_total_cost": financial.actual_total_cost if role in (Role.ADMIN, Role.PROCUREMENT) else None,
        "profit": financial.profit if role == Role.ADMIN else None,
        "margin_percent": financial.margin_percent if role == Role.ADMIN else None,
    }
    return {
        **project_summary(project, role),
        "supplier": project.supplier.name if project.supplier and role in (Role.ADMIN, Role.PROCUREMENT) else None,
        "last_update": project.last_update,
        "financials": f,
        "activities": activities,
    }


def get_project(db: Session, project_id: int) -> Project:
    result = db.execute(
        select(Project)
        .options(joinedload(Project.customer), joinedload(Project.owner), joinedload(Project.supplier), joinedload(Project.financials), joinedload(Project.activities).joinedload(Activity.user))
        .where(Project.id == project_id)
    )
    project = result.unique().scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def transition_project(db: Session, project: Project, to_status: ProjectStatus, actor: User, override_reason: str | None = None):
    try:
        current_index = ORDER.index(project.status)
        target_index = ORDER.index(to_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow status")
    if target_index != current_index + 1:
        raise HTTPException(status_code=400, detail="Status must progress one step at a time")

    hold = project.status == ProjectStatus.SHIPPING and project.financials and project.financials.customer_balance_due > 0 and to_status == ProjectStatus.CLOSED
    if hold and actor.role != Role.ADMIN:
        raise HTTPException(status_code=409, detail="Shipment hold: customer balance is outstanding. Admin override required.")
    if hold and not override_reason:
        raise HTTPException(status_code=400, detail="Admin override reason is required")

    project.status = to_status
    project.last_update = datetime.now(timezone.utc)
    message = f"Status changed from {ORDER[current_index].value} to {to_status.value}."
    if hold:
        message += f" ADMIN OVERRIDE by {actor.name}: {override_reason}"
    db.add(Activity(project_id=project.id, user_id=actor.id, activity_type=ActivityType.SYSTEM, message=message))
    db.commit()
    db.refresh(project)
    return project
