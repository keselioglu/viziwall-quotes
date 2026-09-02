import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ProductType(str, enum.Enum):
    led_wall = "led_wall"
    displays = "displays"
    audio = "audio"
    it_equipment = "it_equipment"
    services = "services"


class QuoteStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    follow_up_sent = "follow_up_sent"
    new_version_sent = "new_version_sent"
    waiting = "waiting"
    approved = "approved"
    declined = "declined"
    cancelled = "cancelled"
    expired = "expired"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    external_id = Column(String, nullable=True, index=True)  # legacy/source system ID, not guaranteed unique
    company_name = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    country = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    quotations = relationship("Quotation", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_type = Column(Enum(ProductType), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    unit_price = Column(Numeric(10, 2), nullable=False)
    unit = Column(String, nullable=False, default="pcs")  # "m2", "pcs", "day", "man", "km", ...

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    quote_number = Column(String, unique=True, nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    event_name = Column(String, nullable=True)
    event_venue = Column(String, nullable=True)
    event_start_date = Column(Date, nullable=True)
    event_end_date = Column(Date, nullable=True)
    event_dates_text = Column(String, nullable=True)  # free-text fallback, e.g. "3 Day Event-Dates TBD"

    status = Column(Enum(QuoteStatus), default=QuoteStatus.draft, nullable=False)
    currency = Column(String, default="EUR", nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    valid_until = Column(Date, nullable=True)

    # Header-level fields for quotes imported from historical records that don't have a
    # structured line-item breakdown — a single service description and a known total/discount.
    # Quotes created in-app instead compute their total from line_items (see QuotationOut.total).
    service_description = Column(Text, nullable=True)
    discount_amount = Column(Numeric(10, 2), nullable=True)
    historical_total_amount = Column(Numeric(10, 2), nullable=True)
    quotation_date_text = Column(String, nullable=True)  # e.g. "09/2025", source sheet's "Date of Quotation"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="quotations")
    created_by = relationship("User")
    line_items = relationship("QuoteLineItem", back_populates="quotation", cascade="all, delete-orphan", order_by="QuoteLineItem.sort_order")


class QuoteLineItem(Base):
    __tablename__ = "quote_line_items"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    quotation_id = Column(String(36), ForeignKey("quotations.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)

    # Snapshot fields — captured at add-time so edits to the product catalog
    # never silently change the price/description on an already-issued quote.
    description = Column(String, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)

    sort_order = Column(Integer, default=0, nullable=False)

    quotation = relationship("Quotation", back_populates="line_items")
    product = relationship("Product")

    @property
    def line_total(self):
        return self.quantity * self.unit_price
