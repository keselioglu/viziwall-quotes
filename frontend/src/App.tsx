import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import CustomersPage from "./pages/CustomersPage";
import EventsPage from "./pages/EventsPage";
import ProductsPage from "./pages/ProductsPage";
import QuotationsPage from "./pages/QuotationsPage";
import QuotationEditorPage from "./pages/QuotationEditorPage";
import SchedulePage from "./pages/SchedulePage";
import "./app.css";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route path="/" element={<QuotationsPage />} />
              <Route path="/quotations/new" element={<QuotationEditorPage />} />
              <Route path="/quotations/:id" element={<QuotationEditorPage />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/customers" element={<CustomersPage />} />
              <Route path="/products" element={<ProductsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
