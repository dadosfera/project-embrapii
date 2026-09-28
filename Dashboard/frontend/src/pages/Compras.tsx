import {
  type FormEvent,
  useMemo,
  useRef,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartFrame } from "@/ui/ChartFrame";
import { EmptyState } from "@/ui/EmptyState";
import { ErrorState } from "@/ui/ErrorState";
import { Icon } from "@/ui/Icon";
import { KpiCard } from "@/ui/KpiCard";
import { PageHeader } from "@/ui/PageHeader";
import { categorica, dotPara, eixo, grade, linha, tooltip } from "@/ui/chartTheme";
import {
  SEM_DADO,
  data as dataBR,
  moedaCompacta,
  moedaExata,
  numeroCompacto,
  numeroExato,
} from "@/ui/format";

import {
  buscarComprasPorMes,
  buscarComprasPorModalidade,
  buscarComprasPorTipo,
  buscarComprasRecentes,
  buscarKpisCompras,
  buscarMedicamentos,
  buscarRankingFabricantes,
  buscarRankingFornecedores,
  listarProdutos,
  type CatmatItem,
  type CompraPorMes,
  type CompraPorModalidade,
  type CompraPorTipo,
  type CompraRecente,
  type FiltrosCompras,
  type KpisCompras,
  type RankingFabricanteCompra,
  type RankingFornecedorCompra,
} from "../lib/api";


type AbaCompras =
  | "fornecedores"
  | "fabricantes"
  | "modalidade"
  | "recentes";


type DadosCompras = {
  kpis: KpisCompras;
  porMes: CompraPorMes[];
  fornecedores: RankingFornecedorCompra[];
  fabricantes: RankingFabricanteCompra[];
  modalidades: CompraPorModalidade[];
  tipos: CompraPorTipo[];
  recentes: CompraRecente[];
};


type FiltrosConfirmados = FiltrosCompras & {
  produto_descricao: string;
  tipo_descricao: string;
};


/** O Radix Select não aceita item com value "": "Todos os produtos" usa esta sentinela na UI. */
const TODOS_PRODUTOS = "__todos__";


