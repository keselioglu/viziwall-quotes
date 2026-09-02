import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getQuotations } from "../api/endpoints";
import type { QuotationListItem, QuoteStatus } from "../types";

const ACTIVE_STATUSES: QuoteStatus[] = [
  "draft", "sent", "follow_up_sent", "new_version_sent", "waiting", "approved",
];

const statusColors: Record<string, string> = {
  draft: "status-draft",
  sent: "status-sent",
  follow_up_sent: "status-sent",
  new_version_sent: "status-sent",
  waiting: "status-waiting",
  approved: "status-accepted",
};

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTH_LABELS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function toDateOnly(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function isoDay(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function buildMonthGrid(year: number, month: number) {
  const firstOfMonth = new Date(year, month, 1);
  const startOffset = (firstOfMonth.getDay() + 6) % 7; // Monday-first
  const gridStart = new Date(year, month, 1 - startOffset);
  const days: Date[] = [];
  for (let i = 0; i < 42; i++) {
    days.push(new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i));
  }
  return days;
}

export default function SchedulePage() {
  const { data: quotations, isLoading, error } = useQuery({
    queryKey: ["quotations", false],
    queryFn: () => getQuotations(false),
  });

  const activeQuotations = useMemo(
    () => (quotations ?? []).filter((q) => ACTIVE_STATUSES.includes(q.status)),
    [quotations]
  );

  const { scheduled, unscheduled } = useMemo(() => {
    const scheduled: QuotationListItem[] = [];
    const unscheduled: QuotationListItem[] = [];
    for (const q of activeQuotations) {
      if (q.event_start_date) scheduled.push(q);
      else unscheduled.push(q);
    }
    return { scheduled, unscheduled };
  }, [activeQuotations]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, QuotationListItem[]>();
    for (const q of scheduled) {
      const start = toDateOnly(q.event_start_date!);
      const end = q.event_end_date ? toDateOnly(q.event_end_date) : start;
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const key = isoDay(d);
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(q);
      }
    }
    return map;
  }, [scheduled]);

  const today = new Date();
  const months = [0, 1, 2].map((offset) => {
    const d = new Date(today.getFullYear(), today.getMonth() + offset, 1);
    return { year: d.getFullYear(), month: d.getMonth() };
  });
  const todayKey = isoDay(today);

  return (
    <div>
      <div className="page-header">
        <h1>Schedule</h1>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load quotations.</p>}

      <div className="schedule-scroll">
        {months.map(({ year, month }) => (
          <div className="schedule-month" key={`${year}-${month}`}>
            <h2 className="section-title">{MONTH_LABELS[month]} {year}</h2>
            <div className="schedule-grid schedule-weekdays">
              {WEEKDAY_LABELS.map((w) => <div key={w} className="schedule-weekday">{w}</div>)}
            </div>
            <div className="schedule-grid">
              {buildMonthGrid(year, month).map((day) => {
                const key = isoDay(day);
                const inMonth = day.getMonth() === month;
                const events = eventsByDay.get(key) ?? [];
                return (
                  <div
                    key={key}
                    className={`schedule-day ${inMonth ? "" : "schedule-day-outside"} ${key === todayKey ? "schedule-day-today" : ""}`}
                  >
                    <span className="schedule-day-number">{day.getDate()}</span>
                    <div className="schedule-day-events">
                      {events.map((q) => (
                        <Link
                          key={q.id}
                          to={`/quotations/${q.id}`}
                          className={`schedule-chip ${statusColors[q.status]}`}
                          title={`${q.event_name || q.quote_number} — ${q.event_venue || ""}`}
                        >
                          <span className="schedule-chip-name">{q.event_name || q.quote_number}</span>
                          {q.event_venue && <span className="schedule-chip-venue">{q.event_venue}</span>}
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {unscheduled.length > 0 && (
        <>
          <h2 className="section-title">Unscheduled (no fixed date)</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Quote #</th>
                <th>Event</th>
                <th>Venue</th>
                <th>Dates</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {unscheduled.map((q) => (
                <tr key={q.id}>
                  <td>{q.quote_number}</td>
                  <td>{q.event_name || "—"}</td>
                  <td>{q.event_venue || "—"}</td>
                  <td>{q.event_dates_text || "—"}</td>
                  <td><span className={`status-badge ${statusColors[q.status]}`}>{q.status}</span></td>
                  <td><Link to={`/quotations/${q.id}`}><button>Open</button></Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
