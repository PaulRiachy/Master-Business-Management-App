from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Role(str, Enum):
    ADMIN = "ADMIN"
    SALES = "SALES"
    PROCUREMENT = "PROCUREMENT"


class ProjectStatus(str, Enum):
    RFQ = "RFQ"
    QUOTED = "QUOTED"
    ORDERED = "ORDERED"
    SHIPPING = "SHIPPING"
    CLOSED = "CLOSED"


class ActivityType(str, Enum):
    COMMENT = "COMMENT"
    SYSTEM = "SYSTEM"
    AI_DRAFT = "AI_DRAFT"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(String(20), default=Role.SALES)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    contact: Mapped[str] = mapped_column(String(160), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    payment_terms: Mapped[str] = mapped_column(String(120), default="Net 30")
    projects: Mapped[list["Project"]] = relationship(back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    contact: Mapped[str] = mapped_column(String(160), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    payment_terms: Mapped[str] = mapped_column(String(120), default="Net 30")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    project_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[ProjectStatus] = mapped_column(String(20), default=ProjectStatus.RFQ, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    next_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    last_update: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer: Mapped[Customer] = relationship(back_populates="projects")
    supplier: Mapped[Supplier | None] = relationship()
    owner: Mapped[User] = relationship()
    financials: Mapped["Financial"] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="project", cascade="all, delete-orphan", order_by="Activity.created_at")


class Financial(Base):
    __tablename__ = "financials"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    estimated_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    actual_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    estimated_supplier_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    actual_supplier_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    estimated_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    actual_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    customer_balance_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    project: Mapped[Project] = relationship(back_populates="financials")

    @property
    def actual_total_cost(self) -> Decimal:
        return self.actual_supplier_cost + self.actual_expenses

    @property
    def profit(self) -> Decimal:
        return self.actual_revenue - self.actual_total_cost

    @property
    def margin_percent(self) -> Decimal:
        if not self.actual_revenue:
            return Decimal("0")
        return (self.profit / self.actual_revenue) * 100


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    activity_type: Mapped[ActivityType] = mapped_column(String(20), default=ActivityType.COMMENT)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    project: Mapped[Project] = relationship(back_populates="activities")
    user: Mapped[User | None] = relationship()
