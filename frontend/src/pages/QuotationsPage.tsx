import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  archiveQuotation, createQuotation, getQuotation, getQuotations, restoreQuotation,
} from "../api/endpoints";
import type { QuotationInput } from "../types";

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

function formatEventDates(q: { event_dates_text: string | null; event_start_date: string | null; event_end_date: string | null }) {
  if (q.event_dates_text) return q.event_dates_text;
  if (!q.event_start_date) return "—";
  const start = new Date(q.event_start_date).toLocaleDateString();
  if (!q.event_end_date || q.event_end_date === q.event_start_date) return start;
  return `${start} – ${new Date(q.event_end_date).toLocaleDateString()}`;
}

const statusLabels: Record<string, string> = {
  draft: "Draft",
  sent: "Sent",
  follow_up_sent: "Follow up sent",
  new_version_sent: "New version sent",
  waiting: "Waiting",
  approved: "Approved",
  declined: "Declined",
  cancelled: "Cancelled",
  expired: "Expired",
  archived: "Archived",
};

export default function QuotationsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showArchived, setShowArchived] = useState(false);

  const { data: quotations, isLoading, error } = useQuery({
    queryKey: ["quotations", showArchived],
    queryFn: () => getQuotations(showArchived),
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => archiveQuotation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotations"] }),
    onError: () => alert("Failed to archive quotation."),
  });

  const restoreMutation = useMutation({
    mutationFn: (id: string) => restoreQuotation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotations"] }),
    onError: () => alert("Failed to restore quotation."),
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
        notes: source.notes,
        valid_until: null,
        service_description: source.service_description,
        discount_amount: source.discount_amount ? Number(source.discount_amount) : null,
        historical_total_amount: null,
        quotation_date_text: null,
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

  return (
    <div>
      <div className="page-header">
        <h1>Quotations</h1>
        <div className="header-actions">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            Show archived
          </label>
          <Link to="/quotations/new"><button>+ New Quotation</button></Link>
        </div>
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
            {quotations.map((q) => (
              <tr key={q.id}>
                <td>{q.quote_number}</td>
                <td>{q.customer.company_name}</td>
                <td>{q.event_name || "—"}</td>
                <td>{q.event_venue || "—"}</td>
                <td>{formatEventDates(q)}</td>
                <td><span className={`status-badge ${statusColors[q.status]}`}>{statusLabels[q.status]}</span></td>
                <td className="num-cell">{Number(q.total).toFixed(2)}</td>
                <td>{new Date(q.created_at).toLocaleDateString()}</td>
                <td className="row-actions">
                  <Link to={`/quotations/${q.id}`}><button>Open</button></Link>
                  <button
                    onClick={() => duplicateMutation.mutate(q.id)}
                    disabled={duplicateMutation.isPending}
                  >
                    Duplicate
                  </button>
                  {q.status === "archived" ? (
                    <button onClick={() => restoreMutation.mutate(q.id)} disabled={restoreMutation.isPending}>
                      Restore
                    </button>
                  ) : (
                    <button
                      className="danger"
                      onClick={() => {
                        if (confirm(`Archive quotation ${q.quote_number}?`)) archiveMutation.mutate(q.id);
                      }}
                    >
                      Archive
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {quotations.length === 0 && (
              <tr><td colSpan={9} className="empty-row">No quotations yet.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
