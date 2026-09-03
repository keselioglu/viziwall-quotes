from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, computed_field

from app.models import ProductType, QuoteStatus


# --- Auth ---

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    is_active: bool


# --- Customer ---

class CustomerBase(BaseModel):
    external_id: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


# --- Product ---

class ProductBase(BaseModel):
    product_type: ProductType
    name: str
    description: Optional[str] = None
    unit_price: Decimal
    unit: str = "pcs"
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_type: Optional[ProductType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[Decimal] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


# --- Event ---

class EventBase(BaseModel):
    name: str
    venue: Optional[str] = None
    default_start_date: Optional[date] = None
    default_end_date: Optional[date] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    venue: Optional[str] = None
    default_start_date: Optional[date] = None
    default_end_date: Optional[date] = None


class EventOut(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


# --- Quote line items ---

class QuoteLineItemBase(BaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    sort_order: int = 0


class QuoteLineItemCreate(QuoteLineItemBase):
    pass


class QuoteLineItemOut(QuoteLineItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    line_total: Decimal


# --- Quotation ---

class QuotationBase(BaseModel):
    customer_id: str
    event_name: Optional[str] = None
    event_venue: Optional[str] = None
    event_start_date: Optional[date] = None
    event_end_date: Optional[date] = None
    event_dates_text: Optional[str] = None
    status: QuoteStatus = QuoteStatus.draft
    currency: str = "EUR"
    tax_rate_percent: Decimal = Decimal("0")
    notes: Optional[str] = None
    valid_until: Optional[date] = None
    service_description: Optional[str] = None
    discount_amount: Optional[Decimal] = None
    historical_total_amount: Optional[Decimal] = None
    quotation_date_text: Optional[str] = None


class QuotationCreate(QuotationBase):
    quote_number: Optional[str] = None  # set explicitly for imports; auto-generated otherwise
    line_items: list[QuoteLineItemCreate] = []


class QuotationUpdate(BaseModel):
    customer_id: Optional[str] = None
    event_name: Optional[str] = None
    event_venue: Optional[str] = None
    event_start_date: Optional[date] = None
    event_end_date: Optional[date] = None
    event_dates_text: Optional[str] = None
    status: Optional[QuoteStatus] = None
    currency: Optional[str] = None
    tax_rate_percent: Optional[Decimal] = None
    notes: Optional[str] = None
    valid_until: Optional[date] = None
    service_description: Optional[str] = None
    discount_amount: Optional[Decimal] = None
    historical_total_amount: Optional[Decimal] = None
    quotation_date_text: Optional[str] = None
    line_items: Optional[list[QuoteLineItemCreate]] = None


class QuotationOut(QuotationBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    quote_number: str
    created_at: datetime
    updated_at: datetime
    line_items: list[QuoteLineItemOut] = []
    customer: CustomerOut

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return sum((li.line_total for li in self.line_items), Decimal("0"))

    @computed_field
    @property
    def tax_amount(self) -> Decimal:
        return self.subtotal * (self.tax_rate_percent / Decimal("100"))

    @computed_field
    @property
    def total(self) -> Decimal:
        # Historical/imported quotes have no line items — fall back to the recorded total.
        if not self.line_items and self.historical_total_amount is not None:
            return self.historical_total_amount
        return self.subtotal + self.tax_amount


class QuotationListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    quote_number: str
    status: QuoteStatus
    event_name: Optional[str] = None
    event_venue: Optional[str] = None
    event_start_date: Optional[date] = None
    event_end_date: Optional[date] = None
    event_dates_text: Optional[str] = None
    currency: str
    tax_rate_percent: Decimal
    historical_total_amount: Optional[Decimal] = None
    created_at: datetime
    customer: CustomerOut
    line_items: list[QuoteLineItemOut] = []

    @computed_field
    @property
    def total(self) -> Decimal:
        subtotal = sum((li.line_total for li in self.line_items), Decimal("0"))
        if not self.line_items and self.historical_total_amount is not None:
            return self.historical_total_amount
        tax_amount = subtotal * (self.tax_rate_percent / Decimal("100"))
        return subtotal + tax_amount
