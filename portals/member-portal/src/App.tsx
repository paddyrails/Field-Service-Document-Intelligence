import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import BookAppointment from "./pages/BookAppointment";
import Services from "./pages/Services";
import Locations from "./pages/Locations";
import Testimonials from "./pages/Testimonials";
import Career from "./pages/Career";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/book" replace />} />
          <Route path="/book" element={<BookAppointment />} />
          <Route path="/services" element={<Services />} />
          <Route path="/locations" element={<Locations />} />
          <Route path="/testimonials" element={<Testimonials />} />
          <Route path="/career" element={<Career />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
