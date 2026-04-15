import React, { useState } from "react";
import { createAppointment, AppointmentRequest } from "../services/api";
import "./BookAppointment.css";

const SERVICE_TYPES = [
  { value: "personal-care-companionship", label: "Personal Care & Companionship" },
  { value: "skilled-nursing", label: "Skilled Nursing" },
  { value: "physical-therapy", label: "Physical Therapy" },
  { value: "occupational-therapy", label: "Occupational Therapy" },
  { value: "respite-care", label: "Respite Care" },
];

const BookAppointment: React.FC = () => {
  const [form, setForm] = useState<AppointmentRequest>({
    patient_id: "",
    patient_name: "",
    service_type: "",
    scheduled_at: "",
    address: "",
    notes: "",
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(null);
    setError(null);

    try {
      const payload: AppointmentRequest = {
        ...form,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
      };
      const response = await createAppointment(payload);
      setSuccess(
        `Appointment booked successfully! ID: ${response.appointment_id}`
      );
      setForm({
        patient_id: "",
        patient_name: "",
        service_type: "",
        scheduled_at: "",
        address: "",
        notes: "",
      });
    } catch (err: any) {
      setError(
        err.response?.data?.detail?.[0]?.msg ||
          err.response?.data?.detail ||
          "Failed to book appointment. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="book-appointment">
      <h1>Book Appointment</h1>
      <p className="page-subtitle">Schedule a new care visit for a patient</p>

      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="appointment-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="patient_id">Patient ID</label>
            <input
              id="patient_id"
              name="patient_id"
              type="text"
              placeholder="e.g. P001"
              value={form.patient_id}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="patient_name">Patient Name</label>
            <input
              id="patient_name"
              name="patient_name"
              type="text"
              placeholder="e.g. John Doe"
              value={form.patient_name}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="service_type">Service Type</label>
            <select
              id="service_type"
              name="service_type"
              value={form.service_type}
              onChange={handleChange}
              required
            >
              <option value="">Select a service</option>
              {SERVICE_TYPES.map((st) => (
                <option key={st.value} value={st.value}>
                  {st.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="scheduled_at">Scheduled Date & Time</label>
            <input
              id="scheduled_at"
              name="scheduled_at"
              type="datetime-local"
              value={form.scheduled_at}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="address">Address</label>
          <input
            id="address"
            name="address"
            type="text"
            placeholder="e.g. 123 Main St, Springfield"
            value={form.address}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            name="notes"
            placeholder="e.g. Patient has back pain, needs wheelchair access"
            value={form.notes}
            onChange={handleChange}
            rows={3}
          />
        </div>

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? "Booking..." : "Book Appointment"}
        </button>
      </form>
    </div>
  );
};

export default BookAppointment;
