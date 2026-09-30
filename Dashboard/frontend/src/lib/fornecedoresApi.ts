import { request } from "./http";

export interface MapaFornecedorUf {
  uf: string;
  quantidade_nacional: number;
  quantidade_estrangeiro: number;
  quantidade_grupo_estrangeiro: number;
  quantidade_desconhecida: number;
  valor_nacional: number;
  valor_estrangeiro: number;
  valor_grupo_estrangeiro: number;
  valor_desconhecido: number;
  predominancia: "NACIONAL" | "ESTRANGEIRO" | "EMPATE";
}

export interface RankingFornecedor {
  fornecedor: string;
  cnpj: string | null;
  nacional_estrangeiro: "NACIONAL" | "ESTRANGEIRO" | "GRUPO_ESTRANGEIRO" | "DESCONHECIDO";
  grupo_estrangeiro_socio: string | null;
  valor_total: number;
  quantidade_itens: number;
  numero_compras: number;
}

export function buscarMapaFornecedoresPorUf(
  dataInicio: string,
  dataFim: string,
): Promise<MapaFornecedorUf[]> {
  return request<MapaFornecedorUf[]>("/api/fornecedores/mapa-por-uf", {
    data_inicio: dataInicio,
    data_fim: dataFim,
  });
}

export function buscarRankingFornecedores(
  dataInicio: string,
  dataFim: string,
  uf?: string,
  limite?: number,
): Promise<RankingFornecedor[]> {
  return request<RankingFornecedor[]>("/api/fornecedores/ranking", {
    data_inicio: dataInicio,
    data_fim: dataFim,
    uf,
    limite,
  });
}
