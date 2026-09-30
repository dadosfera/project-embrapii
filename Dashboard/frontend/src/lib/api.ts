import { request } from "./http";

// ---------------------------------------------------------------------------
// Medicamentos
// ---------------------------------------------------------------------------

export interface CatmatItem {
  catmat_id: number;
  codigo_catmat: string;
  descricao_catmat: string;
}

export interface Produto {
  produto_id: number;
  catmat_id: number;
  anvisa: string | null;
  generico: string | null;
  codigo_catmat: string;
}

export interface ResumoMedicamento {
  estoque_total: number;
  instituicoes_com_registro: number;
  instituicoes_estoque_zerado: number;
  preco_medio_compra: number | null;
}

export interface LoteVencendo {
  instituicao_id: number;
  produto_id: number;
  numero_do_lote: string | null;
  quantidade_do_item_em_estoque: number;
  data_de_posicao_no_estoque: string | null;
  data_de_validade: string | null;
}

export interface LotesVencendo {
  dias: number;
  quantidade_lotes: number;
  items: LoteVencendo[];
}

export interface EstoqueUf {
  uf: string | null;
  estoque_total: number;
  num_instituicoes: number;
}

export interface EvolucaoPreco {
  data_de_compra: string;
  preco_medio: number;
}

export interface FornecedorCompra {
  nome_fornecedor: string;
  valor_total: number;
}

export interface FabricanteCompra {
  nome_fabricante: string;
  valor_total: number;
}

export interface CompraMedicamento {
  data_de_compra: string | null;
  modalidade_de_compra: string | null;
  tipo_da_compra: string | null;
  quantidade_de_itens: number | null;
  preco_unitario: number | null;
  preco_total: number | null;
  nome_fornecedor: string | null;
  nome_fabricante: string | null;
  nome_mantenedora: string | null;
}

export interface HistoricoCompras {
  limite: number;
  offset: number;
  items: CompraMedicamento[];
}

export function buscarMedicamentos(q: string, limite?: number): Promise<CatmatItem[]> {
  return request<CatmatItem[]>("/api/medicamentos/busca", { q, limite });
}

export function listarProdutos(catmatId: number): Promise<Produto[]> {
  return request<Produto[]>(`/api/medicamentos/${catmatId}/produtos`);
}

export function buscarResumoMedicamento(catmatId: number): Promise<ResumoMedicamento> {
  return request<ResumoMedicamento>(`/api/medicamentos/${catmatId}/resumo`);
}

export function buscarLotesVencendo(catmatId: number, dias: number): Promise<LotesVencendo> {
  return request<LotesVencendo>(`/api/medicamentos/${catmatId}/lotes-vencendo`, { dias });
}

export function buscarEstoquePorUf(catmatId: number): Promise<EstoqueUf[]> {
  return request<EstoqueUf[]>(`/api/medicamentos/${catmatId}/estoque-por-uf`);
}

export function buscarEvolucaoPreco(catmatId: number): Promise<EvolucaoPreco[]> {
  return request<EvolucaoPreco[]>(`/api/medicamentos/${catmatId}/compras/evolucao-preco`);
}

export function buscarFornecedores(catmatId: number, limite: number): Promise<FornecedorCompra[]> {
  return request<FornecedorCompra[]>(`/api/medicamentos/${catmatId}/compras/fornecedores`, { limite });
}

export function buscarFabricantes(catmatId: number, limite: number): Promise<FabricanteCompra[]> {
  return request<FabricanteCompra[]>(`/api/medicamentos/${catmatId}/compras/fabricantes`, { limite });
}

export function buscarHistoricoCompras(
  catmatId: number,
  limite: number,
  offset: number,
): Promise<HistoricoCompras> {
  return request<HistoricoCompras>(`/api/medicamentos/${catmatId}/compras`, { limite, offset });
}

// ---------------------------------------------------------------------------
// Compras
// ---------------------------------------------------------------------------

export interface FiltrosCompras {
  data_inicio: string;
  data_fim: string;
  catmat_id?: number | null;
  tipo_compra?: string;
}

export interface KpisCompras {
  valor_total: number;
  numero_compras: number;
  quantidade_itens: number;
  numero_fornecedores: number;
  numero_fabricantes: number;
  numero_mantenedoras: number;
}

export interface CompraPorMes {
  mes: string;
  valor_total: number;
  numero_compras: number;
  quantidade_itens: number;
}

export interface RankingFornecedorCompra {
  fornecedor: string;
  valor_total: number;
  numero_compras: number;
  quantidade_itens: number;
}

export interface RankingFabricanteCompra {
  fabricante: string;
  valor_total: number;
  numero_compras: number;
  quantidade_itens: number;
}

export interface CompraPorModalidade {
  modalidade: string;
  valor_total: number;
  numero_compras: number;
  quantidade_itens: number;
}

export interface CompraPorTipo {
  tipo_compra: string;
  valor_total: number;
  numero_compras: number;
  quantidade_itens: number;
}

