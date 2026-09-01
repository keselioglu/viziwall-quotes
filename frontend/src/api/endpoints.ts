import { api } from "./client";
import type {
  Customer, CustomerInput, Product, ProductInput, Quotation, QuotationInput, QuotationListItem,
} from "../types";

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const { data } = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data.access_token as string;
}

// --- Customers ---

export const getCustomers = (search?: string) =>
  api.get<Customer[]>("/customers", { params: search ? { search } : {} }).then((r) => r.data);

export const getCustomer = (id: string) =>
  api.get<Customer>(`/customers/${id}`).then((r) => r.data);

export const createCustomer = (input: Partial<CustomerInput>) =>
  api.post<Customer>("/customers", input).then((r) => r.data);

export const updateCustomer = (id: string, input: Partial<CustomerInput>) =>
  api.put<Customer>(`/customers/${id}`, input).then((r) => r.data);

export const deleteCustomer = (id: string) => api.delete(`/customers/${id}`);

// --- Products ---

export const getProducts = (includeInactive = false) =>
  api.get<Product[]>("/products", { params: { include_inactive: includeInactive } }).then((r) => r.data);

export const createProduct = (input: ProductInput) =>
  api.post<Product>("/products", input).then((r) => r.data);

export const updateProduct = (id: string, input: Partial<ProductInput>) =>
  api.put<Product>(`/products/${id}`, input).then((r) => r.data);

export const deleteProduct = (id: string) => api.delete(`/products/${id}`);

// --- Quotations ---

export const getQuotations = () =>
  api.get<QuotationListItem[]>("/quotations").then((r) => r.data);

export const getQuotation = (id: string) =>
  api.get<Quotation>(`/quotations/${id}`).then((r) => r.data);

export const createQuotation = (input: QuotationInput) =>
  api.post<Quotation>("/quotations", input).then((r) => r.data);

export const updateQuotation = (id: string, input: Partial<QuotationInput>) =>
  api.put<Quotation>(`/quotations/${id}`, input).then((r) => r.data);

export const deleteQuotation = (id: string) => api.delete(`/quotations/${id}`);

export const getQuotationPdfUrl = (id: string) =>
  `${import.meta.env.VITE_API_URL}/quotations/${id}/pdf`;
