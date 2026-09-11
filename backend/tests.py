import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.models import ProjectStatus, Role
from app.services.project_service import ORDER, project_margin, project_summary, serialize_detail, transition_project


def financial(revenue="1000", supplier="700", expenses="50", balance="0"):
    r,s,e,b=map(Decimal,(revenue,supplier,expenses,balance))
    return SimpleNamespace(estimated_revenue=r, actual_revenue=r, estimated_supplier_cost=s, actual_supplier_cost=s,
                           estimated_expenses=e, actual_expenses=e, customer_balance_due=b,
                           margin_percent=((r-s-e)/r*100 if r else Decimal("0")),
                           actual_total_cost=s+e, profit=r-s-e)

def project(status=ProjectStatus.RFQ, balance="0"):
    return SimpleNamespace(id=1,status=status,financials=financial(balance=balance),owner=SimpleNamespace(name="Owner"),customer=SimpleNamespace(name="Customer"),project_name="Demo",next_action="Follow up",due_date=None,last_update=None,activities=[])


def test_workflow_order_is_linear():
    assert ORDER == [ProjectStatus.RFQ, ProjectStatus.QUOTED, ProjectStatus.ORDERED, ProjectStatus.SHIPPING, ProjectStatus.CLOSED]

@pytest.mark.parametrize("current,target", [(ProjectStatus.RFQ,ProjectStatus.ORDERED),(ProjectStatus.QUOTED,ProjectStatus.SHIPPING),(ProjectStatus.SHIPPING,ProjectStatus.RFQ)])
def test_workflow_rejects_skipping_or_backwards(current,target):
    p=project(current); db=SimpleNamespace(add=lambda x:None,commit=lambda:None,refresh=lambda x:None)
    actor=SimpleNamespace(role=Role.SALES,id=1,name="Sales")
    with pytest.raises(HTTPException) as exc: transition_project(db,p,target,actor)
    assert exc.value.status_code == 400


def test_shipping_hold_blocks_sales():
    p=project(ProjectStatus.SHIPPING,"250"); db=SimpleNamespace(add=lambda x:None,commit=lambda:None,refresh=lambda x:None)
    actor=SimpleNamespace(role=Role.SALES,id=1,name="Sales")
    with pytest.raises(HTTPException) as exc: transition_project(db,p,ProjectStatus.CLOSED,actor)
    assert exc.value.status_code == 409


def test_shipping_hold_requires_admin_reason():
    p=project(ProjectStatus.SHIPPING,"250"); db=SimpleNamespace(add=lambda x:None,commit=lambda:None,refresh=lambda x:None)
    actor=SimpleNamespace(role=Role.ADMIN,id=1,name="Admin")
    with pytest.raises(HTTPException) as exc: transition_project(db,p,ProjectStatus.CLOSED,actor)
    assert exc.value.status_code == 400


def test_admin_can_override_shipping_hold_and_logs_activity():
    added=[]; p=project(ProjectStatus.SHIPPING,"250"); db=SimpleNamespace(add=added.append,commit=lambda:None,refresh=lambda x:None)
    actor=SimpleNamespace(role=Role.ADMIN,id=1,name="Admin")
    transition_project(db,p,ProjectStatus.CLOSED,actor,"Customer confirmed payment next business day")
    assert p.status == ProjectStatus.CLOSED
    assert "ADMIN OVERRIDE by Admin" in added[0].message
    assert "Customer confirmed payment" in added[0].message


def test_margin_calculation_is_live():
    p=project(); p.financials=financial("10000","7500","500")
    assert project_margin(p) == Decimal("20.0")
    p.financials=financial("10000","8000","500")
    assert project_margin(p) == Decimal("15.0")


def test_summary_hides_margin_and_supplier_cost_from_sales():
    p=project(); p.supplier=SimpleNamespace(name="Secret Supplier")
    result=project_summary(p,Role.SALES)
    assert result["margin_percent"] is None
    assert result["balance_due"] == Decimal("0")
    assert "supplier" not in result


def test_summary_exposes_margin_to_admin():
    p=project(); result=project_summary(p,Role.ADMIN)
    assert result["margin_percent"] == Decimal("25")


def test_summary_flags_shipping_hold():
    p=project(ProjectStatus.SHIPPING,"100")
    assert project_summary(p,Role.ADMIN)["hold"] is True


def test_procurement_summary_hides_margin_and_balance():
    p=project(); p.supplier=SimpleNamespace(name="Supplier")
    result=project_summary(p,Role.PROCUREMENT)
    assert result["margin_percent"] is None
    assert result["balance_due"] is None


def test_procurement_detail_hides_revenue_balance_profit_and_margin():
    p=project(); p.supplier=SimpleNamespace(name="Supplier")
    result=serialize_detail(p,Role.PROCUREMENT)
    f=result["financials"]
    assert f["estimated_revenue"] is None
    assert f["actual_revenue"] is None
    assert f["customer_balance_due"] is None
    assert f["profit"] is None
    assert f["margin_percent"] is None


def test_sales_detail_hides_supplier_costs_expenses_profit_and_margin():
    p=project(); p.supplier=SimpleNamespace(name="Supplier")
    result=serialize_detail(p,Role.SALES)
    f=result["financials"]
    assert f["estimated_supplier_cost"] is None
    assert f["actual_supplier_cost"] is None
    assert f["estimated_expenses"] is None
    assert f["actual_expenses"] is None
    assert f["profit"] is None
    assert f["margin_percent"] is None


def test_ai_context_hides_sales_restricted_financials():
    from app.services.ai_service import visible_project_data
    class DB:
        def scalars(self, query):
            p = project()
            p.supplier = SimpleNamespace(name="Supplier")
            return SimpleNamespace(all=lambda: [p])
    rows = visible_project_data(DB(), Role.SALES)
    row = rows[0]
    assert "revenue" in row and "balance_due" in row
    assert "supplier_cost" not in row
    assert "margin_percent" not in row


def test_ai_context_hides_procurement_restricted_financials():
    from app.services.ai_service import visible_project_data
    class DB:
        def scalars(self, query):
            p = project()
            p.supplier = SimpleNamespace(name="Supplier")
            return SimpleNamespace(all=lambda: [p])
    rows = visible_project_data(DB(), Role.PROCUREMENT)
    row = rows[0]
    assert "supplier_cost" in row
    assert "revenue" not in row
    assert "balance_due" not in row
    assert "margin_percent" not in row


def test_ai_rejects_sales_restricted_questions():
    from app.services.ai_service import ask_business
    assert "restricted" in ask_business(None, Role.SALES, "Show me supplier costs", None)


def test_ai_rejects_procurement_restricted_questions():
    from app.services.ai_service import ask_business
    assert "restricted" in ask_business(None, Role.PROCUREMENT, "Show me customer revenue and margins", None)


def test_project_detail_allows_null_hidden_financial_fields():
    from app.schemas.schemas import ProjectDetail
    payload = {
        "id": 1, "project_name": "Demo", "status": "RFQ", "owner": "Owner",
        "customer": "Customer", "next_action": "Follow up", "due_date": None,
        "margin_percent": None, "balance_due": None, "hold": False, "supplier": None,
        "last_update": datetime.now(timezone.utc),
        "financials": {
            "estimated_revenue": None, "actual_revenue": None,
            "estimated_supplier_cost": 10, "actual_supplier_cost": 10,
            "estimated_expenses": 2, "actual_expenses": 2,
            "customer_balance_due": None, "actual_total_cost": 12,
            "profit": None, "margin_percent": None,
        },
        "activities": [],
    }
    ProjectDetail.model_validate(payload)
