import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createProduct, deleteProduct, getProducts, updateProduct } from "../api/endpoints";
import type { Product, ProductInput, ProductType } from "../types";

const emptyForm: ProductInput = {
  product_type: "led_wall",
  name: "",
  description: "",
  unit_price: "0",
  unit: "pcs",
  is_active: true,
};

const categories: { type: ProductType; label: string }[] = [
  { type: "led_wall", label: "LED Wall Panels & Accessories" },
  { type: "displays", label: "TVs & Touch Screen Displays" },
  { type: "audio", label: "Audio" },
  { type: "it_equipment", label: "Laptops & Tablets" },
  { type: "services", label: "Services" },
];

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

  return (
    <div>
      <div className="page-header">
        <h1>Products</h1>
        <button onClick={openCreate}>+ New Product</button>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">Failed to load products.</p>}

      {products && categories.map(({ type, label }) => {
        const items = products.filter((p) => p.product_type === type);
        return (
          <div key={type}>
            <h2 className="section-title">{label}</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Unit</th>
                  <th>Price</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id}>
                    <td>{p.name}</td>
                    <td>{p.description || "—"}</td>
                    <td>{p.unit}</td>
                    <td>{p.unit_price} €</td>
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
                {items.length === 0 && (
                  <tr><td colSpan={5} className="empty-row">No products in this category yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        );
      })}

      {showForm && (
        <ProductFormModal
          initial={editing ?? emptyForm}
          existingUnits={Array.from(new Set(products?.map((p) => p.unit) ?? [])).sort()}
          onCancel={closeForm}
          onSubmit={handleSubmit}
          saving={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

const ADD_NEW_UNIT = "__add_new_unit__";

function ProductFormModal({
  initial, existingUnits, onCancel, onSubmit, saving,
}: {
  initial: ProductInput;
  existingUnits: string[];
  onCancel: () => void;
  onSubmit: (input: ProductInput) => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<ProductInput>(initial);
  const [addingUnit, setAddingUnit] = useState(!initial.unit || !existingUnits.includes(initial.unit));

  function set<K extends keyof ProductInput>(key: K, value: ProductInput[K]) {
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
        <h2>{initial.name ? "Edit Product" : "New Product"}</h2>

        <label>
          Type *
          <select
            value={form.product_type}
            onChange={(e) => set("product_type", e.target.value as ProductType)}
          >
            {categories.map(({ type, label }) => (
              <option key={type} value={type}>{label}</option>
            ))}
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

        <div className="form-row">
          <label>
            Unit *
            {addingUnit ? (
              <div className="inline-field-with-action">
                <input
                  required autoFocus value={form.unit}
                  placeholder="m2, pcs, day, man, km..."
                  onChange={(e) => set("unit", e.target.value)}
                />
                {existingUnits.length > 0 && (
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => {
                      setAddingUnit(false);
                      set("unit", existingUnits[0]);
                    }}
                  >
                    Choose existing
                  </button>
                )}
              </div>
            ) : (
              <select
                value={form.unit}
                onChange={(e) => {
                  if (e.target.value === ADD_NEW_UNIT) {
                    set("unit", "");
                    setAddingUnit(true);
                  } else {
                    set("unit", e.target.value);
                  }
                }}
              >
                {existingUnits.map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
                <option value={ADD_NEW_UNIT}>+ Add new unit...</option>
              </select>
            )}
          </label>
          <label>
            Unit Price (€) *
            <input
              required type="number" step="0.01"
              value={form.unit_price}
              onChange={(e) => set("unit_price", e.target.value)}
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
