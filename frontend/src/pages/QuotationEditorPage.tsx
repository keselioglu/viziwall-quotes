import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createQuotation, getCustomers, getProducts, getQuotation, updateQuotation,
} from "../api/endpoints";
import { api } from "../api/client";
import type { Product, QuoteLineItemInput, QuoteStatus, QuotationInput } from "../types";

interface DraftLineItem extends QuoteLineItemInput {
  key: string;
}

function newLineItem(): DraftLineItem {
  return {
    key: crypto.randomUUID(),
    product_id: null,
    description: "",
    quantity: "1",
    unit_price: "0",
    sort_order: 0,
  };
}

export default function QuotationEditorPage() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ["quotation", id],
    queryFn: () => getQuotation(id!),
    enabled: !isNew,
  });

  const { data: customers } = useQuery({ queryKey: ["customers"], queryFn: () => getCustomers() });
  const { data: products } = useQuery({ queryKey: ["products"], queryFn: () => getProducts() });

  const [customerId, setCustomerId] = useState("");
  const [eventName, setEventName] = useState("");
  const [eventVenue, setEventVenue] = useState("");
  const [eventStart, setEventStart] = useState("");
  const [eventEnd, setEventEnd] = useState("");
  const [status, setStatus] = useState<QuoteStatus>("draft");
  const [currency, setCurrency] = useState("EUR");
  const [taxRate, setTaxRate] = useState("0");
  const [notes, setNotes] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [items, setItems] = useState<DraftLineItem[]>([newLineItem()]);
  const [pdfError, setPdfError] = useState<string | null>(null);

  useEffect(() => {
    if (!existing) return;
    setCustomerId(existing.customer_id);
    setEventName(existing.event_name || "");
    setEventVenue(existing.event_venue || "");
    setEventStart(existing.event_start_date || "");
    setEventEnd(existing.event_end_date || "");
    setStatus(existing.status);
    setCurrency(existing.currency);
    setTaxRate(existing.tax_rate_percent);
    setNotes(existing.notes || "");
    setValidUntil(existing.valid_until || "");
    setItems(
      existing.line_items.length
        ? existing.line_items.map((li) => ({ ...li, key: li.id }))
        : [newLineItem()]
    );
  }, [existing]);

  const saveMutation = useMutation({
    mutationFn: (input: QuotationInput) =>
      isNew ? createQuotation(input) : updateQuotation(id!, input),
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ["quotations"] });
      queryClient.invalidateQueries({ queryKey: ["quotation", saved.id] });
      navigate(`/quotations/${saved.id}`);
    },
  });

  function updateItem(key: string, patch: Partial<DraftLineItem>) {
    setItems((prev) => prev.map((it) => (it.key === key ? { ...it, ...patch } : it)));
  }

  function removeItem(key: string) {
    setItems((prev) => prev.filter((it) => it.key !== key));
  }

  function addItem() {
    setItems((prev) => [...prev, newLineItem()]);
  }

  function pickProduct(key: string, productId: string) {
    const product = products?.find((p) => p.id === productId);
    if (!product) {
      updateItem(key, { product_id: null });
      return;
    }
    updateItem(key, {
      product_id: product.id,
      description: product.description || product.name,
      unit_price: product.price_per_day,
    });
  }

  function computeTotals() {
    const subtotal = items.reduce((sum, it) => {
      const qty = parseFloat(it.quantity) || 0;
      const price = parseFloat(it.unit_price) || 0;
      return sum + qty * price;
    }, 0);
    const tax = subtotal * ((parseFloat(taxRate) || 0) / 100);
    return { subtotal, tax, total: subtotal + tax };
  }

  function handleSave() {
    if (!customerId) {
      alert("Please select a customer.");
      return;
    }
    const input: QuotationInput = {
      customer_id: customerId,
      event_name: eventName || null,
      event_venue: eventVenue || null,
      event_start_date: eventStart || null,
      event_end_date: eventEnd || null,
      event_dates_text: null,
      status,
      currency,
      tax_rate_percent: parseFloat(taxRate) || 0,
      notes: notes || null,
      valid_until: validUntil || null,
      service_description: null,
      discount_amount: null,
      historical_total_amount: null,
      quotation_date_text: null,
      line_items: items.map((it, idx) => ({
        product_id: it.product_id,
        description: it.description,
        quantity: it.quantity,
        unit_price: it.unit_price,
        sort_order: idx,
      })),
    };
    saveMutation.mutate(input);
  }

  async function handleDownloadPdf() {
    if (!id || isNew) return;
    setPdfError(null);
    try {
      const response = await api.get(`/quotations/${id}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${existing?.quote_number || "quotation"}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setPdfError("Could not generate PDF. Please try again.");
    }
  }

  const { subtotal, tax, total } = computeTotals();

  return (
    <div>
      <div className="page-header">
        <h1>{isNew ? "New Quotation" : existing?.quote_number || "Quotation"}</h1>
        <div className="header-actions">
          {!isNew && (
            <button onClick={handleDownloadPdf}>Download PDF</button>
          )}
          <button onClick={handleSave} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
      {pdfError && <p className="form-error">{pdfError}</p>}
      {saveMutation.isError && <p className="form-error">Failed to save quotation.</p>}

      <div className="quote-form-grid">
        <label>
          Customer *
          <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
            <option value="">Select a customer...</option>
            {customers?.map((c) => (
              <option key={c.id} value={c.id}>{c.company_name}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value as QuoteStatus)}>
            <option value="draft">Draft</option>
            <option value="sent">Sent</option>
            <option value="follow_up_sent">Follow up sent</option>
            <option value="new_version_sent">New version sent</option>
            <option value="waiting">Waiting</option>
            <option value="approved">Approved</option>
            <option value="declined">Declined</option>
            <option value="cancelled">Cancelled</option>
            <option value="expired">Expired</option>
            <option value="archived">Archived</option>
          </select>
        </label>
        <label>
          Event Name
          <input value={eventName} onChange={(e) => setEventName(e.target.value)} />
        </label>
        <label>
          Venue
          <input value={eventVenue} onChange={(e) => setEventVenue(e.target.value)} />
        </label>
        <label>
          Event Start
          <input type="date" value={eventStart} onChange={(e) => setEventStart(e.target.value)} />
        </label>
        <label>
          Event End
          <input type="date" value={eventEnd} onChange={(e) => setEventEnd(e.target.value)} />
        </label>
        <label>
          Currency
          <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
            <option value="EUR">EUR</option>
            <option value="USD">USD</option>
            <option value="GBP">GBP</option>
          </select>
        </label>
        <label>
          Tax Rate (%)
          <input type="number" step="0.01" value={taxRate} onChange={(e) => setTaxRate(e.target.value)} />
        </label>
        <label>
          Valid Until
          <input type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
        </label>
      </div>

      <h2 className="section-title">Line Items</h2>
      <table className="data-table line-items-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Description</th>
            <th>Qty</th>
            <th>Unit Price</th>
            <th>Line Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const qty = parseFloat(item.quantity) || 0;
            const price = parseFloat(item.unit_price) || 0;
            const lineTotal = qty * price;
            const unit = products?.find((p) => p.id === item.product_id)?.unit;
            return (
              <tr key={item.key}>
                <td className="col-product">
                  <select
                    value={item.product_id || ""}
                    onChange={(e) => pickProduct(item.key, e.target.value)}
                  >
                    <option value="">Custom line item</option>
                    {products?.map((p: Product) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </td>
                <td className="col-description">
                  <input
                    value={item.description}
                    onChange={(e) => updateItem(item.key, { description: e.target.value })}
                  />
                </td>
                <td>
                  <div className="qty-with-unit">
                    <input
                      type="number" step="0.01" className="num-input"
                      value={item.quantity}
                      onChange={(e) => updateItem(item.key, { quantity: e.target.value })}
                    />
                    {unit && <span className="unit-label">{unit}</span>}
                  </div>
                </td>
                <td>
                  <input
                    type="number" step="0.01" className="num-input"
                    value={item.unit_price}
                    onChange={(e) => updateItem(item.key, { unit_price: e.target.value })}
                  />
                </td>
                <td className="num-cell">{lineTotal.toFixed(2)} {currency}</td>
                <td>
                  <button className="danger" onClick={() => removeItem(item.key)}>×</button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <button onClick={addItem}>+ Add Line Item</button>

      <div className="quote-totals">
        <div><span>Subtotal</span><span>{subtotal.toFixed(2)} {currency}</span></div>
        <div><span>Tax ({taxRate || 0}%)</span><span>{tax.toFixed(2)} {currency}</span></div>
        <div className="total-line"><span>Total</span><span>{total.toFixed(2)} {currency}</span></div>
      </div>

      <label className="notes-field">
        Notes
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
    </div>
  );
}
