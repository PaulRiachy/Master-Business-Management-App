from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Activity, ActivityType, User
from app.schemas.schemas import ActivityCreate, AIDraftResponse, AIRequest
from app.services.ai_service import ask_business, daily_brief, draft_followup
from app.services.project_service import get_project

router = APIRouter()


@router.post("/ai/ask")
def ai_ask(
    payload: AIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return {"answer": ask_business(db, user.role, payload.message, payload.project_id)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/daily-brief")
def ai_daily_brief(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return {"brief": daily_brief(db, user.role)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/draft-followup/{project_id}", response_model=AIDraftResponse)
def ai_draft(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return {
            "draft": draft_followup(db, user.role, project_id),
            "requires_confirmation": True,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/confirm-draft/{project_id}")
def confirm_draft(
    project_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        activity_type=ActivityType.AI_DRAFT,
        message=f"AI draft confirmed by {user.name}:\n{payload.message}",
    )
    project.last_update = datetime.now(timezone.utc)
    db.add(activity)
    db.commit()
    return {"message": "AI draft recorded after human confirmation"}
