import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  archiveQuotation, createQuotation, getQuotation, getQuotations, updateQuotation,
} from "../api/endpoints";
import { openQuotationView } from "../viewQuotation";
import type { QuotationInput, QuoteStatus } from "../types";

const statusColors: Record<string, string> = {
  draft: "status-draft",
  sent: "status-sent",
  follow_up_sent: "status-sent",
  new_version_sent: "status-sent",
  waiting: "status-waiting",
  approved: "status-accepted",
  declined: "status-rejected",
  cancelled: "status-rejected",
  expired: "status-expired",
  archived: "status-archived",
};

const statusLabels: Record<string, string> = {
  draft: "Draft",
  sent: "Sent",
  follow_up_sent: "Follow up sent",
  new_version_sent: "Active",
  waiting: "Waiting",
  approved: "Approved",
  declined: "Declined",
  cancelled: "Cancelled",
  expired: "Expired",
  archived: "Archived",
};

const STATUS_OPTIONS = (Object.keys(statusLabels) as QuoteStatus[]).filter((s) => s !== "archived");

function isPastEvent(q: { event_start_date: string | null }) {
  if (!q.event_start_date) return false;
  const todayIso = new Date().toISOString().slice(0, 10);
  return q.event_start_date < todayIso;
}

function formatEventDates(q: { event_dates_text: string | null; event_start_date: string | null; event_end_date: string | null }) {
  if (q.event_dates_text) return q.event_dates_text;
  if (!q.event_start_date) return "—";
  const start = new Date(q.event_start_date).toLocaleDateString();
  if (!q.event_end_date || q.event_end_date === q.event_start_date) return start;
  return `${start} – ${new Date(q.event_end_date).toLocaleDateString()}`;
}

