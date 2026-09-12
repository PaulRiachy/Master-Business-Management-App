from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models import (
    Activity,
    ActivityType,
    Customer,
    Financial,
    Project,
    ProjectStatus,
    Role,
    Supplier,
    User,
)
from app.schemas.schemas import (
    ActivityCreate,
    ActivityOut,
    FinancialOut,
    FinancialPatch,
    ProjectCreate,
    ProjectDetail,
    ProjectSummary,
    ProjectUpdate,
    TransitionIn,
)
from app.services.project_service import (
    get_project,
    project_summary,
    serialize_detail,
    transition_project,
)

router = APIRouter()


@router.get("/projects", response_model=list[ProjectSummary])
def projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Project)
        .options(
            joinedload(Project.customer),
            joinedload(Project.owner),
            joinedload(Project.financials),
        )
        .order_by(Project.due_date.nulls_last(), Project.id.desc())
    ).unique().all()

    return [project_summary(project, user.role) for project in rows]


@router.post("/projects", response_model=ProjectDetail)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SALES)),
):
    customer = db.get(Customer, payload.customer_id)
    owner = db.get(User, payload.owner_id)

    if not customer or not owner:
        raise HTTPException(status_code=400, detail="Customer or owner not found")

    project_name = payload.project_name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    project = Project(
        customer_id=payload.customer_id,
        supplier_id=payload.supplier_id,
        project_name=project_name,
        owner_id=payload.owner_id,
        next_action=payload.next_action.strip() if payload.next_action else None,
        due_date=payload.due_date,
        status=ProjectStatus.RFQ,
    )
    project.financials = Financial(**payload.financials.model_dump())

    db.add(project)
    db.flush()
    db.add(
        Activity(
            project_id=project.id,
            user_id=user.id,
            activity_type=ActivityType.SYSTEM,
            message="Project created in RFQ status.",
        )
    )
    db.commit()

    return serialize_detail(get_project(db, project.id), user.role)


@router.put("/projects/{project_id}", response_model=ProjectDetail)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SALES, Role.PROCUREMENT)),
):
    project = get_project(db, project_id)
    values = payload.model_dump(exclude_unset=True)

    if "project_name" in values:
        name = (values["project_name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Project name cannot be empty")
        project.project_name = name

    if "owner_id" in values:
        if not db.get(User, values["owner_id"]):
            raise HTTPException(status_code=400, detail="Owner not found")
        project.owner_id = values["owner_id"]

    if "supplier_id" in values:
        if user.role not in (Role.ADMIN, Role.PROCUREMENT):
            raise HTTPException(
                status_code=403,
                detail="Only Admin or Procurement can change supplier",
            )
        if values["supplier_id"] is not None and not db.get(Supplier, values["supplier_id"]):
            raise HTTPException(status_code=400, detail="Supplier not found")
        project.supplier_id = values["supplier_id"]

    if "next_action" in values:
        project.next_action = values["next_action"].strip() if values["next_action"] else None

    if "due_date" in values:
        project.due_date = values["due_date"]

    project.last_update = datetime.now(timezone.utc)
    db.add(
        Activity(
            project_id=project.id,
            user_id=user.id,
            activity_type=ActivityType.SYSTEM,
            message=f"Project details updated by {user.name}.",
        )
    )
    db.commit()

    return serialize_detail(get_project(db, project.id), user.role)


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return serialize_detail(get_project(db, project_id), user.role)


@router.post("/projects/{project_id}/activities", response_model=ActivityOut)
def add_activity(
    project_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        activity_type=ActivityType.COMMENT,
        message=payload.message.strip(),
    )
    project.last_update = datetime.now(timezone.utc)
    db.add(activity)
    db.commit()
    db.refresh(activity)

    return {
        "id": activity.id,
        "activity_type": activity.activity_type,
        "message": activity.message,
        "created_at": activity.created_at,
        "user_name": user.name,
    }


@router.post("/projects/{project_id}/transition", response_model=ProjectDetail)
def transition(
    project_id: int,
    payload: TransitionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        status = ProjectStatus(payload.to_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid status") from exc

    project = get_project(db, project_id)
    project = transition_project(db, project, status, user, payload.override_reason)
    return serialize_detail(get_project(db, project.id), user.role)


@router.patch("/projects/{project_id}/financials", response_model=FinancialOut)
def update_financials(
    project_id: int,
    payload: FinancialPatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SALES, Role.PROCUREMENT)),
):
    project = get_project(db, project_id)
    financial = project.financials or Financial(project_id=project.id)

    allowed_fields = {
        Role.ADMIN: set(payload.model_fields),
        Role.SALES: {"estimated_revenue", "actual_revenue", "customer_balance_due"},
        Role.PROCUREMENT: {
            "estimated_supplier_cost",
            "actual_supplier_cost",
            "estimated_expenses",
            "actual_expenses",
        },
    }[user.role]

    submitted = payload.model_dump(exclude_unset=True)
    forbidden = set(submitted) - allowed_fields
    if forbidden:
        raise HTTPException(
            status_code=403,
            detail=f"Fields not allowed for {user.role}: {', '.join(sorted(forbidden))}",
        )

    for key, value in submitted.items():
        setattr(financial, key, value)

    project.last_update = datetime.now(timezone.utc)
    db.add(financial)
    db.add(
        Activity(
            project_id=project.id,
            user_id=user.id,
            activity_type=ActivityType.SYSTEM,
            message=f"Financials updated by {user.name}.",
        )
    )
    db.commit()

    return serialize_detail(get_project(db, project.id), user.role)["financials"]
