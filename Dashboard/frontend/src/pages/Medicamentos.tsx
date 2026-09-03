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


function numero(valor: unknown) {
  const convertido =
    Number(valor);

  return Number.isFinite(
    convertido,
  )
    ? convertido
    : 0;
}


const numeroInteiro =
  new Intl.NumberFormat(
    "pt-BR",
    {
      maximumFractionDigits: 0,
    },
  );


const moeda =
  new Intl.NumberFormat(
    "pt-BR",
    {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  );


function formatarNumero(
  valor: unknown,
) {
  return numeroInteiro.format(
    numero(valor),
  );
}


function formatarMoeda(
  valor: unknown,
) {
  if (
    valor === null
    || valor === undefined
    || valor === ""
  ) {
    return "—";
  }

  return moeda.format(
    numero(valor),
  );
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


function MensagemVazia({
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


function GraficoBarrasHorizontal({
  data,
  nomeKey,
  valorKey,
}: {
  data: Record<
    string,
    string | number
  >[];
  nomeKey: string;
  valorKey: string;
}) {
  if (data.length === 0) {
    return (
      <MensagemVazia>
        Não há dados para exibir.
      </MensagemVazia>
    );
  }

  const altura =
    Math.max(
      280,
      data.length * 40,
    );

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
            strokeDasharray="3 3"
            horizontal={false}
          />

          <XAxis
            type="number"
            tickFormatter={(
              value,
            ) =>
              formatarMoeda(
                value,
              )
            }
            fontSize={10}
          />

          <YAxis
            type="category"
            dataKey={nomeKey}
            width={115}
            tickFormatter={(
              value,
            ) =>
              truncar(
                value,
                20,
              )
            }
            tickLine={false}
            fontSize={10}
          />

          <Tooltip
            formatter={(
              value,
            ) =>
              formatarMoeda(
                value,
              )
            }
            labelFormatter={(
              value,
            ) =>
              String(value)
            }
          />

          <Bar
            dataKey={valorKey}
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
        throw new Error(
          "Esse item do CATMAT não tem produto vinculado na base.",
        );
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

      setErroDados(
        error
          instanceof Error
          ? error.message
          : "Não foi possível carregar os dados do medicamento.",
      );
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
              formatarData(
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
        },
        {
          header:
            "Quantidade",
          accessorKey:
            "quantidade_do_item_em_estoque",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .quantidade_do_item_em_estoque,
            ),
        },
        {
          header:
            "Validade",
          accessorKey:
            "data_de_validade",
          cell: ({
            row,
          }) =>
            formatarData(
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
            formatarNumero(
              row.original
                .estoque_total,
            ),
        },
        {
          header:
            "Instituições",
          accessorKey:
            "num_instituicoes",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .num_instituicoes,
            ),
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
            formatarData(
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
          💊 Medicamentos
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
          Consulte estoque atual, lotes próximos do vencimento,
          distribuição geográfica e histórico de compras por
          medicamento CATMAT.
        </p>
      </header>


      <section className="mt-7">
        <form
          onSubmit={
            handleBuscar
          }
          className="space-y-3"
        >
          <label
            htmlFor="busca-medicamento"
            className="block text-sm font-semibold text-slate-800"
          >
            Buscar medicamento (CATMAT)
          </label>

          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="busca-medicamento"
              value={busca}
              onChange={(
                event,
              ) =>
                alterarBusca(
                  event.target
                    .value,
                )
              }
              placeholder="ex: dipirona, insulina, seringa..."
              className="h-12 min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
            />

            <button
              type="submit"
              disabled={
                buscando
              }
              className="h-12 w-full rounded-xl bg-teal-700 px-6 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
            >
              {buscando
                ? "Buscando..."
                : "Buscar"}
            </button>
          </div>
        </form>


        {!busca.trim()
          && !erroBusca
          && (
            <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-800">
              Digite algo acima para buscar um medicamento no catálogo CATMAT.
            </div>
          )}


        {erroBusca && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
            {erroBusca}
          </div>
        )}


        {resultados.length
          > 0
          && (
            <div className="mt-5 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
              <label
                htmlFor="catmat"
                className="block text-sm font-semibold text-slate-800"
              >
                Selecione o item
              </label>

              <select
                id="catmat"
                value={
                  selecionado
                }
                onChange={(
                  event,
                ) =>
                  setSelecionado(
                    event.target
                      .value,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50 sm:px-4"
              >
                <option value="">
                  — Selecione um medicamento —
                </option>

                {resultados.map(
                  (item) => (
                    <option
                      key={
                        item.catmat_id
                      }
                      value={
                        item.catmat_id
                      }
                    >
                      {rotuloMedicamento(
                        item,
                      )}
                    </option>
                  ),
                )}
              </select>

              <button
                type="button"
                onClick={
                  carregarDados
                }
                disabled={
                  !itemSelecionado
                  || carregando
                }
                className="mx-auto mt-4 block min-h-12 w-full rounded-xl bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-1/2 lg:w-1/4"
              >
                {carregando
                  ? "Carregando dados..."
                  : "Pesquisar"}
              </button>
            </div>
          )}
      </section>


      {erroDados && (
        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800">
          {erroDados}
        </div>
      )}


      {carregando && (
        <section className="mt-7 space-y-4">
          <div className="h-8 w-72 max-w-full animate-pulse rounded bg-slate-200" />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              1,
              2,
              3,
              4,
            ].map(
              (item) => (
                <div
                  key={item}
                  className="h-28 animate-pulse rounded-2xl bg-slate-200"
                />
              ),
            )}
          </div>

          <div className="h-72 animate-pulse rounded-2xl bg-slate-200" />
        </section>
      )}


      {dados
        && medicamentoCarregado
        && !carregando
        && (
          <section className="mt-7 space-y-8">
            <div>
              <p className="text-sm leading-6 text-slate-500">
                Código CATMAT selecionado —{" "}
                <strong className="font-semibold text-slate-700">
                  {dados.produtos.length} produto(s)
                </strong>{" "}
                vinculado(s) a este item
              </p>

              <p className="mt-1 text-sm font-medium text-slate-800">
                {rotuloMedicamento(
                  medicamentoCarregado,
                )}
              </p>

              {buscaConfirmada && (
                <p className="mt-1 text-xs text-slate-400">
                  Busca confirmada: “{buscaConfirmada}”
                </p>
              )}
            </div>


            <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4">
              <Kpi
                titulo="Estoque total (última posição)"
                valor={
                  formatarNumero(
                    dados.resumo
                      .estoque_total,
                  )
                }
              />

              <Kpi
                titulo="Instituições com registro"
                valor={
                  formatarNumero(
                    dados.resumo
                      .instituicoes_com_registro,
                  )
                }
              />

              <Kpi
                titulo="Instituições com estoque zerado"
                valor={
                  formatarNumero(
                    dados.resumo
                      .instituicoes_estoque_zerado,
                  )
                }
              />

              <Kpi
                titulo="Preço médio de compra"
                valor={
                  formatarMoeda(
                    dados.resumo
                      .preco_medio_compra,
                  )
                }
              />
            </section>


            <hr className="border-slate-200" />


            <section>
              {dados.lotes
                .quantidade_lotes
                > 0 ? (
                <div className="rounded-2xl border border-amber-200 bg-amber-50">
                  <div className="px-4 py-4 text-sm font-medium leading-6 text-amber-900 sm:px-5">
                    ⚠️{" "}
                    {
                      dados.lotes
                        .quantidade_lotes
                    }{" "}
                    lote(s) com validade nos próximos 90 dias e estoque &gt; 0
                  </div>

                  <details className="border-t border-amber-200">
                    <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-amber-900 sm:px-5">
                      Ver lotes vencendo
                    </summary>

                    <div className="bg-white p-3 sm:p-5">
                      <DataTable
                        data={
                          dados.lotes
                            .items
                        }
                        columns={
                          colunasLotes
                        }
                        pageSize={
                          10
                        }
                      />
                    </div>
                  </details>
                </div>
              ) : (
                <div className="rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm leading-6 text-teal-800">
                  Nenhum lote com estoque positivo vence nos próximos 90 dias.
                </div>
              )}
            </section>


            <section>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                Estoque por UF
              </h2>

              {dados.estoqueUf.length
                > 0 ? (
                <div className="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-[2fr_1fr]">
                  <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                    <div className="h-80 w-full sm:h-96">
                      <ResponsiveContainer
                        width="100%"
                        height="100%"
                      >
                        <BarChart
                          data={
                            estoqueUfGrafico
                          }
                          margin={{
                            top: 12,
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
                            dataKey="uf"
                            fontSize={
                              11
                            }
                          />

                          <YAxis
                            width={
                              56
                            }
                            tickFormatter={(
                              value,
                            ) =>
                              formatarNumero(
                                value,
                              )
                            }
                            fontSize={
                              10
                            }
                          />

                          <Tooltip
                            formatter={(
                              value,
                            ) =>
                              formatarNumero(
                                value,
                              )
                            }
                          />

                          <Bar
                            dataKey="estoque_total"
                            fill="var(--color-brand-blue)"
                            radius={[
                              5,
                              5,
                              0,
                              0,
                            ]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </article>

                  <article className="min-w-0">
                    <DataTable
                      data={
                        dados.estoqueUf
                      }
                      columns={
                        colunasUf
                      }
                      pageSize={
                        10
                      }
                    />
                  </article>
                </div>
              ) : (
                <div className="mt-4">
                  <MensagemVazia>
                    Sem dados de estoque para esse item.
                  </MensagemVazia>
                </div>
              )}
            </section>


            <hr className="border-slate-200" />


            <section>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                Histórico de compras
              </h2>

              {dados.compras.length
                === 0 ? (
                <div className="mt-4">
                  <MensagemVazia>
                    Nenhuma compra registrada para esse item.
                  </MensagemVazia>
                </div>
              ) : (
                <>
                  <div className="mt-4 overflow-x-auto">
                    <div
                      className="inline-flex min-w-max rounded-xl border border-teal-100 bg-white p-1"
                      role="tablist"
                      aria-label="Histórico de compras"
                    >
                      <button
                        type="button"
                        role="tab"
                        aria-selected={
                          abaCompras
                          === "preco"
                        }
                        onClick={() =>
                          setAbaCompras(
                            "preco",
                          )
                        }
                        className={[
                          "rounded-lg px-4 py-2 text-sm font-medium transition",
                          abaCompras
                            === "preco"
                            ? "bg-teal-700 text-white"
                            : "text-slate-600 hover:bg-teal-50 hover:text-slate-900",
                        ].join(
                          " ",
                        )}
                      >
                        Evolução de preço
                      </button>

                      <button
                        type="button"
                        role="tab"
                        aria-selected={
                          abaCompras
                          === "fornecedores"
                        }
                        onClick={() =>
                          setAbaCompras(
                            "fornecedores",
                          )
                        }
                        className={[
                          "rounded-lg px-4 py-2 text-sm font-medium transition",
                          abaCompras
                            === "fornecedores"
                            ? "bg-teal-700 text-white"
                            : "text-slate-600 hover:bg-teal-50 hover:text-slate-900",
                        ].join(
                          " ",
                        )}
                      >
                        Fornecedores
                      </button>

                      <button
                        type="button"
                        role="tab"
                        aria-selected={
                          abaCompras
                          === "dados"
                        }
                        onClick={() =>
                          setAbaCompras(
                            "dados",
                          )
                        }
                        className={[
                          "rounded-lg px-4 py-2 text-sm font-medium transition",
                          abaCompras
                            === "dados"
                            ? "bg-teal-700 text-white"
                            : "text-slate-600 hover:bg-teal-50 hover:text-slate-900",
                        ].join(
                          " ",
                        )}
                      >
                        Dados brutos
                      </button>
                    </div>
                  </div>


                  {abaCompras
                    === "preco"
                    && (
                      <article className="mt-5 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                        {evolucaoPrecoGrafico.length
                          > 0 ? (
                          <div className="h-72 w-full sm:h-96">
                            <ResponsiveContainer
                              width="100%"
                              height="100%"
                            >
                              <LineChart
                                data={
                                  evolucaoPrecoGrafico
                                }
                                margin={{
                                  top: 12,
                                  right: 12,
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
                                  dataKey="data"
                                  minTickGap={
                                    32
                                  }
                                  fontSize={
                                    10
                                  }
                                />

                                <YAxis
                                  width={
                                    72
                                  }
                                  tickFormatter={(
                                    value,
                                  ) =>
                                    formatarMoeda(
                                      value,
                                    )
                                  }
                                  fontSize={
                                    10
                                  }
                                />

                                <Tooltip
                                  formatter={(
                                    value,
                                  ) =>
                                    formatarMoeda(
                                      value,
                                    )
                                  }
                                />

                                <Line
                                  type="monotone"
                                  dataKey="preco"
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
                        ) : (
                          <MensagemVazia>
                            Não há preços válidos para construir a evolução.
                          </MensagemVazia>
                        )}
                      </article>
                    )}


                  {abaCompras
                    === "fornecedores"
                    && (
                      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
                        <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                          <p className="mb-4 text-sm font-semibold text-slate-700">
                            Gasto total por fornecedor
                          </p>

                          <GraficoBarrasHorizontal
                            data={
                              fornecedoresGrafico
                            }
                            nomeKey="nome"
                            valorKey="valor"
                          />
                        </article>

                        <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                          <p className="mb-4 text-sm font-semibold text-slate-700">
                            Gasto total por fabricante
                          </p>

                          <GraficoBarrasHorizontal
                            data={
                              fabricantesGrafico
                            }
                            nomeKey="nome"
                            valorKey="valor"
                          />
                        </article>
                      </div>
                    )}


                  {abaCompras
                    === "dados"
                    && (
                      <div className="mt-5">
                        <DataTable
                          data={
                            dados.compras
                          }
                          columns={
                            colunasCompras
                          }
                          pageSize={
                            15
                          }
                        />
                      </div>
                    )}
                </>
              )}
            </section>
          </section>
        )}
    </main>
  );
}