export default function QuotationsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<Set<QuoteStatus>>(new Set());
  const [statusMenuOpen, setStatusMenuOpen] = useState(false);
  const [customerFilter, setCustomerFilter] = useState("");
  const [eventFilter, setEventFilter] = useState("");
  const statusMenuRef = useRef<HTMLDivElement>(null);

  const { data: quotations, isLoading, error } = useQuery({
    queryKey: ["quotations", false],
    queryFn: () => getQuotations(false),
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => archiveQuotation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotations"] }),
    onError: () => alert("Failed to archive quotation."),
  });

  const statusChangeMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: QuoteStatus }) => updateQuotation(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotations"] }),
    onError: () => alert("Failed to update status."),
  });

  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const source = await getQuotation(id);
      const input: QuotationInput = {
        customer_id: source.customer_id,
        event_name: source.event_name,
        event_venue: source.event_venue,
        event_start_date: source.event_start_date,
        event_end_date: source.event_end_date,
        event_dates_text: source.event_dates_text,
        status: "draft",
        currency: source.currency,
        tax_rate_percent: Number(source.tax_rate_percent),
        advance_payment_percent: source.advance_payment_percent ? Number(source.advance_payment_percent) : null,
        notes: source.notes,
        valid_until: null,
        service_description: source.service_description,
        discount_amount: source.discount_amount ? Number(source.discount_amount) : null,
        historical_total_amount: null,
        quotation_date_text: null,
        contact_name: source.contact_name,
        contact_email: source.contact_email,
        line_items: source.line_items.map((li, idx) => ({
          product_id: li.product_id,
          description: li.description,
          quantity: li.quantity,
          unit_price: li.unit_price,
          sort_order: idx,
        })),
      };
      return createQuotation(input);
    },
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["quotations"] });
      navigate(`/quotations/${created.id}`);
    },
    onError: () => alert("Failed to duplicate quotation."),
  });

  const statusOptions = useMemo(() => {
    const present = new Set((quotations ?? []).map((q) => q.status));
    return STATUS_OPTIONS.filter((s) => present.has(s));
  }, [quotations]);

  const customerOptions = useMemo(() => {
    const names = new Set((quotations ?? []).map((q) => q.customer.company_name).filter(Boolean) as string[]);
    return Array.from(names).sort();
  }, [quotations]);

  const eventOptions = useMemo(() => {
    const latestDateByName = new Map<string, string>();
    for (const q of quotations ?? []) {
      if (!q.event_name) continue;
      const current = latestDateByName.get(q.event_name);
      if (q.event_start_date && (!current || q.event_start_date > current)) {
        latestDateByName.set(q.event_name, q.event_start_date);
      } else if (!latestDateByName.has(q.event_name)) {
        latestDateByName.set(q.event_name, "");
      }
    }
    return Array.from(latestDateByName.entries())
      .sort((a, b) => b[1].localeCompare(a[1]))
      .map(([name]) => name);
  }, [quotations]);

  const filteredQuotations = useMemo(() => {
    const term = search.trim().toLowerCase();
    const filtered = (quotations ?? []).filter((q) => {
      if (statusFilter.size > 0 && !statusFilter.has(q.status)) return false;
      if (customerFilter && q.customer.company_name !== customerFilter) return false;
      if (eventFilter && q.event_name !== eventFilter) return false;
      if (term) {
        const haystack = `${q.quote_number} ${q.customer.company_name ?? ""} ${q.event_name ?? ""}`.toLowerCase();
        if (!haystack.includes(term)) return false;
      }
      return true;
    });
    return [...filtered].sort((a, b) => {
      if (!a.event_start_date && !b.event_start_date) return 0;
      if (!a.event_start_date) return 1;
      if (!b.event_start_date) return -1;
      return b.event_start_date.localeCompare(a.event_start_date);
    });
  }, [quotations, search, statusFilter, customerFilter, eventFilter]);

  function handleStatusChange(id: string, quoteNumber: string, newStatus: QuoteStatus) {
    if (confirm(`Change status of ${quoteNumber} to "${statusLabels[newStatus]}"?`)) {
      statusChangeMutation.mutate({ id, status: newStatus });
    }
  }

  function toggleStatusFilter(status: QuoteStatus) {
    setStatusFilter((prev) => {
      const next = new Set(prev);
      if (next.has(status)) next.delete(status);
      else next.add(status);
      return next;
    });
  }

  useEffect(() => {
    if (!statusMenuOpen) return;
    function handleClickOutside(e: MouseEvent) {
      if (statusMenuRef.current && !statusMenuRef.current.contains(e.target as Node)) {
        setStatusMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [statusMenuOpen]);

  return (
    <div>
      <div className="page-header">
        <h1>Quotations</h1>
        <div className="header-actions">
          <Link to="/quotations/new"><button>+ New Quotation</button></Link>
        </div>
      </div>

      <div className="filter-bar">
        <input
          className="search-box"
          placeholder="Search quote #, customer, or event..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="status-filter" ref={statusMenuRef}>
          <button type="button" onClick={() => setStatusMenuOpen((open) => !open)}>
            {statusFilter.size === 0 ? "All statuses" : `${statusFilter.size} status${statusFilter.size > 1 ? "es" : ""}`}
          </button>
          {statusMenuOpen && (
            <div className="status-filter-menu">
              {statusOptions.map((s) => (
                <label key={s} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={statusFilter.has(s)}
                    onChange={() => toggleStatusFilter(s)}
                  />
                  {statusLabels[s]}
                </label>
              ))}
            </div>
          )}
        </div>
        <select value={customerFilter} onChange={(e) => setCustomerFilter(e.target.value)}>
          <option value="">All customers</option>
          {customerOptions.map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
        <select value={eventFilter} onChange={(e) => setEventFilter(e.target.value)}>
          <option value="">All events</option>
          {eventOptions.map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
        {(search || statusFilter.size > 0 || customerFilter || eventFilter) && (
          <button
            type="button"
            className="link-button"
            onClick={() => { setSearch(""); setStatusFilter(new Set()); setCustomerFilter(""); setEventFilter(""); }}
          >
            Clear filters
          </button>
        )}
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load quotations.</p>}

      {quotations && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Quote #</th>
              <th>Customer</th>
              <th>Event</th>
              <th>Venue</th>
              <th>Event Dates</th>
              <th>Status</th>
              <th>Total</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filteredQuotations.map((q) => (
              <tr key={q.id} className={isPastEvent(q) ? "past-event-row" : ""}>
                <td>{q.quote_number}</td>
                <td>{q.customer.company_name}</td>
                <td>{q.event_name || "—"}</td>
                <td>{q.event_venue || "—"}</td>
                <td>{formatEventDates(q)}</td>
                <td>
                  <select
                    className={`status-select ${statusColors[q.status]}`}
                    value={q.status}
                    disabled={statusChangeMutation.isPending}
                    onChange={(e) => handleStatusChange(q.id, q.quote_number, e.target.value as QuoteStatus)}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{statusLabels[s]}</option>
                    ))}
                  </select>
                </td>
                <td className="num-cell">{Number(q.total).toFixed(2)}</td>
                <td>{new Date(q.created_at).toLocaleDateString()}</td>
                <td className="row-actions">
                  <Link to={`/quotations/${q.id}`}><button>Open</button></Link>
                  <button
                    onClick={() => {
                      openQuotationView(q.id).catch(() => alert("Could not open the quotation preview."));
                    }}
                  >
                    View
                  </button>
                  <button
                    onClick={() => duplicateMutation.mutate(q.id)}
                    disabled={duplicateMutation.isPending}
                  >
                    Duplicate
                  </button>
                  <button
                    className="danger"
                    onClick={() => {
                      if (confirm(`Archive quotation ${q.quote_number}?`)) archiveMutation.mutate(q.id);
                    }}
                  >
                    Archive
                  </button>
                </td>
              </tr>
            ))}
            {filteredQuotations.length === 0 && (
              <tr><td colSpan={9} className="empty-row">No quotations match these filters.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
