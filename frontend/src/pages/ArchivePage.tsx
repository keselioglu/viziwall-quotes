import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getQuotations, restoreQuotation } from "../api/endpoints";

function formatEventDates(q: { event_dates_text: string | null; event_start_date: string | null; event_end_date: string | null }) {
  if (q.event_dates_text) return q.event_dates_text;
  if (!q.event_start_date) return "—";
  const start = new Date(q.event_start_date).toLocaleDateString();
  if (!q.event_end_date || q.event_end_date === q.event_start_date) return start;
  return `${start} – ${new Date(q.event_end_date).toLocaleDateString()}`;
}

export default function ArchivePage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");

  const { data: quotations, isLoading, error } = useQuery({
    queryKey: ["quotations", true],
    queryFn: () => getQuotations(true),
  });

  const archivedQuotations = useMemo(
    () => (quotations ?? []).filter((q) => q.status === "archived"),
    [quotations]
  );

  const restoreMutation = useMutation({
    mutationFn: (id: string) => restoreQuotation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotations"] }),
    onError: () => alert("Failed to restore quotation."),
  });

  const filteredQuotations = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return archivedQuotations;
    return archivedQuotations.filter((q) => {
      const haystack = `${q.quote_number} ${q.customer.company_name ?? ""} ${q.event_name ?? ""}`.toLowerCase();
      return haystack.includes(term);
    });
  }, [archivedQuotations, search]);

  return (
    <div>
      <div className="page-header">
        <h1>Archive</h1>
      </div>

      <div className="filter-bar">
        <input
          className="search-box"
          placeholder="Search quote #, customer, or event..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load archived quotations.</p>}

      {quotations && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Quote #</th>
              <th>Customer</th>
              <th>Event</th>
              <th>Venue</th>
              <th>Event Dates</th>
              <th>Total</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filteredQuotations.map((q) => (
              <tr key={q.id}>
                <td>{q.quote_number}</td>
                <td>{q.customer.company_name}</td>
                <td>{q.event_name || "—"}</td>
                <td>{q.event_venue || "—"}</td>
                <td>{formatEventDates(q)}</td>
                <td className="num-cell">{Number(q.total).toFixed(2)}</td>
                <td>{new Date(q.created_at).toLocaleDateString()}</td>
                <td className="row-actions">
                  <Link to={`/quotations/${q.id}`}><button>Open</button></Link>
                  <button
                    onClick={() => {
                      if (confirm(`Restore quotation ${q.quote_number}?`)) restoreMutation.mutate(q.id);
                    }}
                    disabled={restoreMutation.isPending}
                  >
                    Restore
                  </button>
                </td>
              </tr>
            ))}
            {filteredQuotations.length === 0 && (
              <tr><td colSpan={8} className="empty-row">No archived quotations.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
