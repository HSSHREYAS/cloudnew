import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function authorizedRequest(getToken, config) {
  const token = await getToken();
  if (!token) {
    throw new Error("Authentication token is unavailable.");
  }
  return apiClient.request({
    ...config,
    headers: {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}

export default apiClient;
