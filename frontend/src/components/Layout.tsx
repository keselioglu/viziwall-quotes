import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { logout } = useAuth();

  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="brand">Viziwall Quotes</div>
        <NavLink to="/" end>Quotations</NavLink>
        <NavLink to="/customers">Customers</NavLink>
        <NavLink to="/products">Products</NavLink>
        <button className="logout-btn" onClick={logout}>Log out</button>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
