import {
  type FormEvent,
  useMemo,
  useState,
} from "react";

import type { ColumnDef } from "@tanstack/react-table";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DataTable } from "../components/DataTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartFrame } from "@/ui/ChartFrame";
import { EmptyState } from "@/ui/EmptyState";
import { ErrorState } from "@/ui/ErrorState";
import { Icon } from "@/ui/Icon";
import { KpiCard } from "@/ui/KpiCard";
import { PageHeader } from "@/ui/PageHeader";
import { categorica, dotPara, eixo, grade, linha, tooltip } from "@/ui/chartTheme";
import { useEhTelaEstreita } from "@/ui/useEhTelaEstreita";
import {
  data as dataBR,
  moedaCompacta,
  moedaExata,
  numeroCompacto,
  numeroExato,
  quantidade,
} from "@/ui/format";

import {
  buscarEvolucaoPreco,
  buscarEstoquePorUf,
  buscarFabricantes,
  buscarFornecedores,
  buscarHistoricoCompras,
  buscarLotesVencendo,
  buscarMedicamentos,
  buscarResumoMedicamento,
  listarProdutos,
  type CatmatItem,
  type CompraMedicamento,
  type EstoqueUf,
  type EvolucaoPreco,
  type FabricanteCompra,
  type FornecedorCompra,
  type LoteVencendo,
  type Produto,
  type ResumoMedicamento,
} from "../lib/api";

import { useUiContext } from "../lib/uiContext";


type AbaCompras =
  | "preco"
  | "fornecedores"
  | "dados";


type DadosMedicamento = {
  produtos: Produto[];
  resumo: ResumoMedicamento;
  lotes: {
    dias: number;
    quantidade_lotes: number;
    items: LoteVencendo[];
  };
  estoqueUf: EstoqueUf[];
  evolucaoPreco: EvolucaoPreco[];
  fornecedores: FornecedorCompra[];
  fabricantes: FabricanteCompra[];
  compras: CompraMedicamento[];
};


function rotuloMedicamento(
  item: CatmatItem,
) {
  const descricao =
    item.descricao_catmat
    ?? "Sem descrição";

  const codigo =
    item.codigo_catmat
    ?? "sem código";

  return `${descricao} — CATMAT ${codigo}`;
}


/** Coerção numérica (a API pode mandar decimal como string). Usada nos gráficos e no contexto do chat. */
function numero(valor: unknown) {
  const convertido =
    Number(valor);

  return Number.isFinite(
    convertido,
  )
    ? convertido
    : 0;
}


/** Para KPI: nulo continua nulo (vira "sem dado"), nunca 0. */
function numeroOuNulo(valor: unknown): number | null {
  if (valor === null || valor === undefined || valor === "") return null;
  const convertido = Number(valor);
  return Number.isFinite(convertido) ? convertido : null;
}


function truncar(
  valor: unknown,
  tamanho = 24,
) {
  const texto =
    String(
      valor ?? "Não informado",
    );

  if (
    texto.length
    <= tamanho
  ) {
    return texto;
  }

  return `${texto.slice(
    0,
    tamanho - 1,
  )}…`;
}


