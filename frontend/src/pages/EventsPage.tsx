import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createEvent, deleteEvent, getEvents, updateEvent } from "../api/endpoints";
import type { Event, EventInput } from "../types";

const emptyForm: EventInput = {
  name: "",
  venue: "",
  default_start_date: null,
  default_end_date: null,
};

function isPast(event: Event) {
  if (!event.default_start_date) return false;
  const todayIso = new Date().toISOString().slice(0, 10);
  return event.default_start_date < todayIso;
}

export default function EventsPage() {
  const [editing, setEditing] = useState<Event | null>(null);
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: events, isLoading, error } = useQuery({
    queryKey: ["events"],
    queryFn: () => getEvents(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["events"] });

  const createMutation = useMutation({
    mutationFn: (input: EventInput) => createEvent(input),
    onSuccess: () => { invalidate(); closeForm(); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<EventInput> }) => updateEvent(id, input),
    onSuccess: () => { invalidate(); closeForm(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteEvent(id),
    onSuccess: invalidate,
    onError: () => alert("Failed to delete event."),
  });

  function openCreate() {
    setEditing(null);
    setShowForm(true);
  }

  function openEdit(event: Event) {
    setEditing(event);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
  }

  function handleSubmit(input: EventInput) {
    if (editing) {
      updateMutation.mutate({ id: editing.id, input });
    } else {
      createMutation.mutate(input);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Events</h1>
        <button onClick={openCreate}>+ New Event</button>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load events.</p>}

      {events && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Venue</th>
              <th>Default Dates</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.id} className={isPast(ev) ? "past-event-row" : ""}>
                <td>{ev.name}</td>
                <td>{ev.venue || "—"}</td>
                <td>
                  {ev.default_start_date
                    ? `${new Date(ev.default_start_date).toLocaleDateString()}${
                        ev.default_end_date && ev.default_end_date !== ev.default_start_date
                          ? ` – ${new Date(ev.default_end_date).toLocaleDateString()}`
                          : ""
                      }`
                    : "—"}
                </td>
                <td className="row-actions">
                  <button onClick={() => openEdit(ev)}>Edit</button>
                  <button
                    className="danger"
                    onClick={() => { if (confirm(`Delete event "${ev.name}"?`)) deleteMutation.mutate(ev.id); }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr><td colSpan={4} className="empty-row">No events yet.</td></tr>
            )}
          </tbody>
        </table>
      )}

      {showForm && (
        <EventFormModal
          initial={editing ?? emptyForm}
          onCancel={closeForm}
          onSubmit={handleSubmit}
          saving={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

function EventFormModal({
  initial, onCancel, onSubmit, saving,
}: {
  initial: EventInput;
  onCancel: () => void;
  onSubmit: (input: EventInput) => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<EventInput>(initial);

  function set<K extends keyof EventInput>(key: K, value: EventInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <form
        className="modal-card"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(form);
        }}
      >
        <h2>{initial.name ? "Edit Event" : "New Event"}</h2>

        <label>
          Name *
          <input required value={form.name} onChange={(e) => set("name", e.target.value)} />
        </label>

        <label>
          Venue
          <input value={form.venue || ""} onChange={(e) => set("venue", e.target.value || null)} />
        </label>

        <div className="form-row">
          <label>
            Default Start Date
            <input
              type="date"
              value={form.default_start_date || ""}
              onChange={(e) => set("default_start_date", e.target.value || null)}
            />
          </label>
          <label>
            Default End Date
            <input
              type="date"
              value={form.default_end_date || ""}
              onChange={(e) => set("default_end_date", e.target.value || null)}
            />
          </label>
        </div>

        <div className="modal-actions">
          <button type="button" onClick={onCancel}>Cancel</button>
          <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
        </div>
      </form>
    </div>
  );
}
