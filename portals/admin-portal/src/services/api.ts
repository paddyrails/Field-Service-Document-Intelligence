import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost",
});

export interface IngestResponse {
  dag_run_id: string;
  file_path: string;
  status: string;
}

export interface DagRunStatus {
  dag_run_id: string;
  state: string;
}

export const uploadDocument = async (
  file: File,
  bu: string,
  customerId: string,
  serviceType: string
): Promise<IngestResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("bu", bu);
  formData.append("customer_id", customerId);
  formData.append("service_type", serviceType);

  const response = await api.post<IngestResponse>("/ingest", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const getDagRunStatus = async (
  dagRunId: string
): Promise<DagRunStatus> => {
  const response = await api.get<DagRunStatus>(
    `/ingest/${encodeURIComponent(dagRunId)}/status`
  );
  return response.data;
};
