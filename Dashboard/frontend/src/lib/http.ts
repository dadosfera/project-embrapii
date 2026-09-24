import { apiUrl } from "./base";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Param = string | number | boolean | null | undefined;

function detalheDeErro(body: unknown): string | null {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (Array.isArray(detail)) {
      const mensagens = detail
        .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : null))
        .filter((msg): msg is string => Boolean(msg));
      if (mensagens.length > 0) return mensagens.join("; ");
    } else if (detail) {
      return String(detail);
    }
  }
  return null;
}

export async function request<T>(path: string, params: Record<string, Param> = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const query = qs.toString();

  let response: Response;
  try {
    response = await fetch(apiUrl(path) + (query ? `?${query}` : ""));
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiError(0, "Falha de rede ao acessar a API");
    }
    throw error;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const ehJson = contentType.includes("application/json");

  if (!response.ok) {
    let detail = `Erro ${response.status}`;
    if (ehJson) {
      try {
        const body = await response.json();
        detail = detalheDeErro(body) ?? detail;
      } catch {
        /* corpo não-JSON */
      }
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  if (!ehJson) {
    throw new ApiError(response.status, "Resposta inesperada do servidor");
  }

  return (await response.json()) as T;
}