/** Coerção numérica (a API pode mandar decimal como string). */
function numero(
  valor: unknown,
) {
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


/** Participação com uma casa ("12,3%"). O format.ts não tem percentual, por isso fica aqui. */
function percentual(
  valor: unknown,
) {
  if (valor === null || valor === undefined) return SEM_DADO;
  return `${numero(valor).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}


const MESES_CURTOS = [
  "jan", "fev", "mar", "abr", "mai", "jun",
  "jul", "ago", "set", "out", "nov", "dez",
];


/** "AAAA-MM-DD" → "jan/24", rótulo do eixo mensal. O format.ts não tem mês, por isso fica aqui. */
function rotuloMes(
  valor: string,
) {
  const [
    ano,
    mes,
  ] = valor
    .slice(0, 10)
    .split("-")
    .map(Number);

  if (
    !ano
    || !mes
  ) {
    return valor;
  }

  return `${MESES_CURTOS[mes - 1]}/${String(ano).slice(-2)}`;
}


function hojeIso() {
  const agora =
    new Date();

  const ano =
    agora.getFullYear();

  const mes =
    String(
      agora.getMonth() + 1,
    ).padStart(
      2,
      "0",
    );

  const dia =
    String(
      agora.getDate(),
    ).padStart(
      2,
      "0",
    );

  return `${ano}-${mes}-${dia}`;
}


function umAnoAntesIso() {
  const agora =
    new Date();

  agora.setFullYear(
    agora.getFullYear() - 1,
  );

  const ano =
    agora.getFullYear();

  const mes =
    String(
      agora.getMonth() + 1,
    ).padStart(
      2,
      "0",
    );

  const dia =
    String(
      agora.getDate(),
    ).padStart(
      2,
      "0",
    );

  return `${ano}-${mes}-${dia}`;
}


function rotuloCatmat(
  item: CatmatItem,
) {
  return `${
    item.descricao_catmat
    ?? "Sem descrição"
  } — CATMAT ${
    item.codigo_catmat
    ?? "sem código"
  }`;
}


function truncar(
  valor: unknown,
  limite = 25,
) {
  const texto =
    String(
      valor
      ?? "Não informado",
    );

  if (
    texto.length
    <= limite
  ) {
    return texto;
  }

  return `${texto.slice(
    0,
    limite - 1,
  )}…`;
}


function GraficoRanking({
  dados,
  nomeKey,
  cor,
}: {
  dados: Record<
    string,
    string | number
  >[];
  nomeKey: string;
  cor: string;
}) {
  if (
    dados.length === 0
  ) {
    return (
      <EmptyState
        title="Sem dados para o ranking"
        cause="Não há compras no período selecionado com esses filtros."
      />
    );
  }

  const altura =
    Math.max(
      300,
      dados.length * 38,
    );

  return (
    <div
      className="w-full overflow-hidden"
      style={{
        height: altura,
      }}
    >
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <BarChart
          data={dados}
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
            tickFormatter={(valor) => moedaCompacta(numero(valor))}
          />

          <YAxis
            {...eixo}
            type="category"
            dataKey={nomeKey}
            width={120}
            tickFormatter={(valor) => truncar(valor, 20)}
          />

          <Tooltip
            {...tooltip}
            formatter={(valor) => moedaExata(numero(valor))}
          />

          <Bar
            dataKey="valor_total"
            name="Valor total"
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


export function Compras() {
  const [
    buscaProduto,
    setBuscaProduto,
  ] = useState("");

  const [
    buscandoProduto,
    setBuscandoProduto,
  ] = useState(false);

  const [
    opcoesCatmat,
    setOpcoesCatmat,
  ] =
    useState<
      CatmatItem[]
    >([]);

  const [
    avisoBusca,
    setAvisoBusca,
  ] =
    useState<
      string | null
    >(null);

  const [
    catmatSelecionado,
    setCatmatSelecionado,
  ] = useState("");

  const [
    dataInicio,
    setDataInicio,
  ] =
    useState(
      umAnoAntesIso(),
    );

  const [
    dataFim,
    setDataFim,
  ] =
    useState(
      hojeIso(),
    );

  const [
    tipoCompra,
    setTipoCompra,
  ] =
    useState("Todos");

  const [
    carregando,
    setCarregando,
  ] = useState(false);

  const [
    erro,
    setErro,
  ] =
    useState<
      string | null
    >(null);

  // Falha de requisição: guarda o erro real para o ErrorState (erro fica para validação e avisos).
  const [
    falhaCarga,
    setFalhaCarga,
  ] =
    useState<unknown>(null);

  const formFiltros =
    useRef<HTMLFormElement>(null);

  const [
    filtrosConfirmados,
    setFiltrosConfirmados,
  ] =
    useState<
      FiltrosConfirmados | null
    >(null);

  const [
    dados,
    setDados,
  ] =
    useState<
      DadosCompras | null
    >(null);

  const [
    aba,
    setAba,
  ] =
    useState<AbaCompras>(
      "fornecedores",
    );


  const catmatAtual =
    opcoesCatmat.find(
      (item) =>
        String(
          item.catmat_id,
        )
        === catmatSelecionado,
    );


  async function buscarProduto(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const termo =
      buscaProduto.trim();

    if (!termo) {
      setOpcoesCatmat([]);
      setCatmatSelecionado("");
      setAvisoBusca(null);
      return;
    }

    setBuscandoProduto(true);
    setAvisoBusca(null);

    try {
      const itens =
        await buscarMedicamentos(
          termo,
        );

      setOpcoesCatmat(
        itens,
      );
      setCatmatSelecionado(
        "",
      );

      if (
        itens.length === 0
      ) {
        setAvisoBusca(
          "Nenhum CATMAT foi encontrado para essa busca. Você ainda pode consultar todos os produtos.",
        );
      }
    } catch (error) {
      setAvisoBusca(
        error
          instanceof Error
          ? error.message
          : "Não foi possível buscar produtos.",
      );
    } finally {
      setBuscandoProduto(false);
    }
  }


  async function aplicarFiltros(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setErro(null);
    setFalhaCarga(null);

    if (
      !dataInicio
      || !dataFim
    ) {
      setErro(
        "Informe a data inicial e a data final.",
      );
      return;
    }

    if (
      dataFim
      < dataInicio
    ) {
      setErro(
        "A data final não pode ser anterior à data inicial.",
      );
      return;
    }

    let catmatId:
      number | null =
        null;

    let produtoDescricao =
      "Todos os produtos";

    if (
      catmatSelecionado
    ) {
      if (
        !catmatAtual
      ) {
        setErro(
          "Selecione um produto válido.",
        );
        return;
      }

      catmatId =
        catmatAtual
          .catmat_id;

      produtoDescricao =
        rotuloCatmat(
          catmatAtual,
        );
    }

    setCarregando(true);
    setDados(null);
    setAba(
      "fornecedores",
    );

    try {
      if (
        catmatId !== null
      ) {
        const produtos =
          await listarProdutos(
            catmatId,
          );

        if (
          produtos.length === 0
        ) {
          setErro(
            "O CATMAT selecionado não possui produtos vinculados.",
          );
          return;
        }
      }

      const filtros:
        FiltrosCompras = {
          data_inicio:
            dataInicio,
          data_fim:
            dataFim,
          catmat_id:
            catmatId,
          tipo_compra:
            tipoCompra
            === "Todos"
              ? ""
              : tipoCompra,
        };

      const [
        kpis,
        porMes,
        fornecedores,
        fabricantes,
        modalidades,
        tipos,
        recentes,
      ] =
        await Promise.all([
          buscarKpisCompras(
            filtros,
          ),
          buscarComprasPorMes(
            filtros,
          ),
          buscarRankingFornecedores(
            filtros,
            15,
          ),
          buscarRankingFabricantes(
            filtros,
            15,
          ),
          buscarComprasPorModalidade(
            filtros,
          ),
          buscarComprasPorTipo(
            filtros,
          ),
          buscarComprasRecentes(
            filtros,
            500,
          ),
        ]);

      setFiltrosConfirmados({
        ...filtros,
        produto_descricao:
          produtoDescricao,
        tipo_descricao:
          tipoCompra,
      });

      setDados({
        kpis,
        porMes,
        fornecedores,
        fabricantes,
        modalidades,
        tipos,
        recentes,
      });
    } catch (error) {
      setFalhaCarga(error);
    } finally {
      setCarregando(false);
    }
  }


  const totalComprado =
    numero(
      dados?.kpis
        .valor_total,
    );


  const mensalGrafico =
    useMemo(
      () =>
        (
          dados?.porMes
          ?? []
        ).map(
          (item) => ({
            mes:
              rotuloMes(
                item.mes,
              ),
            valor_total:
              numero(
                item.valor_total,
              ),
            numero_compras:
              numero(
                item.numero_compras,
              ),
          }),
        ),
      [dados],
    );


  const fornecedoresTabela =
    useMemo(
      () =>
        (
          dados
            ?.fornecedores
          ?? []
        ).map(
          (item) => ({
            ...item,
            participacao_percentual:
              totalComprado
              > 0
                ? (
                    numero(
                      item.valor_total,
                    )
                    / totalComprado
                  )
                  * 100
                : 0,
          }),
        ),
      [
        dados,
        totalComprado,
      ],
    );


  const fabricantesTabela =
    useMemo(
      () =>
        (
          dados
            ?.fabricantes
          ?? []
        ).map(
          (item) => ({
            ...item,
            participacao_percentual:
              totalComprado
              > 0
                ? (
                    numero(
                      item.valor_total,
                    )
                    / totalComprado
                  )
                  * 100
                : 0,
          }),
        ),
      [
        dados,
        totalComprado,
      ],
    );


  const colunasFornecedores =
    useMemo<
      ColumnDef<
        RankingFornecedorCompra
        & {
          participacao_percentual:
            number;
        },
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Fornecedor",
          accessorKey:
            "fornecedor",
        },
        {
          header:
            "Valor total",
          accessorKey:
            "valor_total",
          cell: ({
            row,
          }) =>
            moedaExata(
              row.original
                .valor_total,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .numero_compras,
            ),
          meta: { align: "right" },
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .quantidade_itens,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Participação (%)",
          accessorKey:
            "participacao_percentual",
          cell: ({
            row,
          }) =>
            percentual(
              row.original
                .participacao_percentual,
            ),
          meta: { align: "right" },
        },
      ],
      [],
    );


  const colunasFabricantes =
    useMemo<
      ColumnDef<
        RankingFabricanteCompra
        & {
          participacao_percentual:
            number;
        },
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Fabricante",
          accessorKey:
            "fabricante",
        },
        {
          header:
            "Valor total",
          accessorKey:
            "valor_total",
          cell: ({
            row,
          }) =>
            moedaExata(
              row.original
                .valor_total,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .numero_compras,
            ),
          meta: { align: "right" },
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .quantidade_itens,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Participação (%)",
          accessorKey:
            "participacao_percentual",
          cell: ({
            row,
          }) =>
            percentual(
              row.original
                .participacao_percentual,
            ),
          meta: { align: "right" },
        },
      ],
      [],
    );


  const colunasModalidades =
    useMemo<
      ColumnDef<
        CompraPorModalidade,
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Modalidade",
          accessorKey:
            "modalidade",
        },
        {
          header:
            "Valor total",
          accessorKey:
            "valor_total",
          cell: ({
            row,
          }) =>
            moedaExata(
              row.original
                .valor_total,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .numero_compras,
            ),
          meta: { align: "right" },
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .quantidade_itens,
            ),
          meta: { align: "right" },
        },
      ],
      [],
    );


  const colunasTipos =
    useMemo<
      ColumnDef<
        CompraPorTipo,
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Tipo da compra",
          accessorKey:
            "tipo_compra",
        },
        {
          header:
            "Valor total",
          accessorKey:
            "valor_total",
          cell: ({
            row,
          }) =>
            moedaExata(
              row.original
                .valor_total,
            ),
          meta: { align: "right" },
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .numero_compras,
            ),
          meta: { align: "right" },
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            numeroExato(
              row.original
                .quantidade_itens,
            ),
          meta: { align: "right" },
        },
      ],
      [],
    );


  const colunasRecentes =
    useMemo<
      ColumnDef<
        CompraRecente,
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
            "Código CATMAT",
          accessorKey:
            "codigo_catmat",
          cell: ({
            row,
          }) =>
            row.original
              .codigo_catmat
            ?? "—",
          meta: { priority: "low" },
        },
        {
          header: "Produto",
          accessorKey:
            "descricao_catmat",
          cell: ({
            row,
          }) =>
            row.original
              .descricao_catmat
            ?? "—",
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
            numeroExato(
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


  // Resolve a paleta uma vez por montagem (lê as variáveis CSS do documento).
  const paleta = useMemo(() => categorica(), []);


  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <PageHeader
        icon="cart"
        title="Compras"
        description="Analise valores, fornecedores, fabricantes, modalidades e evolução das compras registradas."
      />


      <section className="mt-7 rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--text)]">
          <Icon name="funnel" size={18} className="text-muted" />
          Filtros
        </h2>

        <form
          onSubmit={buscarProduto}
          className="mt-5"
        >
          <label
            htmlFor="busca-produto-compras"
            className="block text-sm font-semibold text-[var(--text)]"
          >
            Filtrar por medicamento ou produto CATMAT (opcional)
          </label>

          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <Input
              id="busca-produto-compras"
              value={buscaProduto}
              onChange={(event) => setBuscaProduto(event.target.value)}
              placeholder="Ex.: dipirona, insulina, seringa..."
              className="h-10 bg-panel sm:flex-1"
            />

            <Button
              type="submit"
              variant="outline"
              disabled={buscandoProduto}
              className="h-10 w-full px-5 sm:w-auto"
            >
              <Icon name="search" size={16} />
              {buscandoProduto
                ? "Buscando..."
                : "Buscar CATMAT"}
            </Button>
          </div>
        </form>


        {avisoBusca && (
          <div
            role="status"
            className="mt-3 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text"
          >
            <Icon name="alert" size={18} className="mt-0.5" />
            {avisoBusca}
          </div>
        )}


        <form
          ref={formFiltros}
          onSubmit={aplicarFiltros}
          className="mt-6 border-t border-line pt-6"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="data-inicio"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Data inicial
              </label>

              <Input
                id="data-inicio"
                type="date"
                value={dataInicio}
                max={hojeIso()}
                onChange={(event) => setDataInicio(event.target.value)}
                className="mt-2 h-10 bg-panel"
              />
            </div>

            <div>
              <label
                htmlFor="data-fim"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Data final
              </label>

              <Input
                id="data-fim"
                type="date"
                value={dataFim}
                max={hojeIso()}
                onChange={(event) => setDataFim(event.target.value)}
                className="mt-2 h-10 bg-panel"
              />
            </div>

            <div className="min-w-0">
              <label
                htmlFor="produto-compras"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Produto
              </label>

              <Select
                value={catmatSelecionado || TODOS_PRODUTOS}
                onValueChange={(valor) =>
                  setCatmatSelecionado(valor === TODOS_PRODUTOS ? "" : valor)
                }
              >
                <SelectTrigger
                  id="produto-compras"
                  className="mt-2 h-10 w-full min-w-0 bg-panel data-[size=default]:h-10"
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent position="popper" className="max-w-[min(90vw,48rem)]">
                  <SelectItem value={TODOS_PRODUTOS}>
                    Todos os produtos
                  </SelectItem>

                  {opcoesCatmat.map((item) => (
                    <SelectItem
                      key={item.catmat_id}
                      value={String(item.catmat_id)}
                    >
                      {rotuloCatmat(item)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label
                htmlFor="tipo-compra"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Tipo da compra
              </label>

              <Select
                value={tipoCompra}
                onValueChange={setTipoCompra}
              >
                <SelectTrigger
                  id="tipo-compra"
                  className="mt-2 h-10 w-full bg-panel data-[size=default]:h-10"
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent position="popper">
                  <SelectItem value="Todos">Todos</SelectItem>
                  <SelectItem value="ADMINISTRATIVA">ADMINISTRATIVA</SelectItem>
                  <SelectItem value="JUDICIAL">JUDICIAL</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            type="submit"
            disabled={carregando}
            className="mx-auto mt-6 flex h-10 w-full sm:w-1/2 lg:w-1/4"
          >
            {carregando
              ? "Carregando análises..."
              : "Pesquisar"}
          </Button>
        </form>
      </section>


      {erro && (
        <div
          role="status"
          className="mt-5 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text"
        >
          <Icon name="alert" size={18} className="mt-0.5" />
          {erro}
        </div>
      )}


      {falhaCarga != null && (
        <div className="mt-5">
          <ErrorState
            error={falhaCarga}
            onRetry={() => formFiltros.current?.requestSubmit()}
          />
        </div>
      )}


      {!filtrosConfirmados
        && !carregando
        && (
          <p className="mt-5 flex items-center gap-2 text-sm leading-6 text-muted">
            <Icon name="info" size={16} />
            <span>
              Escolha o período e clique em <strong className="font-semibold text-[var(--text)]">Pesquisar</strong> para carregar as análises.
            </span>
          </p>
        )}


      {carregando && (
        <section className="mt-6 space-y-4" aria-busy="true">
          <Skeleton className="h-8 w-full max-w-2xl" />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map((item) => (
              <Skeleton key={item} className="h-28" />
            ))}
          </div>

          <Skeleton className="h-80" />
        </section>
      )}


      {dados
        && filtrosConfirmados
        && !carregando
        && (
          <section className="mt-6 space-y-8">
            <p className="text-sm leading-6 text-muted">
              Filtros aplicados:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {dataBR(filtrosConfirmados.data_inicio)}
              </strong>{" "}
              até{" "}
              <strong className="font-semibold text-[var(--text)]">
                {dataBR(filtrosConfirmados.data_fim)}
              </strong>
              {" | "}Produto:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {filtrosConfirmados.produto_descricao}
              </strong>
              {" | "}Tipo:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {filtrosConfirmados.tipo_descricao}
              </strong>
            </p>


            {numero(
              dados.kpis
                .numero_compras,
            ) === 0 ? (
              <EmptyState
                title="Nenhuma compra encontrada"
                cause="Não há compras no período selecionado com esses filtros."
              />
            ) : (
              <>
                <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4">
                  <KpiCard
                    label="Valor total comprado"
                    value={numeroOuNulo(dados.kpis.valor_total)}
                    format={moedaCompacta}
                    exact={moedaExata}
                  />

                  <KpiCard
                    label="Registros de compra"
                    value={numeroOuNulo(dados.kpis.numero_compras)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Quantidade de itens"
                    value={numeroOuNulo(dados.kpis.quantidade_itens)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Fornecedores"
                    value={numeroOuNulo(dados.kpis.numero_fornecedores)}
                    format={numeroCompacto}
                  />
                </section>


                <hr className="border-line" />


                <section>
                  <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                    Evolução mensal das compras
                  </h2>

                  {mensalGrafico.length
                    === 0 ? (
                    <div className="mt-4">
                      <EmptyState
                        title="Sem série mensal"
                        cause="Não há compras no período selecionado com esses filtros."
                      />
                    </div>
                  ) : (
                    <div className="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-2">
                      <div className="min-w-0">
                        <ChartFrame
                          title="Valor total comprado por mês"
                          source="DATASUS"
                        >
                          <div className="h-72 w-full sm:h-80">
                            <ResponsiveContainer
                              width="100%"
                              height="100%"
                            >
                              <LineChart
                                data={mensalGrafico}
                                margin={{
                                  top: 8,
                                  right: 8,
                                  bottom: 8,
                                  left: 0,
                                }}
                              >
                                <CartesianGrid {...grade} />

                                <XAxis
                                  {...eixo}
                                  dataKey="mes"
                                  minTickGap={30}
                                />

                                <YAxis
                                  {...eixo}
                                  width={75}
                                  tickFormatter={(valor) => moedaCompacta(numero(valor))}
                                />

                                <Tooltip
                                  {...tooltip}
                                  cursor={{ stroke: "var(--beast-basic-600)" }}
                                  formatter={(valor) => moedaExata(numero(valor))}
                                />

                                <Line
                                  {...linha}
                                  dataKey="valor_total"
                                  name="Valor total"
                                  stroke={paleta[0]}
                                  dot={dotPara(mensalGrafico.length)}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </ChartFrame>
                      </div>


                      <div className="min-w-0">
                        <ChartFrame
                          title="Número de compras por mês"
                          source="DATASUS"
                        >
                          <div className="h-72 w-full sm:h-80">
                            <ResponsiveContainer
                              width="100%"
                              height="100%"
                            >
                              <LineChart
                                data={mensalGrafico}
                                margin={{
                                  top: 8,
                                  right: 8,
                                  bottom: 8,
                                  left: 0,
                                }}
                              >
                                <CartesianGrid {...grade} />

                                <XAxis
                                  {...eixo}
                                  dataKey="mes"
                                  minTickGap={30}
                                />

                                <YAxis
                                  {...eixo}
                                  width={48}
                                  tickFormatter={(valor) => numeroCompacto(numero(valor))}
                                />

                                <Tooltip
                                  {...tooltip}
                                  cursor={{ stroke: "var(--beast-basic-600)" }}
                                  formatter={(valor) => numeroExato(numero(valor))}
                                />

                                <Line
                                  {...linha}
                                  dataKey="numero_compras"
                                  name="Compras"
                                  stroke={paleta[0]}
                                  dot={dotPara(mensalGrafico.length)}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </ChartFrame>
                      </div>
                    </div>
                  )}
                </section>


                <hr className="border-line" />


                <Tabs
                  value={aba}
                  onValueChange={(valor) => setAba(valor as AbaCompras)}
                >
                  <TabsList
                    aria-label="Análises de compras"
                    className="w-full flex-wrap justify-start group-data-[orientation=horizontal]/tabs:h-auto sm:w-fit sm:flex-nowrap sm:group-data-[orientation=horizontal]/tabs:h-9"
                  >
                    {[
                      { id: "fornecedores", label: "Fornecedores" },
                      { id: "fabricantes", label: "Fabricantes" },
                      { id: "modalidade", label: "Modalidade e tipo" },
                      { id: "recentes", label: "Compras recentes" },
                    ].map((item) => (
                      <TabsTrigger
                        key={item.id}
                        value={item.id}
                        className="min-h-8 px-4 sm:flex-none"
                      >
                        {item.label}
                      </TabsTrigger>
                    ))}
                  </TabsList>


                  <TabsContent value="fornecedores" className="mt-3">
                    {fornecedoresTabela.length
                      === 0 ? (
                      <EmptyState
                        title="Sem fornecedores"
                        cause="Não há compras com fornecedor identificado no período selecionado."
                      />
                    ) : (
                      <div className="space-y-5">
                        <ChartFrame
                          title="Principais fornecedores"
                          subtitle="Valor total comprado, 15 maiores"
                          source="DATASUS"
                        >
                          <GraficoRanking
                            dados={fornecedoresTabela.map((item) => ({
                              fornecedor: item.fornecedor,
                              valor_total: numero(item.valor_total),
                            }))}
                            nomeKey="fornecedor"
                            cor={paleta[0]}
                          />
                        </ChartFrame>

                        <div className="min-w-0 w-full">
                          <DataTable
                            data={fornecedoresTabela}
                            columns={colunasFornecedores}
                            pageSize={8}
                          />
                        </div>
                      </div>
                    )}
                  </TabsContent>


                  <TabsContent value="fabricantes" className="mt-3">
                    {fabricantesTabela.length
                      === 0 ? (
                      <EmptyState
                        title="Sem fabricantes"
                        cause="Não há compras com fabricante identificado no período selecionado."
                      />
                    ) : (
                      <div className="space-y-5">
                        <ChartFrame
                          title="Principais fabricantes"
                          subtitle="Valor total comprado, 15 maiores"
                          source="DATASUS"
                        >
                          <GraficoRanking
                            dados={fabricantesTabela.map((item) => ({
                              fabricante: item.fabricante,
                              valor_total: numero(item.valor_total),
                            }))}
                            nomeKey="fabricante"
                            cor={paleta[0]}
                          />
                        </ChartFrame>

                        <div className="min-w-0 w-full">
                          <DataTable
                            data={fabricantesTabela}
                            columns={colunasFabricantes}
                            pageSize={8}
                          />
                        </div>
                      </div>
                    )}
                  </TabsContent>


                  <TabsContent value="modalidade" className="mt-3">
                    <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                      <div className="min-w-0 space-y-4">
                        {dados.modalidades.length
                          === 0 ? (
                          <EmptyState
                            title="Sem modalidades"
                            cause="Não há compras no período selecionado com esses filtros."
                          />
                        ) : (
                          <>
                            <ChartFrame
                              title="Compras por modalidade"
                              source="DATASUS"
                            >
                              <GraficoRanking
                                dados={dados.modalidades.map((item) => ({
                                  modalidade: item.modalidade,
                                  valor_total: numero(item.valor_total),
                                }))}
                                nomeKey="modalidade"
                                cor={paleta[0]}
                              />
                            </ChartFrame>

                            <DataTable
                              data={dados.modalidades}
                              columns={colunasModalidades}
                              pageSize={8}
                            />
                          </>
                        )}
                      </div>


                      <div className="min-w-0 space-y-4">
                        {dados.tipos.length
                          === 0 ? (
                          <EmptyState
                            title="Sem tipos de compra"
                            cause="Não há compras no período selecionado com esses filtros."
                          />
                        ) : (
                          <>
                            <ChartFrame
                              title="Compras por tipo"
                              source="DATASUS"
                            >
                              <GraficoRanking
                                dados={dados.tipos.map((item) => ({
                                  tipo_compra: item.tipo_compra,
                                  valor_total: numero(item.valor_total),
                                }))}
                                nomeKey="tipo_compra"
                                cor={paleta[0]}
                              />
                            </ChartFrame>

                            <DataTable
                              data={dados.tipos}
                              columns={colunasTipos}
                              pageSize={8}
                            />
                          </>
                        )}
                      </div>
                    </div>
                  </TabsContent>


                  <TabsContent value="recentes" className="mt-3">
                    <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                      Compras mais recentes
                    </h2>

                    <p className="mt-1 mb-4 text-sm leading-6 text-muted">
                      São exibidos no máximo 500 registros, ordenados da compra mais recente para a mais antiga.
                    </p>

                    <DataTable
                      data={dados.recentes}
                      columns={colunasRecentes}
                      pageSize={15}
                      emptyMessage="Não há compras recentes para exibir."
                    />
                  </TabsContent>
                </Tabs>
              </>
            )}
          </section>
        )}
    </main>
  );
}
