import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Layout from "./components/Layout";
import Members from "./pages/Members";
import SupportTickets from "./pages/SupportTickets";
import Billing from "./pages/Billing";
import Collections from "./pages/Collections";
import Onboarding from "./pages/Onboarding";

function App() {
  return (
    <BrowserRouter>
      <ToastContainer
        position="top-right"
        autoClose={4000}
        hideProgressBar={false}
        closeOnClick
        pauseOnHover
      />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/onboarding" replace />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/members" element={<Members />} />
          <Route path="/support-tickets" element={<SupportTickets />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/collections" element={<Collections />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
