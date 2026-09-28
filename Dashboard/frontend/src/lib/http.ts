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

/**
 * Erro com mensagem escrita pelo próprio app (em português, segura para o usuário), para
 * falhas que não vêm da API: o ErrorState mostra a mensagem dele, como faz com a ApiError.
 * Erros de rede/JS genéricos continuam com o texto padrão.
 */
export class UiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UiError";
  }
}

type Param = string | number | boolean | null | undefined;

// Frases padrão que o Starlette/FastAPI devolvem para uma rota que ele mesmo não reconhece
// (proxy/servidor não-API na frente, prefixo errado, etc.): têm exatamente a mesma forma
// `{"detail": "..."}` do erro "de verdade" da nossa API, mas não vêm de um handler nosso —
// mostrar essa frase crua ("Not Found") ao usuário não ajuda em nada.
const DETALHE_GENERICO = /^(not found|method not allowed|forbidden|unauthorized|internal server error|not acceptable|bad request)$/i;

function mensagemPorStatus(status: number): string {
  if (status === 404) return "Recurso não encontrado.";
  if (status >= 500) return "O servidor não respondeu.";
  return `Erro ${status} ao acessar a API.`;
}

/**
 * Só usa o `detail` do corpo quando ele parece vir do formato da nossa API (string "de negócio"
 * ou lista de erros de validação do Pydantic, cada um com `msg`). Um `detail` genérico do próprio
 * framework HTTP (ex.: "Not Found") não conta como "da nossa API": quem decide a mensagem nesse
 * caso é `mensagemPorStatus`, pelo status.
 */
function detalheDeErro(body: unknown): string | null {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (Array.isArray(detail)) {
      const mensagens = detail
        .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : null))
        .filter((msg): msg is string => Boolean(msg));
      if (mensagens.length > 0) return mensagens.join("; ");
    } else if (typeof detail === "string" && detail.trim() && !DETALHE_GENERICO.test(detail.trim())) {
      return detail;
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
    let detail = mensagemPorStatus(response.status);
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