function GraficoBarrasHorizontal({
  data,
  nomeKey,
  valorKey,
  cor,
  vazio,
}: {
  data: Record<
    string,
    string | number
  >[];
  nomeKey: string;
  valorKey: string;
  cor: string;
  vazio: string;
}) {
  if (data.length === 0) {
    return (
      <EmptyState title="Sem compras para comparar" cause={vazio} />
    );
  }

  const altura =
    Math.max(
      280,
      data.length * 40,
    );

  // Mesma correção do B5 em Compras.tsx: nomes de fabricante/fornecedor em CAIXA ALTA são
  // largos demais para os ~20 caracteres calibrados para desktop dentro do eixo Y de 115px
  // numa tela estreita — o rótulo cortava pela esquerda.
  const estreita = useEhTelaEstreita();

  return (
    <div
      className="w-full"
      style={{ height: altura }}
    >
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <BarChart
          data={data}
          layout="vertical"
          margin={{
            top: 4,
            right: 12,
            bottom: 4,
            left: 4,
          }}
        >
          <CartesianGrid
            {...grade}
            horizontal={false}
            vertical
          />

          <XAxis
            {...eixo}
            type="number"
            tickFormatter={(value) => moedaCompacta(value)}
          />

          <YAxis
            {...eixo}
            type="category"
            dataKey={nomeKey}
            width={estreita ? 100 : 115}
            tickFormatter={(value) => truncar(value, estreita ? 12 : 20)}
          />

          <Tooltip
            {...tooltip}
            formatter={(value) => moedaExata(numero(value))}
            labelFormatter={(value) => String(value)}
          />

          <Bar
            dataKey={valorKey}
            name="Gasto total"
            fill={cor}
            radius={[
              0,
              4,
              4,
              0,
            ]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}


const MAX_PONTOS_BRUTOS = 60;


/**
 * Contexto da tela para o chat: pequeno vai bruto (é o que está nos gráficos), grande vai resumido —
 * a evolução de preço vira média anual acima de 60 pontos e o histórico de compras (até 500 linhas) vira
 * totais por ano × tipo + as 15 compras mais recentes.
 */
function contextoMedicamento(
  dados: DadosMedicamento,
  item: CatmatItem,
  abaCompras: AbaCompras,
  busca: string | null,
) {
  const evolucao = dados.evolucaoPreco.map((e) => ({
    data: String(e.data_de_compra).slice(0, 10),
    preco_medio: numero(e.preco_medio),
  }));

  const porAno = new Map<string, { soma: number; n: number }>();
  for (const e of evolucao) {
    const ano = e.data.slice(0, 4);
    const acc = porAno.get(ano) ?? { soma: 0, n: 0 };
    acc.soma += e.preco_medio;
    acc.n += 1;
    porAno.set(ano, acc);
  }

  const comprasResumo = new Map<string, { ano: string; tipo: string; compras: number; valor_total: number; itens: number }>();
  for (const c of dados.compras) {
    const ano = (c.data_de_compra ?? "").slice(0, 4) || "N/I";
    const tipo = c.tipo_da_compra ?? "NÃO INFORMADO";
    const chave = `${ano}|${tipo}`;
    const acc = comprasResumo.get(chave) ?? { ano, tipo, compras: 0, valor_total: 0, itens: 0 };
    acc.compras += 1;
    acc.valor_total += numero(c.preco_total);
    acc.itens += numero(c.quantidade_de_itens);
    comprasResumo.set(chave, acc);
  }

  return {
    screen: "Medicamentos",
    description:
      "Detalhe de um medicamento CATMAT: KPIs de estoque (última posição por instituição), lotes vencendo em 90 dias, "
      + "estoque por UF e compras públicas (preço, fornecedores, fabricantes, histórico).",
    filters: { busca, aba_compras: abaCompras, janela_lotes_dias: dados.lotes.dias },
    selection: {
      catmat_id: item.catmat_id,
      codigo_catmat: item.codigo_catmat,
      descricao: item.descricao_catmat,
      produtos_vinculados: dados.produtos.length,
    },
    visible_kpis: {
      estoque_total: numero(dados.resumo.estoque_total),
      instituicoes_com_registro: numero(dados.resumo.instituicoes_com_registro),
      instituicoes_estoque_zerado: numero(dados.resumo.instituicoes_estoque_zerado),
      preco_medio_compra: dados.resumo.preco_medio_compra === null ? null : numero(dados.resumo.preco_medio_compra),
      lotes_vencendo_90d: dados.lotes.quantidade_lotes,
    },
    visible_data: {
      estoque_por_uf: dados.estoqueUf.map((e) => ({
        uf: e.uf ?? "N/I",
        estoque_total: numero(e.estoque_total),
        num_instituicoes: numero(e.num_instituicoes),
      })),
      ...(evolucao.length <= MAX_PONTOS_BRUTOS
        ? { evolucao_preco: evolucao }
        : {
            evolucao_preco_por_ano: [...porAno.entries()].map(([ano, a]) => ({ ano, preco_medio: a.soma / a.n })),
            evolucao_preco_pontos: evolucao.length,
          }),
      fornecedores_top: dados.fornecedores.map((f) => ({ nome: f.nome_fornecedor, valor_total: numero(f.valor_total) })),
      fabricantes_top: dados.fabricantes.map((f) => ({ nome: f.nome_fabricante, valor_total: numero(f.valor_total) })),
      lotes_vencendo: dados.lotes.items.slice(0, 20).map((l) => ({
        instituicao_id: l.instituicao_id,
        lote: l.numero_do_lote,
        quantidade: numero(l.quantidade_do_item_em_estoque),
        validade: l.data_de_validade?.slice(0, 10) ?? null,
      })),
      compras_por_ano: [...comprasResumo.values()].sort((a, b) => a.ano.localeCompare(b.ano)),
      compras_recentes: dados.compras.slice(0, 15).map((c) => ({
        data: c.data_de_compra?.slice(0, 10) ?? null,
        tipo: c.tipo_da_compra,
        modalidade: c.modalidade_de_compra,
        quantidade: c.quantidade_de_itens,
        preco_unitario: c.preco_unitario,
        preco_total: c.preco_total,
        fornecedor: c.nome_fornecedor,
        mantenedora: c.nome_mantenedora,
      })),
      historico_compras_linhas: dados.compras.length,
    },
  };
}


export function Medicamentos() {
  const [
    busca,
    setBusca,
  ] = useState("");

  const [
    resultados,
    setResultados,
  ] =
    useState<
      CatmatItem[]
    >([]);

  const [
    selecionado,
    setSelecionado,
  ] = useState("");

  const [
    buscando,
    setBuscando,
  ] = useState(false);

  const [
    carregando,
    setCarregando,
  ] = useState(false);

  const [
    erroBusca,
    setErroBusca,
  ] =
    useState<
      string | null
    >(null);

  const [
    erroDados,
    setErroDados,
  ] =
    useState<
      string | null
    >(null);

  // Falha de requisição: guarda o erro real para o ErrorState (erroDados fica para mensagens da página).
  const [
    falhaDados,
    setFalhaDados,
  ] =
    useState<unknown>(null);

  const [
    buscaConfirmada,
    setBuscaConfirmada,
  ] =
    useState<
      string | null
    >(null);

  const [
    medicamentoCarregado,
    setMedicamentoCarregado,
  ] =
    useState<
      CatmatItem | null
    >(null);

  const [
    dados,
    setDados,
  ] =
    useState<
      DadosMedicamento | null
    >(null);

  const [
    abaCompras,
    setAbaCompras,
  ] =
    useState<AbaCompras>(
      "preco",
    );


  const itemSelecionado =
    resultados.find(
      (item) =>
        String(
          item.catmat_id,
        )
        === selecionado,
    );


  function alterarBusca(
    valor: string,
  ) {
    setBusca(valor);

    if (
      medicamentoCarregado
      || dados
    ) {
      setMedicamentoCarregado(
        null,
      );
      setDados(null);
      setErroDados(null);
      setFalhaDados(null);
    }
  }


  async function handleBuscar(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const termo =
      busca.trim();

    if (!termo) {
      setErroBusca(
        "Digite algo para buscar um medicamento no catálogo CATMAT.",
      );
      return;
    }

    setBuscando(true);
    setErroBusca(null);
    setErroDados(null);
    setFalhaDados(null);
    setResultados([]);
    setSelecionado("");
    setBuscaConfirmada(null);
    setMedicamentoCarregado(
      null,
    );
    setDados(null);

    try {
      const itens =
        await buscarMedicamentos(
          termo,
        );

      setResultados(
        itens,
      );

      if (
        itens.length === 0
      ) {
        setErroBusca(
          "Nenhum item encontrado para essa busca.",
        );
      }
    } catch (error) {
      setErroBusca(
        error
          instanceof Error
          ? error.message
          : "Não foi possível consultar a API.",
      );
    } finally {
      setBuscando(false);
    }
  }


  async function carregarDados() {
    if (
      !itemSelecionado
    ) {
      setErroDados(
        "Selecione um medicamento antes de carregar os dados.",
      );
      return;
    }

    const catmatId =
      itemSelecionado
        .catmat_id;

    setCarregando(true);
    setErroDados(null);
    setFalhaDados(null);
    setDados(null);
    setAbaCompras(
      "preco",
    );

    try {
      const [
        produtos,
        resumo,
        lotes,
        estoqueUf,
        evolucaoPreco,
        fornecedores,
        fabricantes,
        historico,
      ] =
        await Promise.all([
          listarProdutos(
            catmatId,
          ),
          buscarResumoMedicamento(
            catmatId,
          ),
          buscarLotesVencendo(
            catmatId,
            90,
          ),
          buscarEstoquePorUf(
            catmatId,
          ),
          buscarEvolucaoPreco(
            catmatId,
          ),
          buscarFornecedores(
            catmatId,
            15,
          ),
          buscarFabricantes(
            catmatId,
            15,
          ),
          buscarHistoricoCompras(
            catmatId,
            500,
            0,
          ),
        ]);

      if (
        produtos.length === 0
      ) {
        setMedicamentoCarregado(
          null,
        );
        setErroDados(
          "Esse item do CATMAT não tem produto vinculado na base.",
        );
        return;
      }

      setBuscaConfirmada(
        busca.trim(),
      );

      setMedicamentoCarregado(
        itemSelecionado,
      );

      setDados({
        produtos,
        resumo,
        lotes,
        estoqueUf,
        evolucaoPreco,
        fornecedores,
        fabricantes,
        compras:
          historico.items,
      });
    } catch (error) {
      setMedicamentoCarregado(
        null,
      );

      setFalhaDados(error);
    } finally {
      setCarregando(false);
    }
  }


  const estoqueUfGrafico =
    useMemo(
      () =>
        (
          dados?.estoqueUf
          ?? []
        )
          .filter(
            (item) =>
              item.uf,
          )
          .map(
            (item) => ({
              uf:
                item.uf
                ?? "N/I",
              estoque_total:
                numero(
                  item.estoque_total,
                ),
            }),
          ),
      [dados],
    );


  const evolucaoPrecoGrafico =
    useMemo(
      () =>
        (
          dados
            ?.evolucaoPreco
          ?? []
        ).map(
          (item) => ({
            data:
              dataBR(
                item.data_de_compra,
              ),
            preco:
              numero(
                item.preco_medio,
              ),
          }),
        ),
      [dados],
    );


  const fornecedoresGrafico =
    useMemo(
      () =>
        (
          dados
            ?.fornecedores
          ?? []
        ).map(
          (item) => ({
            nome:
              item
                .nome_fornecedor
              ?? "Não informado",
            valor:
              numero(
                item.valor_total,
              ),
          }),
        ),
      [dados],
    );


  const fabricantesGrafico =
    useMemo(
      () =>
        (
          dados
            ?.fabricantes
          ?? []
        ).map(
          (item) => ({
            nome:
              item
                .nome_fabricante
              ?? "Não informado",
            valor:
              numero(
                item.valor_total,
              ),
          }),
        ),
      [dados],
    );


  const colunasLotes =
    useMemo<
      ColumnDef<
        LoteVencendo,
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Instituição",
          accessorKey:
            "instituicao_id",
          cell: ({
            row,
          }) =>
            row.original
              .instituicao_id
            ?? "—",
        },
        {
          header: "Lote",
          accessorKey:
            "numero_do_lote",
          cell: ({
            row,
          }) =>
            row.original
              .numero_do_lote
            ?? "—",
          meta: { priority: "low" },
        },
        {
          header:
            "Quantidade",
          accessorKey:
            "quantidade_do_item_em_estoque",
          cell: ({
            row,
          }) =>
            quantidade(
              row.original
                .quantidade_do_item_em_estoque,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Validade",
          accessorKey:
            "data_de_validade",
          cell: ({
            row,
          }) =>
            dataBR(
              row.original
                .data_de_validade,
            ),
        },
      ],
      [],
    );


  const colunasUf =
    useMemo<
      ColumnDef<
        EstoqueUf,
        unknown
      >[]
    >(
      () => [
        {
          header: "UF",
          accessorKey: "uf",
          cell: ({
            row,
          }) =>
            row.original.uf
            ?? "Não informado",
        },
        {
          header:
            "Estoque total",
          accessorKey:
            "estoque_total",
          cell: ({
            row,
          }) =>
            quantidade(
              row.original
                .estoque_total,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Instituições",
          accessorKey:
            "num_instituicoes",
          cell: ({
            row,
          }) =>
            quantidade(
              row.original
                .num_instituicoes,
            ),
          meta: { align: "right" },
        },
      ],
      [],
    );


  const colunasCompras =
    useMemo<
      ColumnDef<
        CompraMedicamento,
        unknown
      >[]
    >(
      () => [
        {
          header: "Data",
          accessorKey:
            "data_de_compra",
          cell: ({
            row,
          }) =>
            dataBR(
              row.original
                .data_de_compra,
            ),
        },
        {
          header:
            "Modalidade",
          accessorKey:
            "modalidade_de_compra",
          cell: ({
            row,
          }) =>
            row.original
              .modalidade_de_compra
            ?? "—",
        },
        {
          header: "Tipo",
          accessorKey:
            "tipo_da_compra",
          cell: ({
            row,
          }) =>
            row.original
              .tipo_da_compra
            ?? "—",
        },
        {
          header:
            "Quantidade",
          accessorKey:
            "quantidade_de_itens",
          cell: ({
            row,
          }) =>
            quantidade(
              row.original
                .quantidade_de_itens,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Preço unitário",
          accessorKey:
            "preco_unitario",
          cell: ({
            row,
          }) =>
            moedaExata(
              row.original
                .preco_unitario,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Preço total",
          accessorKey:
            "preco_total",
          cell: ({
            row,
          }) =>
            moedaExata(
              row.original
                .preco_total,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Fornecedor",
          accessorKey:
            "nome_fornecedor",
          cell: ({
            row,
          }) =>
            row.original
              .nome_fornecedor
            ?? "—",
        },
        {
          header:
            "Fabricante",
          accessorKey:
            "nome_fabricante",
          cell: ({
            row,
          }) =>
            row.original
              .nome_fabricante
            ?? "—",
        },
        {
          header:
            "Mantenedora",
          accessorKey:
            "nome_mantenedora",
          cell: ({
            row,
          }) =>
            row.original
              .nome_mantenedora
            ?? "—",
        },
      ],
      [],
    );


  useUiContext(
    dados && medicamentoCarregado
      ? contextoMedicamento(dados, medicamentoCarregado, abaCompras, buscaConfirmada)
      : {
          screen: "Medicamentos",
          description: carregando
            ? "Carregando os dados do medicamento selecionado."
            : "Nenhum medicamento carregado: o usuário ainda está buscando no catálogo CATMAT.",
          filters: { busca: busca || null, resultados_da_busca: resultados.length },
          selection: null,
        },
    [dados, medicamentoCarregado, abaCompras, buscaConfirmada, carregando, busca, resultados.length],
  );

  // Resolve a paleta uma vez por montagem (lê as variáveis CSS do documento).
  const paleta = useMemo(() => categorica(), []);


  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <PageHeader
        icon="droplet"
        title="Medicamentos"
        description="Consulte estoque atual, lotes próximos do vencimento, distribuição geográfica e histórico de compras por medicamento CATMAT."
      />


      <section className="mt-7">
        <form
          onSubmit={handleBuscar}
          className="space-y-2"
        >
          <label
            htmlFor="busca-medicamento"
            className="block text-sm font-semibold text-[var(--text)]"
          >
            Buscar medicamento (CATMAT)
          </label>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Input
              id="busca-medicamento"
              value={busca}
              onChange={(event) => alterarBusca(event.target.value)}
              placeholder="ex: dipirona, insulina, seringa..."
              className="h-10 bg-panel sm:flex-1"
            />

            <Button
              type="submit"
              disabled={buscando}
              className="h-10 w-full px-6 sm:w-auto"
            >
              <Icon name="search" size={16} />
              {buscando
                ? "Buscando..."
                : "Buscar"}
            </Button>
          </div>
        </form>


        {!busca.trim()
          && !erroBusca
          && (
            <p className="mt-3 flex items-center gap-2 text-sm leading-6 text-muted">
              <Icon name="info" size={16} />
              Digite algo acima para buscar um medicamento no catálogo CATMAT.
            </p>
          )}


        {erroBusca && (
          <div
            role="status"
            className="mt-4 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text"
          >
            <Icon name="alert" size={18} className="mt-0.5" />
            {erroBusca}
          </div>
        )}


        {resultados.length
          > 0
          && (
            <div className="mt-5 rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
              <label
                htmlFor="catmat"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Selecione o item
              </label>

              {/* Continua <select> nativo: o smoke e o e2e do chat usam selectOption() em #catmat. */}
              <select
                id="catmat"
                value={selecionado}
                onChange={(event) => setSelecionado(event.target.value)}
                className="mt-2 h-10 w-full rounded-[var(--radius-md)] border border-line bg-panel px-3 text-sm text-[var(--text)] shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
              >
                <option value="">
                  — Selecione um medicamento —
                </option>

                {resultados.map((item) => (
                  <option
                    key={item.catmat_id}
                    value={item.catmat_id}
                  >
                    {rotuloMedicamento(item)}
                  </option>
                ))}
              </select>

              <Button
                type="button"
                onClick={carregarDados}
                disabled={!itemSelecionado || carregando}
                className="mx-auto mt-4 flex h-10 w-full sm:w-1/2 lg:w-1/4"
              >
                {carregando
                  ? "Carregando dados..."
                  : "Pesquisar"}
              </Button>
            </div>
          )}
      </section>


      {erroDados && (
        <div
          role="status"
          className="mt-5 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text"
        >
          <Icon name="alert" size={18} className="mt-0.5" />
          {erroDados}
        </div>
      )}


      {falhaDados != null && (
        <div className="mt-5">
          <ErrorState
            error={falhaDados}
            onRetry={itemSelecionado ? carregarDados : undefined}
          />
        </div>
      )}


      {carregando && (
        <section className="mt-7 space-y-4" aria-busy="true">
          <Skeleton className="h-8 w-72 max-w-full" />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map((item) => (
              <Skeleton key={item} className="h-28" />
            ))}
          </div>

          <Skeleton className="h-72" />
        </section>
      )}


      {dados
        && medicamentoCarregado
        && !carregando
        && (
          <section className="mt-7 space-y-8">
            <div data-chat-context="medicamento selecionado">
              <p className="text-sm leading-6 text-muted">
                Código CATMAT selecionado —{" "}
                <strong className="font-semibold text-[var(--text)]">
                  {dados.produtos.length} produto(s)
                </strong>{" "}
                vinculado(s) a este item
              </p>

              <p className="mt-1 text-sm font-medium text-[var(--text)]">
                {rotuloMedicamento(medicamentoCarregado)}
              </p>

              {buscaConfirmada && (
                <p className="mt-1 text-xs text-muted">
                  Busca confirmada: “{buscaConfirmada}”
                </p>
              )}
            </div>


            <section
              data-chat-context="KPIs"
              className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4"
            >
              <KpiCard
                label="Estoque total (última posição)"
                value={numeroOuNulo(dados.resumo.estoque_total)}
                format={numeroCompacto}
              />

              <KpiCard
                label="Instituições com registro"
                value={numeroOuNulo(dados.resumo.instituicoes_com_registro)}
                format={numeroCompacto}
              />

              <KpiCard
                label="Instituições com estoque zerado"
                value={numeroOuNulo(dados.resumo.instituicoes_estoque_zerado)}
                format={numeroCompacto}
              />

              {/* Preço unitário: o compacto (1 casa) apagaria os centavos, então mostra o valor exato. */}
              <KpiCard
                label="Preço médio de compra"
                value={numeroOuNulo(dados.resumo.preco_medio_compra)}
                format={moedaExata}
                exact={moedaExata}
              />
            </section>


            <hr className="border-line" />


            <section data-chat-context="alerta de lotes">
              {dados.lotes
                .quantidade_lotes
                > 0 ? (
                <div className="rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)]">
                  <div className="flex items-start gap-2 px-4 py-4 text-sm font-medium leading-6 text-warning-text sm:px-5">
                    <Icon name="alert" size={18} className="mt-0.5" />
                    <span>
                      {dados.lotes.quantidade_lotes}{" "}
                      lote(s) com validade nos próximos 90 dias e estoque &gt; 0
                    </span>
                  </div>

                  <details className="border-t border-warning-border">
                    <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-warning-text sm:px-5">
                      Ver lotes vencendo
                    </summary>

                    <div className="bg-panel p-3 sm:p-5">
                      <DataTable
                        data={dados.lotes.items}
                        columns={colunasLotes}
                        pageSize={10}
                      />
                    </div>
                  </details>
                </div>
              ) : (
                <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-line bg-primary-tint px-4 py-3 text-sm leading-6 text-[var(--text)]">
                  <Icon name="info" size={18} className="mt-0.5 text-primary" />
                  Nenhum lote com estoque positivo vence nos próximos 90 dias.
                </div>
              )}
            </section>


            <section>
              <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                Estoque por UF
              </h2>

              {dados.estoqueUf.length
                > 0 ? (
                <div className="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-[2fr_1fr]">
                  <div className="min-w-0">
                    <ChartFrame as="h3"
                      title="Estoque total por UF"
                      subtitle="Soma da última posição de estoque das instituições de cada UF"
                      source="DATASUS"
                    >
                      <div className="h-80 w-full sm:h-96">
                        <ResponsiveContainer
                          width="100%"
                          height="100%"
                        >
                          <BarChart
                            data={estoqueUfGrafico}
                            margin={{
                              top: 12,
                              right: 8,
                              bottom: 8,
                              left: 0,
                            }}
                          >
                            <CartesianGrid {...grade} />

                            <XAxis
                              {...eixo}
                              dataKey="uf"
                              tick={{ ...eixo.tick, fontSize: 11 }}
                            />

                            <YAxis
                              {...eixo}
                              width={56}
                              tickFormatter={(value) => numeroCompacto(value)}
                            />

                            <Tooltip
                              {...tooltip}
                              formatter={(value) => numeroExato(numero(value))}
                            />

                            <Bar
                              dataKey="estoque_total"
                              name="Estoque total"
                              fill={paleta[0]}
                              radius={[
                                4,
                                4,
                                0,
                                0,
                              ]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </ChartFrame>
                  </div>

                  <div className="min-w-0">
                    <DataTable
                      data={dados.estoqueUf}
                      columns={colunasUf}
                      pageSize={10}
                    />
                  </div>
                </div>
              ) : (
                <div className="mt-4">
                  <EmptyState
                    title="Sem estoque por UF"
                    cause="Nenhuma instituição registrou estoque deste medicamento."
                  />
                </div>
              )}
            </section>


            <hr className="border-line" />


            <section>
              <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                Histórico de compras
              </h2>

              {dados.compras.length
                === 0 ? (
                <div className="mt-4">
                  <EmptyState
                    title="Sem compras registradas"
                    cause="Nenhuma compra pública deste item aparece na base."
                  />
                </div>
              ) : (
                <Tabs
                  value={abaCompras}
                  onValueChange={(valor) => setAbaCompras(valor as AbaCompras)}
                  className="mt-4"
                >
                  <TabsList
                    aria-label="Histórico de compras"
                    className="w-full flex-wrap justify-start group-data-[orientation=horizontal]/tabs:h-auto sm:w-fit sm:flex-nowrap sm:group-data-[orientation=horizontal]/tabs:h-9"
                  >
                    <TabsTrigger value="preco" className="min-h-8 px-4 sm:flex-none">
                      Evolução de preço
                    </TabsTrigger>

                    <TabsTrigger value="fornecedores" className="min-h-8 px-4 sm:flex-none">
                      Fornecedores
                    </TabsTrigger>

                    <TabsTrigger value="dados" className="min-h-8 px-4 sm:flex-none">
                      Dados brutos
                    </TabsTrigger>
                  </TabsList>


                  <TabsContent value="preco" className="mt-3">
                    <ChartFrame as="h3"
                      title="Evolução do preço médio"
                      subtitle="Preço unitário médio por data de compra"
                      source="DATASUS"
                    >
                      {evolucaoPrecoGrafico.length
                        > 0 ? (
                        <div className="h-72 w-full sm:h-96">
                          <ResponsiveContainer
                            width="100%"
                            height="100%"
                          >
                            <LineChart
                              data={evolucaoPrecoGrafico}
                              margin={{
                                top: 12,
                                right: 12,
                                bottom: 8,
                                left: 0,
                              }}
                            >
                              <CartesianGrid {...grade} />

                              <XAxis
                                {...eixo}
                                dataKey="data"
                                minTickGap={32}
                              />

                              <YAxis
                                {...eixo}
                                width={72}
                                tickFormatter={(value) => moedaCompacta(value)}
                              />

                              <Tooltip
                                {...tooltip}
                                cursor={{ stroke: "var(--beast-basic-600)" }}
                                formatter={(value) => moedaExata(numero(value))}
                              />

                              <Line
                                {...linha}
                                dataKey="preco"
                                name="Preço médio"
                                stroke={paleta[0]}
                                dot={dotPara(evolucaoPrecoGrafico.length)}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      ) : (
                        <EmptyState
                          title="Sem preços válidos"
                          cause="As compras deste item não têm preço unitário para construir a evolução."
                        />
                      )}
                    </ChartFrame>
                  </TabsContent>


                  <TabsContent value="fornecedores" className="mt-3">
                    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
                      <div className="min-w-0">
                        <ChartFrame as="h3"
                          title="Gasto total por fornecedor"
                          source="DATASUS"
                        >
                          <GraficoBarrasHorizontal
                            data={fornecedoresGrafico}
                            nomeKey="nome"
                            valorKey="valor"
                            cor={paleta[0]}
                            vazio="Nenhuma compra deste item tem fornecedor identificado."
                          />
                        </ChartFrame>
                      </div>

                      <div className="min-w-0">
                        <ChartFrame as="h3"
                          title="Gasto total por fabricante"
                          source="DATASUS"
                        >
                          <GraficoBarrasHorizontal
                            data={fabricantesGrafico}
                            nomeKey="nome"
                            valorKey="valor"
                            cor={paleta[0]}
                            vazio="Nenhuma compra deste item tem fabricante identificado."
                          />
                        </ChartFrame>
                      </div>
                    </div>
                  </TabsContent>


                  <TabsContent value="dados" className="mt-3">
                    <DataTable
                      data={dados.compras}
                      columns={colunasCompras}
                      pageSize={15}
                    />
                  </TabsContent>
                </Tabs>
              )}
            </section>
          </section>
        )}
    </main>
  );
}
