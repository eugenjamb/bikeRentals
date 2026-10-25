import type { Forecast, ForecastRequest, Scenario, Study } from "./types";

export const apiBase = `${import.meta.env.BASE_URL}api`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item: { msg: string }) => item.msg).join("; ")
      : typeof detail === "string"
        ? detail
        : "The service is unavailable. Please try again.";
    throw new Error(message);
  }
  return response.json();
}

export const getStudy = () => request<Study>("/study");
export const getScenarios = () => request<Scenario[]>("/scenarios");
export const getScenario = (id: string) =>
  request<Scenario>(`/scenarios/${id}`);
export const predict = (payload: ForecastRequest) =>
  request<Forecast>("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
