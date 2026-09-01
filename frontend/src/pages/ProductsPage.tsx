import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createProduct, deleteProduct, getProducts, updateProduct } from "../api/endpoints";
import type { Product, ProductInput, ProductType } from "../types";

const emptyForm: ProductInput = {
  product_type: "led_wall",
  name: "",
  description: "",
  pixel_pitch_mm: null,
  panel_width_mm: null,
  panel_height_mm: null,
  resolution_width_px: null,
  resolution_height_px: null,
  price_per_day: "0",
  price_per_week: null,
  unit: "day",
  is_active: true,
};

export default function ProductsPage() {
  const [editing, setEditing] = useState<Product | null>(null);
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: products, isLoading, error } = useQuery({
    queryKey: ["products"],
    queryFn: () => getProducts(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["products"] });

  const createMutation = useMutation({
    mutationFn: (input: ProductInput) => createProduct(input),
    onSuccess: () => { invalidate(); closeForm(); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<ProductInput> }) => updateProduct(id, input),
    onSuccess: () => { invalidate(); closeForm(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProduct(id),
    onSuccess: invalidate,
  });

  function openCreate() {
    setEditing(null);
    setShowForm(true);
  }

  function openEdit(product: Product) {
    setEditing(product);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
  }

  function handleSubmit(input: ProductInput) {
    if (editing) {
      updateMutation.mutate({ id: editing.id, input });
    } else {
      createMutation.mutate(input);
    }
  }

  const ledWalls = products?.filter((p) => p.product_type === "led_wall") ?? [];
  const logistics = products?.filter((p) => p.product_type === "logistics") ?? [];

  return (
    <div>
      <div className="page-header">
        <h1>Products</h1>
        <button onClick={openCreate}>+ New Product</button>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load products.</p>}

      {products && (
        <>
          <h2 className="section-title">LED Wall Panels</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Pixel Pitch</th>
                <th>Panel Size</th>
                <th>Price / Day</th>
                <th>Price / Week</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {ledWalls.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.pixel_pitch_mm ? `P${p.pixel_pitch_mm}` : "—"}</td>
                  <td>{p.panel_width_mm && p.panel_height_mm ? `${p.panel_width_mm}×${p.panel_height_mm}mm` : "—"}</td>
                  <td>{p.price_per_day} €</td>
                  <td>{p.price_per_week ? `${p.price_per_week} €` : "—"}</td>
                  <td className="row-actions">
                    <button onClick={() => openEdit(p)}>Edit</button>
                    <button
                      className="danger"
                      onClick={() => { if (confirm(`Deactivate ${p.name}?`)) deleteMutation.mutate(p.id); }}
                    >
                      Deactivate
                    </button>
                  </td>
                </tr>
              ))}
              {ledWalls.length === 0 && <tr><td colSpan={6} className="empty-row">No LED wall products yet.</td></tr>}
            </tbody>
          </table>

          <h2 className="section-title">Logistics &amp; Services</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Unit</th>
                <th>Price</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {logistics.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.unit}</td>
                  <td>{p.price_per_day} €</td>
                  <td className="row-actions">
                    <button onClick={() => openEdit(p)}>Edit</button>
                    <button
                      className="danger"
                      onClick={() => { if (confirm(`Deactivate ${p.name}?`)) deleteMutation.mutate(p.id); }}
                    >
                      Deactivate
                    </button>
                  </td>
                </tr>
              ))}
              {logistics.length === 0 && <tr><td colSpan={4} className="empty-row">No logistics products yet.</td></tr>}
            </tbody>
          </table>
        </>
      )}

      {showForm && (
        <ProductFormModal
          initial={editing ?? emptyForm}
          onCancel={closeForm}
          onSubmit={handleSubmit}
          saving={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

function ProductFormModal({
  initial, onCancel, onSubmit, saving,
}: {
  initial: ProductInput;
  onCancel: () => void;
  onSubmit: (input: ProductInput) => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<ProductInput>(initial);

  function set<K extends keyof ProductInput>(key: K, value: ProductInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  const isLedWall = form.product_type === "led_wall";

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
        <h2>{initial.name ? "Edit Product" : "New Product"}</h2>

        <label>
          Type *
          <select
            value={form.product_type}
            onChange={(e) => set("product_type", e.target.value as ProductType)}
          >
            <option value="led_wall">LED Wall Panel</option>
            <option value="logistics">Logistics / Service</option>
          </select>
        </label>

        <label>
          Name *
          <input required value={form.name} onChange={(e) => set("name", e.target.value)} />
        </label>

        <label>
          Description
          <textarea value={form.description || ""} onChange={(e) => set("description", e.target.value)} />
        </label>

        {isLedWall && (
          <>
            <div className="form-row">
              <label>
                Pixel Pitch (mm)
                <input
                  type="number" step="0.1"
                  value={form.pixel_pitch_mm ?? ""}
                  onChange={(e) => set("pixel_pitch_mm", e.target.value || null)}
                />
              </label>
              <label>
                Panel Width (mm)
                <input
                  type="number"
                  value={form.panel_width_mm ?? ""}
                  onChange={(e) => set("panel_width_mm", e.target.value ? Number(e.target.value) : null)}
                />
              </label>
              <label>
                Panel Height (mm)
                <input
                  type="number"
                  value={form.panel_height_mm ?? ""}
                  onChange={(e) => set("panel_height_mm", e.target.value ? Number(e.target.value) : null)}
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                Resolution Width (px)
                <input
                  type="number"
                  value={form.resolution_width_px ?? ""}
                  onChange={(e) => set("resolution_width_px", e.target.value ? Number(e.target.value) : null)}
                />
              </label>
              <label>
                Resolution Height (px)
                <input
                  type="number"
                  value={form.resolution_height_px ?? ""}
                  onChange={(e) => set("resolution_height_px", e.target.value ? Number(e.target.value) : null)}
                />
              </label>
            </div>
          </>
        )}

        <div className="form-row">
          <label>
            Price / Day *
            <input
              required type="number" step="0.01"
              value={form.price_per_day}
              onChange={(e) => set("price_per_day", e.target.value)}
            />
          </label>
          {isLedWall && (
            <label>
              Price / Week
              <input
                type="number" step="0.01"
                value={form.price_per_week ?? ""}
                onChange={(e) => set("price_per_week", e.target.value || null)}
              />
            </label>
          )}
          <label>
            Unit
            <select value={form.unit} onChange={(e) => set("unit", e.target.value)}>
              <option value="day">per day</option>
              <option value="week">per week</option>
              <option value="flat">flat fee</option>
              <option value="unit">per unit</option>
            </select>
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
