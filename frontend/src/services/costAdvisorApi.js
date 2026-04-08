import { authorizedRequest } from "./apiClient.js";

export async function estimateCost(getToken, payload) {
  const response = await authorizedRequest(getToken, {
    url: "/estimate",
    method: "post",
    data: payload,
  });
  return response.data.data;
}

export async function fetchRecommendations(getToken, payload) {
  const response = await authorizedRequest(getToken, {
    url: "/recommendations",
    method: "post",
    data: payload,
  });
  return response.data.data;
}

export async function compareConfigurations(getToken, payload) {
  const response = await authorizedRequest(getToken, {
    url: "/compare",
    method: "post",
    data: payload,
  });
  return response.data.data;
}
