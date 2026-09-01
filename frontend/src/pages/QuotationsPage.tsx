import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getQuotations } from "../api/endpoints";

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
};

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
};

export default function QuotationsPage() {
  const { data: quotations, isLoading, error } = useQuery({
    queryKey: ["quotations"],
    queryFn: getQuotations,
  });

  return (
    <div>
      <div className="page-header">
        <h1>Quotations</h1>
        <Link to="/quotations/new"><button>+ New Quotation</button></Link>
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
              <th>Status</th>
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
                <td><span className={`status-badge ${statusColors[q.status]}`}>{statusLabels[q.status]}</span></td>
                <td>{new Date(q.created_at).toLocaleDateString()}</td>
                <td className="row-actions">
                  <Link to={`/quotations/${q.id}`}><button>Open</button></Link>
                </td>
              </tr>
            ))}
            {quotations.length === 0 && (
              <tr><td colSpan={6} className="empty-row">No quotations yet.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