export interface CompraRecente {
  data_de_compra: string | null;
  codigo_catmat: string | null;
  descricao_catmat: string | null;
  modalidade_de_compra: string | null;
  tipo_da_compra: string | null;
  quantidade_de_itens: number | null;
  preco_unitario: number | null;
  preco_total: number | null;
  nome_fornecedor: string | null;
  nome_fabricante: string | null;
  nome_mantenedora: string | null;
}

function paramsCompras(f: FiltrosCompras) {
  return {
    data_inicio: f.data_inicio,
    data_fim: f.data_fim,
    catmat_id: f.catmat_id,
    tipo_compra: f.tipo_compra,
  };
}

export function buscarKpisCompras(filtros: FiltrosCompras): Promise<KpisCompras> {
  return request<KpisCompras>("/api/compras/kpis", paramsCompras(filtros));
}

export function buscarComprasPorMes(filtros: FiltrosCompras): Promise<CompraPorMes[]> {
  return request<CompraPorMes[]>("/api/compras/por-mes", paramsCompras(filtros));
}

export function buscarRankingFornecedores(
  filtros: FiltrosCompras,
  limite: number,
): Promise<RankingFornecedorCompra[]> {
  return request<RankingFornecedorCompra[]>("/api/compras/fornecedores", {
    ...paramsCompras(filtros),
    limite,
  });
}

export function buscarRankingFabricantes(
  filtros: FiltrosCompras,
  limite: number,
): Promise<RankingFabricanteCompra[]> {
  return request<RankingFabricanteCompra[]>("/api/compras/fabricantes", {
    ...paramsCompras(filtros),
    limite,
  });
}

export function buscarComprasPorModalidade(filtros: FiltrosCompras): Promise<CompraPorModalidade[]> {
  return request<CompraPorModalidade[]>("/api/compras/modalidades", paramsCompras(filtros));
}

export function buscarComprasPorTipo(filtros: FiltrosCompras): Promise<CompraPorTipo[]> {
  return request<CompraPorTipo[]>("/api/compras/tipos", paramsCompras(filtros));
}

export function buscarComprasRecentes(
  filtros: FiltrosCompras,
  limite: number,
): Promise<CompraRecente[]> {
  return request<CompraRecente[]>("/api/compras/recentes", {
    ...paramsCompras(filtros),
    limite,
  });
}

// ---------------------------------------------------------------------------
// Leitos
// ---------------------------------------------------------------------------

export type ModoLeitos = "ultima_competencia" | "ultima_instituicao";

export interface IntervaloLeitos {
  data_minima: string | null;
  data_maxima: string | null;
}

export interface OpcoesLeitos {
  data_minima: string | null;
  data_maxima: string | null;
  ufs: string[];
}

export interface FiltrosLeitos {
  modo: ModoLeitos;
  uf: string;
}

export interface KpisLeitos {
  leitos_gerais: number;
  leitos_sus: number;
  leitos_uti: number;
  leitos_uti_sus: number;
  instituicoes_com_registro: number;
  competencia_minima: string | null;
  competencia_maxima: string | null;
}

export interface LeitosPorUf {
  uf: string;
  leitos_gerais: number;
  leitos_sus: number;
  leitos_uti: number;
  leitos_uti_sus: number;
  instituicoes: number;
}

export interface TipoUti {
  tipo_uti: string;
  total: number;
  sus: number;
}

export interface EvolucaoLeitos {
  competencia: string;
  leitos_gerais: number;
  leitos_sus: number;
  leitos_uti: number;
  leitos_uti_sus: number;
  instituicoes: number;
}

export interface InstituicaoLeitos {
  instituicao_id: number;
  instituicao: string;
  municipio: string | null;
  uf: string | null;
  competencia: string;
  leitos_gerais: number;
  leitos_sus: number;
  leitos_uti: number;
  leitos_uti_sus: number;
}

export interface PainelLeitos {
  kpis: KpisLeitos;
  por_uf: LeitosPorUf[];
  tipos_uti: TipoUti[];
  evolucao: EvolucaoLeitos[];
  instituicoes: InstituicaoLeitos[];
}

export function buscarOpcoesLeitos(): Promise<OpcoesLeitos> {
  return request<OpcoesLeitos>("/api/leitos/opcoes");
}

export function buscarPainelLeitos(
  filtros: FiltrosLeitos,
  dataInicio: string,
  dataFim: string,
): Promise<PainelLeitos> {
  return request<PainelLeitos>("/api/leitos/painel", {
    data_inicio: dataInicio,
    data_fim: dataFim,
    modo: filtros.modo,
    uf: filtros.uf,
  });
}

export function buscarLeitosPorUf(filtros: FiltrosLeitos): Promise<LeitosPorUf[]> {
  return request<LeitosPorUf[]>("/api/leitos/por-uf", {
    modo: filtros.modo,
    uf: filtros.uf,
  });
}
