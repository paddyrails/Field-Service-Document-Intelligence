import React from "react";
import { NavLink } from "react-router-dom";
import "./Sidebar.css";

const menuItems = [
  { label: "Onboarding", path: "/onboarding" },
  { label: "Members", path: "/members" },
  { label: "Support Tickets", path: "/support-tickets" },
  { label: "Billing & Subscription", path: "/billing" },
  { label: "Collections", path: "/collections" },
];

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>RiteCare</h2>
        <span className="sidebar-subtitle">Admin Portal</span>
      </div>
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
