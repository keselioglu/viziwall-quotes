import { NavLink, Outlet } from "react-router-dom";
import type { MouseEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { confirmNavigation } from "../navGuard";

export default function Layout() {
  const { logout } = useAuth();

  function guardedNav(e: MouseEvent) {
    if (!confirmNavigation()) e.preventDefault();
  }

  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="brand">Viziwall Quotes</div>
        <NavLink to="/" end onClick={guardedNav}>Quotations</NavLink>
        <NavLink to="/schedule" onClick={guardedNav}>Schedule</NavLink>
        <NavLink to="/events" onClick={guardedNav}>Events</NavLink>
        <NavLink to="/archive" onClick={guardedNav}>Archive</NavLink>
        <NavLink to="/customers" onClick={guardedNav}>Customers</NavLink>
        <NavLink to="/products" onClick={guardedNav}>Products</NavLink>
        <button className="logout-btn" onClick={logout}>Log out</button>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
