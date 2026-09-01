import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCustomer, deleteCustomer, getCustomers, updateCustomer,
} from "../api/endpoints";
import type { Customer, CustomerInput } from "../types";

const emptyForm: Partial<CustomerInput> = {
  company_name: "", contact_name: "", email: "", phone: "", address: "", country: "", notes: "",
};

export default function CustomersPage() {
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Customer | null>(null);
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: customers, isLoading, error } = useQuery({
    queryKey: ["customers", search],
    queryFn: () => getCustomers(search || undefined),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["customers"] });

  const createMutation = useMutation({
    mutationFn: (input: Partial<CustomerInput>) => createCustomer(input),
    onSuccess: () => { invalidate(); closeForm(); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<CustomerInput> }) => updateCustomer(id, input),
    onSuccess: () => { invalidate(); closeForm(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCustomer(id),
    onSuccess: invalidate,
    onError: () => alert("Cannot delete this customer — they have existing quotations."),
  });

  function openCreate() {
    setEditing(null);
    setShowForm(true);
  }

  function openEdit(customer: Customer) {
    setEditing(customer);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
  }

  function handleSubmit(input: Partial<CustomerInput>) {
    if (editing) {
      updateMutation.mutate({ id: editing.id, input });
    } else {
      createMutation.mutate(input);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Customers</h1>
        <button onClick={openCreate}>+ New Customer</button>
      </div>

      <input
        className="search-box"
        placeholder="Search by company, contact, or email..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load customers.</p>}

      {customers && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Contact</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Country</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id}>
                <td>{c.company_name || <span className="muted">(no company)</span>}</td>
                <td>{c.contact_name || "—"}</td>
                <td>{c.email || "—"}</td>
                <td>{c.phone || "—"}</td>
                <td>{c.country || "—"}</td>
                <td className="row-actions">
                  <button onClick={() => openEdit(c)}>Edit</button>
                  <button
                    className="danger"
                    onClick={() => {
                      if (confirm(`Delete ${c.company_name || c.contact_name}?`)) deleteMutation.mutate(c.id);
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {customers.length === 0 && (
              <tr><td colSpan={6} className="empty-row">No customers yet.</td></tr>
            )}
          </tbody>
        </table>
      )}

      {showForm && (
        <CustomerFormModal
          initial={editing ?? emptyForm}
          isEditing={!!editing}
          onCancel={closeForm}
          onSubmit={handleSubmit}
          saving={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

function CustomerFormModal({
  initial, isEditing, onCancel, onSubmit, saving,
}: {
  initial: Partial<CustomerInput>;
  isEditing: boolean;
  onCancel: () => void;
  onSubmit: (input: Partial<CustomerInput>) => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<Partial<CustomerInput>>(initial);

  function set<K extends keyof CustomerInput>(key: K, value: CustomerInput[K]) {
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
        <h2>{isEditing ? "Edit Customer" : "New Customer"}</h2>
        <label>
          Company Name *
          <input required value={form.company_name || ""} onChange={(e) => set("company_name", e.target.value)} />
        </label>
        <label>
          Contact Name
          <input value={form.contact_name || ""} onChange={(e) => set("contact_name", e.target.value)} />
        </label>
        <label>
          Email
          <input type="email" value={form.email || ""} onChange={(e) => set("email", e.target.value)} />
        </label>
        <label>
          Phone
          <input value={form.phone || ""} onChange={(e) => set("phone", e.target.value)} />
        </label>
        <label>
          Country
          <input value={form.country || ""} onChange={(e) => set("country", e.target.value)} />
        </label>
        <label>
          Address
          <textarea value={form.address || ""} onChange={(e) => set("address", e.target.value)} />
        </label>
        <label>
          Notes
          <textarea value={form.notes || ""} onChange={(e) => set("notes", e.target.value)} />
        </label>
        <div className="modal-actions">
          <button type="button" onClick={onCancel}>Cancel</button>
          <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
        </div>
      </form>
    </div>
  );
}
