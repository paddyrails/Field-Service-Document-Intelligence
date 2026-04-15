import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost/appointments",
});

export interface AppointmentRequest {
  patient_id: string;
  patient_name: string;
  service_type: string;
  scheduled_at: string;
  address?: string;
  notes?: string;
}

export interface AppointmentResponse {
  appointment_id: string;
  patient_id: string;
  patient_name: string;
  service_type: string;
  scheduled_at: string;
  address: string | null;
  notes: string | null;
  status: string;
}

export const createAppointment = async (
  data: AppointmentRequest
): Promise<AppointmentResponse> => {
  const response = await api.post<AppointmentResponse>("", data);
  return response.data;
};
