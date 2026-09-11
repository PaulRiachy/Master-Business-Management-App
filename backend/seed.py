from datetime import date, timedelta
import time

from decimal import Decimal
from sqlalchemy import text
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Activity, ActivityType, Customer, Financial, Project, ProjectStatus, Role, Supplier, User

def wait_for_database(max_attempts: int = 30, delay_seconds: float = 1.0) -> None:
    last_error = None
    for _ in range(max_attempts):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay_seconds)
    raise RuntimeError(f"Could not connect to PostgreSQL. Check Docker and DATABASE_URL. Last error: {last_error}")


wait_for_database()
Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if db.query(User).count():
        print("Seed data already exists. No changes were made.")
    else:
        admin = User(name="Admin User", email="admin@example.com", password_hash=hash_password("admin123"), role=Role.ADMIN)
        sales = User(name="Sarah Sales", email="sales@example.com", password_hash=hash_password("sales123"), role=Role.SALES)
        procurement = User(name="Peter Procurement", email="procurement@example.com", password_hash=hash_password("proc123"), role=Role.PROCUREMENT)
        db.add_all([admin, sales, procurement]); db.flush()
        c1 = Customer(name="Acme Trading", contact="Maya", country="Lebanon", payment_terms="Net 30")
        c2 = Customer(name="Northstar Retail", contact="Omar", country="UAE", payment_terms="Net 45")
        s1 = Supplier(name="Global Components", contact="Lina", country="Turkey", payment_terms="Net 30")
        s2 = Supplier(name="FastShip Logistics", contact="Rami", country="Lebanon", payment_terms="Net 15")
        db.add_all([c1, c2, s1, s2]); db.flush()
        projects = [
            Project(project_name="Acme Control Panels", customer_id=c1.id, supplier_id=s1.id, owner_id=sales.id, status=ProjectStatus.RFQ, next_action="Confirm technical scope", due_date=date.today()+timedelta(days=2)),
            Project(project_name="Northstar Store Rollout", customer_id=c2.id, supplier_id=s2.id, owner_id=sales.id, status=ProjectStatus.QUOTED, next_action="Follow up on quotation", due_date=date.today()-timedelta(days=2)),
            Project(project_name="Acme Spare Parts", customer_id=c1.id, supplier_id=s1.id, owner_id=sales.id, status=ProjectStatus.SHIPPING, next_action="Confirm customer payment", due_date=date.today()-timedelta(days=1)),
            Project(project_name="Northstar Inspection", customer_id=c2.id, supplier_id=s2.id, owner_id=procurement.id, status=ProjectStatus.ORDERED, next_action=None, due_date=date.today()+timedelta(days=5)),
        ]
        db.add_all(projects); db.flush()
        financials = [
            Financial(project_id=projects[0].id, estimated_revenue=Decimal("18000"), actual_revenue=Decimal("0"), estimated_supplier_cost=Decimal("12000"), actual_supplier_cost=Decimal("0"), estimated_expenses=Decimal("800"), actual_expenses=Decimal("0")),
            Financial(project_id=projects[1].id, estimated_revenue=Decimal("25000"), actual_revenue=Decimal("25000"), estimated_supplier_cost=Decimal("21000"), actual_supplier_cost=Decimal("21500"), estimated_expenses=Decimal("1000"), actual_expenses=Decimal("1200")),
            Financial(project_id=projects[2].id, estimated_revenue=Decimal("30000"), actual_revenue=Decimal("30000"), estimated_supplier_cost=Decimal("19000"), actual_supplier_cost=Decimal("20500"), estimated_expenses=Decimal("2500"), actual_expenses=Decimal("3000"), customer_balance_due=Decimal("5000")),
            Financial(project_id=projects[3].id, estimated_revenue=Decimal("12000"), actual_revenue=Decimal("12000"), estimated_supplier_cost=Decimal("9000"), actual_supplier_cost=Decimal("9500"), estimated_expenses=Decimal("500"), actual_expenses=Decimal("400")),
        ]
        db.add_all(financials)
        for p in projects:
            db.add(Activity(project_id=p.id, user_id=admin.id, activity_type=ActivityType.SYSTEM, message=f"Seeded project in {p.status.value} status."))
        db.commit()
        print("Seed data created.")
finally:
    db.close()
