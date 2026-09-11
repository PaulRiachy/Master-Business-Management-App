from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    contact: str = ""
    country: str = ""
    payment_terms: str = "Net 30"


class CustomerOut(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SupplierCreate(CustomerCreate):
    pass


class SupplierOut(SupplierCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class FinancialIn(BaseModel):
    estimated_revenue: Decimal = Field(default=0, ge=0)
    actual_revenue: Decimal = Field(default=0, ge=0)
    estimated_supplier_cost: Decimal = Field(default=0, ge=0)
    actual_supplier_cost: Decimal = Field(default=0, ge=0)
    estimated_expenses: Decimal = Field(default=0, ge=0)
    actual_expenses: Decimal = Field(default=0, ge=0)
    customer_balance_due: Decimal = Field(default=0, ge=0)


class FinancialPatch(BaseModel):
    estimated_revenue: Decimal | None = Field(default=None, ge=0)
    actual_revenue: Decimal | None = Field(default=None, ge=0)
    estimated_supplier_cost: Decimal | None = Field(default=None, ge=0)
    actual_supplier_cost: Decimal | None = Field(default=None, ge=0)
    estimated_expenses: Decimal | None = Field(default=None, ge=0)
    actual_expenses: Decimal | None = Field(default=None, ge=0)
    customer_balance_due: Decimal | None = Field(default=None, ge=0)


class FinancialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    estimated_revenue: Decimal | None = None
    actual_revenue: Decimal | None = None
    estimated_supplier_cost: Decimal | None = None
    actual_supplier_cost: Decimal | None = None
    estimated_expenses: Decimal | None = None
    actual_expenses: Decimal | None = None
    customer_balance_due: Decimal | None = None
    actual_total_cost: Decimal | None = None
    profit: Decimal | None = None
    margin_percent: Decimal | None = None


class ProjectCreate(BaseModel):
    customer_id: int
    supplier_id: int | None = None
    project_name: str = Field(min_length=1)
    owner_id: int
    next_action: str | None = None
    due_date: date | None = None
    financials: FinancialIn = FinancialIn()


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1)
    owner_id: int | None = None
    next_action: str | None = None
    due_date: date | None = None
    supplier_id: int | None = None


class ProjectSummary(BaseModel):
    id: int
    project_name: str
    status: str
    owner: str
    customer: str
    next_action: str | None
    due_date: date | None
    margin_percent: Decimal | None
    balance_due: Decimal | None
    hold: bool


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activity_type: str
    message: str
    created_at: datetime
    user_name: str | None = None


class ProjectDetail(ProjectSummary):
    supplier: str | None
    last_update: datetime
    financials: FinancialOut
    activities: list[ActivityOut]


class TransitionIn(BaseModel):
    to_status: str
    override_reason: str | None = None


class ActivityCreate(BaseModel):
    message: str = Field(min_length=1)


class AIRequest(BaseModel):
    message: str
    project_id: int | None = None


class AIDraftResponse(BaseModel):
    draft: str
    requires_confirmation: bool = True


class DashboardOut(BaseModel):
    attention: list[ProjectSummary]
    active_rfqs: int
    pending_quotes: int
    active_orders: int
    payments_due: Decimal
    shipment_holds: int
