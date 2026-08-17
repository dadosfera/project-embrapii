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


const formatadorNumero =
  new Intl.NumberFormat(
    "pt-BR",
    {
      maximumFractionDigits: 0,
    },
  );


const formatadorMoeda =
  new Intl.NumberFormat(
    "pt-BR",
    {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  );


const formatadorPercentual =
  new Intl.NumberFormat(
    "pt-BR",
    {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    },
  );


function formatarNumero(
  valor: unknown,
) {
  return formatadorNumero.format(
    numero(valor),
  );
}


function formatarMoeda(
  valor: unknown,
) {
  return formatadorMoeda.format(
    numero(valor),
  );
}


function formatarPercentual(
  valor: unknown,
) {
  return `${formatadorPercentual.format(
    numero(valor),
  )}%`;
}


function formatarData(
  valor: string | null,
) {
  if (!valor) {
    return "—";
  }

  const data =
    valor.slice(0, 10);

  const [
    ano,
    mes,
    dia,
  ] = data
    .split("-")
    .map(Number);

  if (
    !ano
    || !mes
    || !dia
  ) {
    return valor;
  }

  return new Intl.DateTimeFormat(
    "pt-BR",
  ).format(
    new Date(
      ano,
      mes - 1,
      dia,
    ),
  );
}


function formatarMes(
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

  return new Intl.DateTimeFormat(
    "pt-BR",
    {
      month: "short",
      year: "2-digit",
    },
  ).format(
    new Date(
      ano,
      mes - 1,
      1,
    ),
  );
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


function Kpi({
  titulo,
  valor,
}: {
  titulo: string;
  valor: string;
}) {
  return (
    <article className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
      <p className="text-sm leading-5 text-slate-500">
        {titulo}
      </p>

      <p className="mt-3 break-words text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
        {valor}
      </p>
    </article>
  );
}


function Vazio({
  children,
}: {
  children: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-slate-200 bg-teal-50/40 px-4 py-9 text-center text-sm leading-6 text-slate-500">
      {children}
    </div>
  );
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
}: {
  dados: Record<
    string,
    string | number
  >[];
  nomeKey: string;
}) {
  if (
    dados.length === 0
  ) {
    return (
      <Vazio>
        Não há dados para exibir.
      </Vazio>
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
            strokeDasharray="3 3"
            horizontal={false}
          />

          <XAxis
            type="number"
            tickFormatter={(
              valor,
            ) =>
              formatadorMoeda.format(
                numero(valor),
              )
            }
            fontSize={10}
          />

          <YAxis
            type="category"
            dataKey={nomeKey}
            width={120}
            tickFormatter={(
              valor,
            ) =>
              truncar(
                valor,
                20,
              )
            }
            tickLine={false}
            fontSize={10}
          />

          <Tooltip
            formatter={(
              valor,
            ) =>
              formatarMoeda(
                valor,
              )
            }
          />

          <Bar
            dataKey="valor_total"
            fill="var(--color-brand-blue)"
            radius={[
              0,
              5,
              5,
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
          throw new Error(
            "O CATMAT selecionado não possui produtos vinculados.",
          );
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
      setErro(
        error
          instanceof Error
          ? error.message
          : "Não foi possível carregar as análises de compras.",
      );
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
              formatarMes(
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
            formatarMoeda(
              row.original
                .valor_total,
            ),
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .numero_compras,
            ),
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .quantidade_itens,
            ),
        },
        {
          header:
            "Participação (%)",
          accessorKey:
            "participacao_percentual",
          cell: ({
            row,
          }) =>
            formatarPercentual(
              row.original
                .participacao_percentual,
            ),
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
            formatarMoeda(
              row.original
                .valor_total,
            ),
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .numero_compras,
            ),
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .quantidade_itens,
            ),
        },
        {
          header:
            "Participação (%)",
          accessorKey:
            "participacao_percentual",
          cell: ({
            row,
          }) =>
            formatarPercentual(
              row.original
                .participacao_percentual,
            ),
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
            formatarMoeda(
              row.original
                .valor_total,
            ),
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .numero_compras,
            ),
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .quantidade_itens,
            ),
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
            formatarMoeda(
              row.original
                .valor_total,
            ),
        },
        {
          header:
            "Compras",
          accessorKey:
            "numero_compras",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .numero_compras,
            ),
        },
        {
          header: "Itens",
          accessorKey:
            "quantidade_itens",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .quantidade_itens,
            ),
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
            formatarData(
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
            formatarNumero(
              row.original
                .quantidade_de_itens,
            ),
        },
        {
          header:
            "Preço unitário",
          accessorKey:
            "preco_unitario",
          cell: ({
            row,
          }) =>
            formatarMoeda(
              row.original
                .preco_unitario,
            ),
        },
        {
          header:
            "Preço total",
          accessorKey:
            "preco_total",
          cell: ({
            row,
          }) =>
            formatarMoeda(
              row.original
                .preco_total,
            ),
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


  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          🛒 Compras
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
          Analise valores, fornecedores, fabricantes, modalidades
          e evolução das compras registradas.
        </p>
      </header>


      <section className="mt-7 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-6">
        <h2 className="text-lg font-semibold text-slate-900">
          Filtros
        </h2>

        <form
          onSubmit={
            buscarProduto
          }
          className="mt-5"
        >
          <label
            htmlFor="busca-produto-compras"
            className="block text-sm font-semibold text-slate-800"
          >
            Filtrar por medicamento ou produto CATMAT (opcional)
          </label>

          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <input
              id="busca-produto-compras"
              value={
                buscaProduto
              }
              onChange={(
                event,
              ) =>
                setBuscaProduto(
                  event.target
                    .value,
                )
              }
              placeholder="Ex.: dipirona, insulina, seringa..."
              className="h-12 min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
            />

            <button
              type="submit"
              disabled={
                buscandoProduto
              }
              className="h-12 w-full rounded-xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:bg-teal-50/40 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {buscandoProduto
                ? "Buscando..."
                : "Buscar CATMAT"}
            </button>
          </div>
        </form>


        {avisoBusca && (
          <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
            {avisoBusca}
          </div>
        )}


        <form
          onSubmit={
            aplicarFiltros
          }
          className="mt-6 border-t border-slate-200 pt-6"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="data-inicio"
                className="block text-sm font-semibold text-slate-800"
              >
                Data inicial
              </label>

              <input
                id="data-inicio"
                type="date"
                value={
                  dataInicio
                }
                max={
                  hojeIso()
                }
                onChange={(
                  event,
                ) =>
                  setDataInicio(
                    event.target
                      .value,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
              />
            </div>

            <div>
              <label
                htmlFor="data-fim"
                className="block text-sm font-semibold text-slate-800"
              >
                Data final
              </label>

              <input
                id="data-fim"
                type="date"
                value={
                  dataFim
                }
                max={
                  hojeIso()
                }
                onChange={(
                  event,
                ) =>
                  setDataFim(
                    event.target
                      .value,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
              />
            </div>

            <div>
              <label
                htmlFor="produto-compras"
                className="block text-sm font-semibold text-slate-800"
              >
                Produto
              </label>

              <select
                id="produto-compras"
                value={
                  catmatSelecionado
                }
                onChange={(
                  event,
                ) =>
                  setCatmatSelecionado(
                    event.target
                      .value,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
              >
                <option value="">
                  Todos os produtos
                </option>

                {opcoesCatmat.map(
                  (item) => (
                    <option
                      key={
                        item.catmat_id
                      }
                      value={
                        item.catmat_id
                      }
                    >
                      {rotuloCatmat(
                        item,
                      )}
                    </option>
                  ),
                )}
              </select>
            </div>

            <div>
              <label
                htmlFor="tipo-compra"
                className="block text-sm font-semibold text-slate-800"
              >
                Tipo da compra
              </label>

              <select
                id="tipo-compra"
                value={
                  tipoCompra
                }
                onChange={(
                  event,
                ) =>
                  setTipoCompra(
                    event.target
                      .value,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
              >
                <option>
                  Todos
                </option>

                <option>
                  ADMINISTRATIVA
                </option>

                <option>
                  JUDICIAL
                </option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={
              carregando
            }
            className="mx-auto mt-6 block min-h-12 w-full rounded-xl bg-teal-700 px-6 py-3 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-1/2 lg:w-1/4"
          >
            {carregando
              ? "Carregando análises..."
              : "Pesquisar"}
          </button>
        </form>
      </section>


      {erro && (
        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800">
          {erro}
        </div>
      )}


      {!filtrosConfirmados
        && !carregando
        && (
          <div className="mt-5 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-800">
            Escolha o período e clique em <strong>Aplicar filtros</strong> para carregar as análises.
          </div>
        )}


      {carregando && (
        <section className="mt-6 space-y-4">
          <div className="h-8 w-full max-w-2xl animate-pulse rounded bg-slate-200" />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map(
              (item) => (
                <div
                  key={item}
                  className="h-28 animate-pulse rounded-2xl bg-slate-200"
                />
              ),
            )}
          </div>

          <div className="h-80 animate-pulse rounded-2xl bg-slate-200" />
        </section>
      )}


      {dados
        && filtrosConfirmados
        && !carregando
        && (
          <section className="mt-6 space-y-8">
            <p className="text-sm leading-6 text-slate-500">
              Filtros aplicados:{" "}
              <strong className="font-semibold text-slate-700">
                {formatarData(
                  filtrosConfirmados
                    .data_inicio,
                )}
              </strong>{" "}
              até{" "}
              <strong className="font-semibold text-slate-700">
                {formatarData(
                  filtrosConfirmados
                    .data_fim,
                )}
              </strong>
              {" | "}Produto:{" "}
              <strong className="font-semibold text-slate-700">
                {
                  filtrosConfirmados
                    .produto_descricao
                }
              </strong>
              {" | "}Tipo:{" "}
              <strong className="font-semibold text-slate-700">
                {
                  filtrosConfirmados
                    .tipo_descricao
                }
              </strong>
            </p>


            {numero(
              dados.kpis
                .numero_compras,
            ) === 0 ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm leading-6 text-amber-900">
                Nenhuma compra foi encontrada para os filtros selecionados.
              </div>
            ) : (
              <>
                <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4">
                  <Kpi
                    titulo="Valor total comprado"
                    valor={
                      formatarMoeda(
                        dados.kpis
                          .valor_total,
                      )
                    }
                  />

                  <Kpi
                    titulo="Registros de compra"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .numero_compras,
                      )
                    }
                  />

                  <Kpi
                    titulo="Quantidade de itens"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .quantidade_itens,
                      )
                    }
                  />

                  <Kpi
                    titulo="Fornecedores"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .numero_fornecedores,
                      )
                    }
                  />
                </section>


                <hr className="border-slate-200" />


                <section>
                  <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                    Evolução mensal das compras
                  </h2>

                  {mensalGrafico.length
                    === 0 ? (
                    <div className="mt-4">
                      <Vazio>
                        Não há dados mensais para os filtros aplicados.
                      </Vazio>
                    </div>
                  ) : (
                    <div className="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-2">
                      <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                        <p className="text-sm font-semibold text-slate-700">
                          Valor total comprado por mês
                        </p>

                        <div className="mt-4 h-72 w-full sm:h-80">
                          <ResponsiveContainer
                            width="100%"
                            height="100%"
                          >
                            <LineChart
                              data={
                                mensalGrafico
                              }
                              margin={{
                                top: 8,
                                right: 8,
                                bottom: 8,
                                left: 0,
                              }}
                            >
                              <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={
                                  false
                                }
                              />

                              <XAxis
                                dataKey="mes"
                                minTickGap={
                                  30
                                }
                                fontSize={
                                  10
                                }
                              />

                              <YAxis
                                width={
                                  75
                                }
                                tickFormatter={(
                                  valor,
                                ) =>
                                  formatadorMoeda.format(
                                    numero(
                                      valor,
                                    ),
                                  )
                                }
                                fontSize={
                                  10
                                }
                              />

                              <Tooltip
                                formatter={(
                                  valor,
                                ) =>
                                  formatarMoeda(
                                    valor,
                                  )
                                }
                              />

                              <Line
                                type="monotone"
                                dataKey="valor_total"
                                stroke="var(--color-brand-blue)"
                                strokeWidth={
                                  2
                                }
                                dot={
                                  false
                                }
                                activeDot={{
                                  r: 4,
                                }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </article>


                      <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                        <p className="text-sm font-semibold text-slate-700">
                          Número de compras por mês
                        </p>

                        <div className="mt-4 h-72 w-full sm:h-80">
                          <ResponsiveContainer
                            width="100%"
                            height="100%"
                          >
                            <LineChart
                              data={
                                mensalGrafico
                              }
                              margin={{
                                top: 8,
                                right: 8,
                                bottom: 8,
                                left: 0,
                              }}
                            >
                              <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={
                                  false
                                }
                              />

                              <XAxis
                                dataKey="mes"
                                minTickGap={
                                  30
                                }
                                fontSize={
                                  10
                                }
                              />

                              <YAxis
                                width={
                                  48
                                }
                                tickFormatter={(
                                  valor,
                                ) =>
                                  formatarNumero(
                                    valor,
                                  )
                                }
                                fontSize={
                                  10
                                }
                              />

                              <Tooltip
                                formatter={(
                                  valor,
                                ) =>
                                  formatarNumero(
                                    valor,
                                  )
                                }
                              />

                              <Line
                                type="monotone"
                                dataKey="numero_compras"
                                stroke="var(--color-brand-blue)"
                                strokeWidth={
                                  2
                                }
                                dot={
                                  false
                                }
                                activeDot={{
                                  r: 4,
                                }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </article>
                    </div>
                  )}
                </section>


                <hr className="border-slate-200" />


                <section>
                  <div className="overflow-x-auto">
                    <div
                      className="inline-flex min-w-max rounded-xl border border-teal-100 bg-white p-1"
                      role="tablist"
                      aria-label="Análises de compras"
                    >
                      {[
                        {
                          id:
                            "fornecedores",
                          label:
                            "Fornecedores",
                        },
                        {
                          id:
                            "fabricantes",
                          label:
                            "Fabricantes",
                        },
                        {
                          id:
                            "modalidade",
                          label:
                            "Modalidade e tipo",
                        },
                        {
                          id:
                            "recentes",
                          label:
                            "Compras recentes",
                        },
                      ].map(
                        (item) => (
                          <button
                            key={
                              item.id
                            }
                            type="button"
                            role="tab"
                            aria-selected={
                              aba
                              === item.id
                            }
                            onClick={() =>
                              setAba(
                                item.id as AbaCompras,
                              )
                            }
                            className={[
                              "rounded-lg px-4 py-2 text-sm font-medium transition",
                              aba
                                === item.id
                                ? "bg-teal-700 text-white"
                                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                            ].join(
                              " ",
                            )}
                          >
                            {item.label}
                          </button>
                        ),
                      )}
                    </div>
                  </div>


                  {aba
                    === "fornecedores"
                    && (
                      <div className="mt-5">
                        <h2 className="mb-4 text-xl font-semibold tracking-tight text-slate-900">
                          Principais fornecedores
                        </h2>

                        {fornecedoresTabela.length
                          === 0 ? (
                          <Vazio>
                            Não há fornecedores para exibir.
                          </Vazio>
                        ) : (
                          <div className="space-y-5">
                            <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                              <GraficoRanking
                                dados={
                                  fornecedoresTabela.map(
                                    (
                                      item,
                                    ) => ({
                                      fornecedor:
                                        item.fornecedor,
                                      valor_total:
                                        numero(
                                          item.valor_total,
                                        ),
                                    }),
                                  )
                                }
                                nomeKey="fornecedor"
                              />
                            </article>

                            <article className="min-w-0 w-full">
                              <DataTable
                                data={
                                  fornecedoresTabela
                                }
                                columns={
                                  colunasFornecedores
                                }
                                pageSize={
                                  8
                                }
                              />
                            </article>
                          </div>
                        )}
                      </div>
                    )}


                  {aba
                    === "fabricantes"
                    && (
                      <div className="mt-5">
                        <h2 className="mb-4 text-xl font-semibold tracking-tight text-slate-900">
                          Principais fabricantes
                        </h2>

                        {fabricantesTabela.length
                          === 0 ? (
                          <Vazio>
                            Não há fabricantes para exibir.
                          </Vazio>
                        ) : (
                          <div className="space-y-5">
                            <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                              <GraficoRanking
                                dados={
                                  fabricantesTabela.map(
                                    (
                                      item,
                                    ) => ({
                                      fabricante:
                                        item.fabricante,
                                      valor_total:
                                        numero(
                                          item.valor_total,
                                        ),
                                    }),
                                  )
                                }
                                nomeKey="fabricante"
                              />
                            </article>

                            <article className="min-w-0 w-full">
                              <DataTable
                                data={
                                  fabricantesTabela
                                }
                                columns={
                                  colunasFabricantes
                                }
                                pageSize={
                                  8
                                }
                              />
                            </article>
                          </div>
                        )}
                      </div>
                    )}


                  {aba
                    === "modalidade"
                    && (
                      <div className="mt-5 grid grid-cols-1 gap-6 xl:grid-cols-2">
                        <article className="min-w-0 space-y-4">
                          <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                            Compras por modalidade
                          </h2>

                          {dados.modalidades.length
                            === 0 ? (
                            <Vazio>
                              Não há modalidades para exibir.
                            </Vazio>
                          ) : (
                            <>
                              <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                                <GraficoRanking
                                  dados={
                                    dados.modalidades.map(
                                      (
                                        item,
                                      ) => ({
                                        modalidade:
                                          item.modalidade,
                                        valor_total:
                                          numero(
                                            item.valor_total,
                                          ),
                                      }),
                                    )
                                  }
                                  nomeKey="modalidade"
                                />
                              </div>

                              <DataTable
                                data={
                                  dados.modalidades
                                }
                                columns={
                                  colunasModalidades
                                }
                                pageSize={
                                  8
                                }
                              />
                            </>
                          )}
                        </article>


                        <article className="min-w-0 space-y-4">
                          <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                            Compras por tipo
                          </h2>

                          {dados.tipos.length
                            === 0 ? (
                            <Vazio>
                              Não há tipos para exibir.
                            </Vazio>
                          ) : (
                            <>
                              <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                                <GraficoRanking
                                  dados={
                                    dados.tipos.map(
                                      (
                                        item,
                                      ) => ({
                                        tipo_compra:
                                          item.tipo_compra,
                                        valor_total:
                                          numero(
                                            item.valor_total,
                                          ),
                                      }),
                                    )
                                  }
                                  nomeKey="tipo_compra"
                                />
                              </div>

                              <DataTable
                                data={
                                  dados.tipos
                                }
                                columns={
                                  colunasTipos
                                }
                                pageSize={
                                  8
                                }
                              />
                            </>
                          )}
                        </article>
                      </div>
                    )}


                  {aba
                    === "recentes"
                    && (
                      <div className="mt-5">
                        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                          Compras mais recentes
                        </h2>

                        <p className="mt-1 mb-4 text-sm leading-6 text-slate-500">
                          São exibidos no máximo 500 registros, ordenados da compra mais recente para a mais antiga.
                        </p>

                        <DataTable
                          data={
                            dados.recentes
                          }
                          columns={
                            colunasRecentes
                          }
                          pageSize={
                            15
                          }
                          emptyMessage="Não há compras recentes para exibir."
                        />
                      </div>
                    )}
                </section>
              </>
            )}
          </section>
        )}
    </main>
  );
}
