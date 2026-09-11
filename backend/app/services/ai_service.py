from datetime import date
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.models import Project, Role


def client():
    from openai import OpenAI
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def visible_project_data(db: Session, role: str, project_id: int | None = None):
    q = select(Project).options(
        joinedload(Project.customer),
        joinedload(Project.owner),
        joinedload(Project.financials),
        joinedload(Project.supplier),
    )
    if project_id:
        q = q.where(Project.id == project_id)
    projects = db.scalars(q).all()
    data = []
    for p in projects:
        row = {
            "id": p.id,
            "name": p.project_name,
            "status": p.status,
            "customer": p.customer.name,
            "owner": p.owner.name,
            "next_action": p.next_action,
            "due_date": str(p.due_date) if p.due_date else None,
        }
        # Keep AI context strictly role-scoped. Never add restricted values and
        # never rely on the prompt alone to hide them.
        if role in (Role.ADMIN, Role.SALES):
            row["revenue"] = float(p.financials.actual_revenue) if p.financials else 0
            row["balance_due"] = float(p.financials.customer_balance_due) if p.financials else 0
        if role in (Role.ADMIN, Role.PROCUREMENT):
            row["supplier"] = p.supplier.name if p.supplier else None
            row["supplier_cost"] = float(p.financials.actual_supplier_cost) if p.financials else 0
        if role == Role.ADMIN:
            row["margin_percent"] = float(p.financials.margin_percent) if p.financials else 0
        data.append(row)
    return data


def _restricted_ai_request(role: str, question: str) -> str | None:
    text = question.lower()
    if role == Role.SALES:
        restricted = (
            "supplier cost", "supplier costs", "supplier", "expense", "expenses",
            "profit", "margin", "gross margin", "cost price", "costs"
        )
    elif role == Role.PROCUREMENT:
        restricted = (
            "revenue", "customer revenue", "customer balance", "balance due",
            "receivable", "receivables", "profit", "margin", "sales price", "customer payment"
        )
    else:
        return None
    if any(term in text for term in restricted):
        return "I can’t provide that information because it is restricted for your role."
    return None


def ask_business(db: Session, role: str, question: str, project_id: int | None = None) -> str:
    restricted_response = _restricted_ai_request(role, question)
    if restricted_response:
        return restricted_response
    context = visible_project_data(db, role, project_id)
    system = """You are Ask My Business, an internal project-management assistant. Answer ONLY from the supplied database context. Never invent projects, numbers, customers, dates, or financial values. If the context does not contain the answer, say so. Respect the user's role: the context is already filtered for visibility. Be concise and practical.\n\nDATABASE CONTEXT:\n""" + json.dumps(context, default=str)
    response = client().chat.completions.create(
        model=settings.openai_model,
        temperature=0.1,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": question}],
    )
    return response.choices[0].message.content or "I could not produce an answer."


def daily_brief(db: Session, role: str) -> str:
    today = date.today()
    context = visible_project_data(db, role)
    attention = []
    for p in context:
        overdue = p.get("due_date") and p["due_date"] < str(today) and p["status"] != "CLOSED"
        missing_action = not p.get("next_action") and p["status"] != "CLOSED"
        low_margin = role == Role.ADMIN and p.get("margin_percent") is not None and p["margin_percent"] < 20
        balance = p.get("balance_due", 0) > 0 and p["status"] == "SHIPPING"
        if overdue or missing_action or low_margin or balance:
            attention.append(p)
    if not attention:
        return "No projects currently require attention based on today's rules."
    system = "Create a short management brief from ONLY this database data. Mention the reason each project needs attention. Do not invent anything.\n" + json.dumps(attention, default=str)
    response = client().chat.completions.create(model=settings.openai_model, temperature=0.1, messages=[{"role": "system", "content": system}])
    return response.choices[0].message.content or "Attention items are available on the dashboard."


def draft_followup(db: Session, role: str, project_id: int) -> str:
    context = visible_project_data(db, role, project_id)
    system = """Draft a professional, short customer follow-up email for this project. Use only supplied facts. Do not send it. Include a subject line and body. If a fact is missing, phrase it without inventing details."""
    response = client().chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        messages=[{"role": "system", "content": system + "\nPROJECT DATA:\n" + json.dumps(context, default=str)}],
    )
    return response.choices[0].message.content or "Unable to draft email."
