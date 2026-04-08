import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

const navItems = [
  { to: "/", label: "Estimator" },
  { to: "/compare", label: "Compare" },
];

export default function AppShell() {
  const { user, signOutUser } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-card">
          <span className="eyebrow">Cloud Economics</span>
          <h1>Smart Cost Advisor</h1>
          <p>Real-time AWS price estimation with explainable optimization insights.</p>
        </div>

        <nav className="nav-links">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="account-card">
          <span className="label">Signed in as</span>
          <strong>{user?.email || "cloud-user"}</strong>
          <button type="button" className="ghost-button" onClick={signOutUser}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="page-content">
        <Outlet />
      </main>
    </div>
  );
}
