import { apiUrl } from "./base";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

type Param = string | number | boolean | null | undefined;

export async function request<T>(path: string, params: Record<string, Param> = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const query = qs.toString();
  const response = await fetch(apiUrl(path) + (query ? `?${query}` : ""));
  if (!response.ok) {
    let detail = `Erro ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* corpo não-JSON */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}
