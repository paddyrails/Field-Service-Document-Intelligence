import React from "react";
import { NavLink } from "react-router-dom";
import "./Sidebar.css";

const menuItems = [
  { label: "Book Appointment", path: "/book" },
  { label: "Services", path: "/services" },
  { label: "Locations", path: "/locations" },
  { label: "Testimonials", path: "/testimonials" },
  { label: "Career", path: "/career" },
];

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>RiteCare</h2>
        <span className="sidebar-subtitle">Member Portal</span>
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
