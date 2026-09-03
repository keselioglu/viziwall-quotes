export type ProductType = "led_wall" | "displays" | "audio" | "it_equipment" | "services";
export type QuoteStatus =
  | "draft"
  | "sent"
  | "follow_up_sent"
  | "new_version_sent"
  | "waiting"
  | "approved"
  | "declined"
  | "cancelled"
  | "expired"
  | "archived";

export interface Customer {
  id: string;
  external_id: string | null;
  company_name: string | null;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  country: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type CustomerInput = Omit<Customer, "id" | "created_at" | "updated_at">;

export interface Product {
  id: string;
  product_type: ProductType;
  name: string;
  description: string | null;
  unit_price: string;
  unit: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type ProductInput = Omit<Product, "id" | "created_at" | "updated_at">;

export interface Event {
  id: string;
  name: string;
  venue: string | null;
  default_start_date: string | null;
  default_end_date: string | null;
  created_at: string;
  updated_at: string;
}

export type EventInput = Omit<Event, "id" | "created_at" | "updated_at">;

export interface QuoteLineItem {
  id: string;
  product_id: string | null;
  description: string;
  quantity: string;
  unit_price: string;
  sort_order: number;
  line_total: string;
  product_type: ProductType | null;
}

export type QuoteLineItemInput = Omit<QuoteLineItem, "id" | "line_total" | "product_type">;

export interface Quotation {
  id: string;
  quote_number: string;
  customer_id: string;
  event_name: string | null;
  event_venue: string | null;
  event_start_date: string | null;
  event_end_date: string | null;
  event_dates_text: string | null;
  status: QuoteStatus;
  currency: string;
  tax_rate_percent: string;
  advance_payment_percent: string | null;
  notes: string | null;
  valid_until: string | null;
  service_description: string | null;
  discount_amount: string | null;
  historical_total_amount: string | null;
  quotation_date_text: string | null;
  created_at: string;
  updated_at: string;
  line_items: QuoteLineItem[];
  customer: Customer;
  subtotal: string;
  tax_amount: string;
  total: string;
  advance_payment_amount: string | null;
}

export interface QuotationListItem {
  id: string;
  quote_number: string;
  status: QuoteStatus;
  event_name: string | null;
  event_venue: string | null;
  event_start_date: string | null;
  event_end_date: string | null;
  event_dates_text: string | null;
  created_at: string;
  customer: Customer;
  total: string;
}

export interface QuotationInput {
  customer_id: string;
  event_name: string | null;
  event_venue: string | null;
  event_start_date: string | null;
  event_end_date: string | null;
  event_dates_text: string | null;
  status: QuoteStatus;
  currency: string;
  tax_rate_percent: number;
  advance_payment_percent: number | null;
  notes: string | null;
  valid_until: string | null;
  service_description: string | null;
  discount_amount: number | null;
  historical_total_amount: number | null;
  quotation_date_text: string | null;
  line_items: QuoteLineItemInput[];
}
