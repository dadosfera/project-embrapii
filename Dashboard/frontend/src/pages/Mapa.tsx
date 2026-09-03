import {
  type FormEvent,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  ColumnDef,
} from "@tanstack/react-table";

import {
  DataTable,
} from "../components/DataTable";

import {
  MapaBrasilUf,
  type DadoMapaUf,
} from "../components/MapaBrasil";

import {
  buscarEstoquePorUf,
  buscarLeitosPorUf,
  buscarMedicamentos,
  type CatmatItem,
  type EstoqueUf,
  type LeitosPorUf,
  type ModoLeitos,
} from "../lib/api";


type AbaMapa =
  | "estoque"
  | "leitos";


type MetricaLeitos =
  | "leitos_gerais"
  | "leitos_sus"
  | "leitos_uti"
  | "leitos_uti_sus";


type LinhaEstoque = {
  uf: string;
  estoque_total: number;
  num_instituicoes: number;
};


type LinhaLeitos = {
  uf: string;
  leitos_gerais: number;
  leitos_sus: number;
  leitos_uti: number;
  leitos_uti_sus: number;
  instituicoes: number;
};


const TODAS_UFS = [
  "AC",
  "AL",
  "AP",
  "AM",
  "BA",
  "CE",
  "DF",
  "ES",
  "GO",
  "MA",
  "MT",
  "MS",
  "MG",
  "PA",
  "PB",
  "PR",
  "PE",
  "PI",
  "RJ",
  "RN",
  "RS",
  "RO",
  "RR",
  "SC",
  "SP",
  "SE",
  "TO",
];


const ROTULOS_METRICA:
  Record<
    MetricaLeitos,
    string
  > = {
    leitos_gerais:
      "Leitos gerais",

    leitos_sus:
      "Leitos SUS",

    leitos_uti:
      "Leitos de UTI",

    leitos_uti_sus:
      "Leitos de UTI SUS",
  };


const ROTULOS_MODO:
  Record<
    ModoLeitos,
    string
  > = {
    ultima_competencia:
      "Competência mais recente da base",

    ultima_instituicao:
      "Última posição de cada instituição",
  };


const formatadorNumero =
  new Intl.NumberFormat(
    "pt-BR",
    {
      maximumFractionDigits: 0,
    },
  );


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


function normalizarEstoque(
  dados: EstoqueUf[],
): LinhaEstoque[] {
  const porUf =
    new Map<
      string,
      LinhaEstoque
    >();

  dados.forEach(
    (item) => {
      if (!item.uf) {
        return;
      }

      const uf =
        item.uf
          .trim()
          .toUpperCase();

      porUf.set(
        uf,
        {
          uf,
          estoque_total:
            numero(
              item.estoque_total,
            ),
          num_instituicoes:
            numero(
              item.num_instituicoes,
            ),
        },
      );
    },
  );

  return TODAS_UFS.map(
    (uf) =>
      porUf.get(
        uf,
      )
      ?? {
        uf,
        estoque_total: 0,
        num_instituicoes: 0,
      },
  );
}


function normalizarLeitos(
  dados: LeitosPorUf[],
): LinhaLeitos[] {
  const porUf =
    new Map<
      string,
      LinhaLeitos
    >();

  dados.forEach(
    (item) => {
      if (!item.uf) {
        return;
      }

      const uf =
        item.uf
          .trim()
          .toUpperCase();

      if (
        !TODAS_UFS.includes(
          uf,
        )
      ) {
        return;
      }

      porUf.set(
        uf,
        {
          uf,
          leitos_gerais:
            numero(
              item.leitos_gerais,
            ),
          leitos_sus:
            numero(
              item.leitos_sus,
            ),
          leitos_uti:
            numero(
              item.leitos_uti,
            ),
          leitos_uti_sus:
            numero(
              item.leitos_uti_sus,
            ),
          instituicoes:
            numero(
              item.instituicoes,
            ),
        },
      );
    },
  );

  return TODAS_UFS.map(
    (uf) =>
      porUf.get(
        uf,
      )
      ?? {
        uf,
        leitos_gerais: 0,
        leitos_sus: 0,
        leitos_uti: 0,
        leitos_uti_sus: 0,
        instituicoes: 0,
      },
  );
}


export function Mapa() {
  const [
    aba,
    setAba,
  ] =
    useState<AbaMapa>(
      "estoque",
    );


  // =========================================
  // ESTOQUE
  // =========================================

  const [
    termoMedicamento,
    setTermoMedicamento,
  ] = useState("");

  const [
    buscandoCatmat,
    setBuscandoCatmat,
  ] = useState(false);

  const [
    opcoesCatmat,
    setOpcoesCatmat,
  ] =
    useState<
      CatmatItem[]
    >([]);

  const [
    catmatSelecionado,
    setCatmatSelecionado,
  ] = useState("");

  const [
    carregandoEstoque,
    setCarregandoEstoque,
  ] = useState(false);

  const [
    estoqueBruto,
    setEstoqueBruto,
  ] =
    useState<
      EstoqueUf[] | null
    >(null);

  const [
    catmatAplicado,
    setCatmatAplicado,
  ] =
    useState<
      CatmatItem | null
    >(null);

  const [
    erroEstoque,
    setErroEstoque,
  ] =
    useState<
      string | null
    >(null);


  // =========================================
  // LEITOS
  // =========================================

  const [
    modoLeitos,
    setModoLeitos,
  ] =
    useState<ModoLeitos>(
      "ultima_competencia",
    );

  const [
    modoLeitosAplicado,
    setModoLeitosAplicado,
  ] =
    useState<
      ModoLeitos | null
    >(null);

  const [
    metricaLeitos,
    setMetricaLeitos,
  ] =
    useState<MetricaLeitos>(
      "leitos_gerais",
    );

  const [
    carregandoLeitos,
    setCarregandoLeitos,
  ] = useState(false);

  const [
    leitosBruto,
    setLeitosBruto,
  ] =
    useState<
      LeitosPorUf[] | null
    >(null);

  const [
    erroLeitos,
    setErroLeitos,
  ] =
    useState<
      string | null
    >(null);


  // Cache de consultas enquanto a rota permanecer aberta.
  const cacheEstoque =
    useRef(
      new Map<
        number,
        EstoqueUf[]
      >(),
    );

  const cacheLeitos =
    useRef(
      new Map<
        ModoLeitos,
        LeitosPorUf[]
      >(),
    );


  const itemCatmatSelecionado =
    useMemo(
      () =>
        opcoesCatmat.find(
          (item) =>
            String(
              item.catmat_id,
            )
            === catmatSelecionado,
        )
        ?? null,
      [
        opcoesCatmat,
        catmatSelecionado,
      ],
    );


  async function localizarCatmat(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const termo =
      termoMedicamento.trim();

    if (!termo) {
      setErroEstoque(
        "Digite um medicamento para localizar itens no CATMAT.",
      );
      return;
    }

    setBuscandoCatmat(true);
    setErroEstoque(null);
    setOpcoesCatmat([]);
    setCatmatSelecionado("");

    try {
      const resposta =
        await buscarMedicamentos(
          termo,
        );

      setOpcoesCatmat(
        resposta,
      );

      if (
        resposta.length === 0
      ) {
        setErroEstoque(
          "Nenhum item do CATMAT foi encontrado para essa busca.",
        );
        return;
      }

      setCatmatSelecionado(
        String(
          resposta[0]
            .catmat_id,
        ),
      );
    } catch (error) {
      setErroEstoque(
        error
          instanceof Error
          ? error.message
          : "Não foi possível consultar o CATMAT.",
      );
    } finally {
      setBuscandoCatmat(false);
    }
  }


  async function buscarMapaEstoque() {
    if (!itemCatmatSelecionado) {
      setErroEstoque(
        "Selecione um item do CATMAT antes de buscar.",
      );
      return;
    }

    setCarregandoEstoque(
      true,
    );
    setErroEstoque(null);

    const catmatId =
      itemCatmatSelecionado
        .catmat_id;

    try {
      const armazenado =
        cacheEstoque
          .current
          .get(
            catmatId,
          );

      const resposta =
        armazenado
        ?? await buscarEstoquePorUf(
          catmatId,
        );

      if (!armazenado) {
        cacheEstoque
          .current
          .set(
            catmatId,
            resposta,
          );
      }

      setEstoqueBruto(
        resposta,
      );

      setCatmatAplicado(
        itemCatmatSelecionado,
      );
    } catch (error) {
      setErroEstoque(
        error
          instanceof Error
          ? error.message
          : "Não foi possível carregar o estoque por estado.",
      );
    } finally {
      setCarregandoEstoque(
        false,
      );
    }
  }


  async function buscarMapaLeitos() {
    setCarregandoLeitos(
      true,
    );
    setErroLeitos(null);

    try {
      const armazenado =
        cacheLeitos
          .current
          .get(
            modoLeitos,
          );

      const resposta =
        armazenado
        ?? await buscarLeitosPorUf({
          modo:
            modoLeitos,
          uf: "",
        });

      if (!armazenado) {
        cacheLeitos
          .current
          .set(
            modoLeitos,
            resposta,
          );
      }

      setLeitosBruto(
        resposta,
      );

      setModoLeitosAplicado(
        modoLeitos,
      );
    } catch (error) {
      setErroLeitos(
        error
          instanceof Error
          ? error.message
          : "Não foi possível carregar os leitos por estado.",
      );
    } finally {
      setCarregandoLeitos(
        false,
      );
    }
  }


  const estoqueNormalizado =
    useMemo(
      () =>
        estoqueBruto
          ? normalizarEstoque(
              estoqueBruto,
            )
          : [],
      [estoqueBruto],
    );


  const dadosMapaEstoque =
    useMemo<
      DadoMapaUf[]
    >(
      () =>
        estoqueNormalizado.map(
          (item) => ({
            uf:
              item.uf,
            valor:
              item.estoque_total,
          }),
        ),
      [estoqueNormalizado],
    );


  const estoqueTabela =
    useMemo(
      () =>
        [
          ...estoqueNormalizado,
        ].sort(
          (
            a,
            b,
          ) =>
            b.estoque_total
            - a.estoque_total,
        ),
      [estoqueNormalizado],
    );


  const leitosNormalizado =
    useMemo(
      () =>
        leitosBruto
          ? normalizarLeitos(
              leitosBruto,
            )
          : [],
      [leitosBruto],
    );


  const dadosMapaLeitos =
    useMemo<
      DadoMapaUf[]
    >(
      () =>
        leitosNormalizado.map(
          (item) => ({
            uf:
              item.uf,
            valor:
              item[
                metricaLeitos
              ],
          }),
        ),
      [
        leitosNormalizado,
        metricaLeitos,
      ],
    );


  const leitosTabela =
    useMemo(
      () =>
        [
          ...leitosNormalizado,
        ].sort(
          (
            a,
            b,
          ) =>
            b[
              metricaLeitos
            ]
            - a[
              metricaLeitos
            ],
        ),
      [
        leitosNormalizado,
        metricaLeitos,
      ],
    );


  const colunasEstoque =
    useMemo<
      ColumnDef<
        LinhaEstoque,
        unknown
      >[]
    >(
      () => [
        {
          header: "UF",
          accessorKey: "uf",
        },
        {
          header: "Estoque",
          accessorKey:
            "estoque_total",
          cell: ({
            row,
          }) =>
            formatadorNumero.format(
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
            formatadorNumero.format(
              row.original
                .num_instituicoes,
            ),
        },
      ],
      [],
    );


  const colunasLeitos =
    useMemo<
      ColumnDef<
        LinhaLeitos,
        unknown
      >[]
    >(
      () => [
        {
          header: "UF",
          accessorKey: "uf",
        },
        {
          header:
            "Leitos gerais",
          accessorKey:
            "leitos_gerais",
          cell: ({
            row,
          }) =>
            formatadorNumero.format(
              row.original
                .leitos_gerais,
            ),
        },
        {
          header:
            "Leitos SUS",
          accessorKey:
            "leitos_sus",
          cell: ({
            row,
          }) =>
            formatadorNumero.format(
              row.original
                .leitos_sus,
            ),
        },
        {
          header:
            "Leitos de UTI",
          accessorKey:
            "leitos_uti",
          cell: ({
            row,
          }) =>
            formatadorNumero.format(
              row.original
                .leitos_uti,
            ),
        },
        {
          header:
            "Leitos de UTI SUS",
          accessorKey:
            "leitos_uti_sus",
          cell: ({
            row,
          }) =>
            formatadorNumero.format(
              row.original
                .leitos_uti_sus,
            ),
        },
        {
          header:
            "Instituições",
          accessorKey:
            "instituicoes",
          cell: ({
            row,
          }) =>
            formatadorNumero.format(
              row.original
                .instituicoes,
            ),
        },
      ],
      [],
    );


  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-700">
          Visão geográfica
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Mapa do Brasil
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
          Explore diferentes indicadores de saúde por Unidade Federativa.
        </p>
      </header>


      <section className="mt-7">
        <div className="overflow-x-auto">
          <div
            className="inline-flex min-w-max rounded-xl border border-teal-100 bg-white p-1 shadow-sm"
            role="tablist"
            aria-label="Análises geográficas"
          >
            <button
              type="button"
              role="tab"
              aria-selected={
                aba === "estoque"
              }
              onClick={() =>
                setAba(
                  "estoque",
                )
              }
              className={[
                "rounded-lg px-4 py-2.5 text-sm font-medium transition",
                aba === "estoque"
                  ? "bg-teal-700 text-white"
                  : "text-slate-600 hover:bg-teal-50 hover:text-teal-800",
              ].join(
                " ",
              )}
            >
              Estoque por estado
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={
                aba === "leitos"
              }
              onClick={() =>
                setAba(
                  "leitos",
                )
              }
              className={[
                "rounded-lg px-4 py-2.5 text-sm font-medium transition",
                aba === "leitos"
                  ? "bg-teal-700 text-white"
                  : "text-slate-600 hover:bg-teal-50 hover:text-teal-800",
              ].join(
                " ",
              )}
            >
              Leitos por estado
            </button>
          </div>
        </div>
      </section>


      {aba === "estoque" && (
        <section className="mt-5">
          <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Estoque de medicamento por estado
              </h2>

              <p className="mt-1 text-sm leading-6 text-slate-500">
                Localize um item no CATMAT e carregue a distribuição de estoque das instituições.
              </p>
            </div>


            <form
              onSubmit={
                localizarCatmat
              }
              className="mt-5"
            >
              <label
                htmlFor="mapa-busca-catmat"
                className="block text-sm font-semibold text-slate-800"
              >
                Medicamento / CATMAT
              </label>

              <div className="mt-2 flex flex-col gap-3 sm:flex-row">
                <input
                  id="mapa-busca-catmat"
                  type="search"
                  value={
                    termoMedicamento
                  }
                  onChange={(
                    event,
                  ) =>
                    setTermoMedicamento(
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
                    buscandoCatmat
                    || !termoMedicamento
                      .trim()
                  }
                  className="min-h-12 rounded-xl border border-teal-200 bg-white px-5 py-3 text-sm font-semibold text-teal-800 transition hover:bg-teal-50 focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400 sm:min-w-36"
                >
                  {buscandoCatmat
                    ? "Localizando..."
                    : "Localizar itens"}
                </button>
              </div>
            </form>


            {opcoesCatmat.length
              > 0
              && (
                <div className="mt-5">
                  <label
                    htmlFor="mapa-catmat-selecionado"
                    className="block text-sm font-semibold text-slate-800"
                  >
                    Item
                  </label>

                  <select
                    id="mapa-catmat-selecionado"
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
                          {item
                            .descricao_catmat
                            ?? "Descrição não informada"}
                          {" — CATMAT "}
                          {item
                            .codigo_catmat
                            ?? "N/I"}
                        </option>
                      ),
                    )}
                  </select>


                  <button
                    type="button"
                    onClick={
                      buscarMapaEstoque
                    }
                    disabled={
                      carregandoEstoque
                      || !itemCatmatSelecionado
                    }
                    className="mx-auto mt-5 block min-h-12 w-full rounded-xl bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-teal-900/10 transition hover:-translate-y-0.5 hover:bg-teal-800 hover:shadow-lg focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none disabled:hover:translate-y-0 sm:w-1/2 lg:w-1/4"
                  >
                    {carregandoEstoque
                      ? "Carregando..."
                      : "Buscar"}
                  </button>
                </div>
              )}


            {erroEstoque && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800">
                {erroEstoque}
              </div>
            )}
          </div>


          {carregandoEstoque && (
            <div className="mt-5 h-[520px] animate-pulse rounded-2xl bg-teal-50" />
          )}


          {estoqueBruto
            && !carregandoEstoque
            && catmatAplicado
            && (
              estoqueBruto.length
              > 0 ? (
                <div className="mt-5 space-y-6">
                  <MapaBrasilUf
                    dados={
                      dadosMapaEstoque
                    }
                    titulo="Estoque por Unidade Federativa"
                    descricao={
                      `${
                        catmatAplicado
                          .descricao_catmat
                          ?? "Medicamento selecionado"
                      } — CATMAT ${
                        catmatAplicado
                          .codigo_catmat
                          ?? "N/I"
                      }`
                    }
                    tituloValor="Estoque"
                  />


                  <section>
                    <div className="mb-4">
                      <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                        Dados por Unidade Federativa
                      </h2>

                      <p className="mt-1 text-sm leading-6 text-slate-500">
                        A tabela e o mapa usam a mesma resposta da consulta. UFs sem registro são mantidas com valor zero.
                      </p>
                    </div>

                    <DataTable
                      data={
                        estoqueTabela
                      }
                      columns={
                        colunasEstoque
                      }
                      pageSize={
                        27
                      }
                    />
                  </section>
                </div>
              ) : (
                <div className="mt-5 rounded-xl border border-teal-200 bg-teal-50 px-4 py-4 text-sm leading-6 text-teal-900">
                  Não há dados de estoque para o item selecionado.
                </div>
              )
            )}
        </section>
      )}


      {aba === "leitos" && (
        <section className="mt-5">
          <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Disponibilidade de leitos por estado
              </h2>

              <p className="mt-1 text-sm leading-6 text-slate-500">
                Escolha a base utilizada. A métrica pode ser alterada depois sem realizar uma nova consulta.
              </p>
            </div>


            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="mapa-modo-leitos"
                  className="block text-sm font-semibold text-slate-800"
                >
                  Base utilizada
                </label>

                <select
                  id="mapa-modo-leitos"
                  value={
                    modoLeitos
                  }
                  onChange={(
                    event,
                  ) =>
                    setModoLeitos(
                      event.target.value as ModoLeitos,)
                  
                  }
                  className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
                >
                  <option value="ultima_competencia">
                    Competência mais recente da base
                  </option>

                  <option value="ultima_instituicao">
                    Última posição de cada instituição
                  </option>
                </select>
              </div>


              <div>
                <label
                  htmlFor="mapa-metrica-leitos"
                  className="block text-sm font-semibold text-slate-800"
                >
                  Métrica exibida no mapa
                </label>

                <select
                  id="mapa-metrica-leitos"
                  value={
                    metricaLeitos
                  }
                  onChange={(
                    event,
                  ) =>
                    setMetricaLeitos(
                      event.target.value as MetricaLeitos,
  
                        
                    )
                  }
                  className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
                >
                  <option value="leitos_gerais">
                    Leitos gerais
                  </option>

                  <option value="leitos_sus">
                    Leitos SUS
                  </option>

                  <option value="leitos_uti">
                    Leitos de UTI
                  </option>

                  <option value="leitos_uti_sus">
                    Leitos de UTI SUS
                  </option>
                </select>
              </div>
            </div>


            <button
              type="button"
              onClick={
                buscarMapaLeitos
              }
              disabled={
                carregandoLeitos
              }
              className="mx-auto mt-5 block min-h-12 w-full rounded-xl bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-teal-900/10 transition hover:-translate-y-0.5 hover:bg-teal-800 hover:shadow-lg focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none disabled:hover:translate-y-0 sm:w-1/2 lg:w-1/4"
            >
              {carregandoLeitos
                ? "Carregando..."
                : "Buscar"}
            </button>


            {erroLeitos && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800">
                {erroLeitos}
              </div>
            )}
          </div>


          {carregandoLeitos && (
            <div className="mt-5 h-[520px] animate-pulse rounded-2xl bg-teal-50" />
          )}


          {leitosBruto
            && !carregandoLeitos
            && modoLeitosAplicado
            && (
              leitosBruto.length
              > 0 ? (
                <div className="mt-5 space-y-6">
                  <MapaBrasilUf
                    dados={
                      dadosMapaLeitos
                    }
                    titulo={
                      ROTULOS_METRICA[
                        metricaLeitos
                      ]
                    }
                    descricao={
                      ROTULOS_MODO[
                        modoLeitosAplicado
                      ]
                    }
                    tituloValor={
                      ROTULOS_METRICA[
                        metricaLeitos
                      ]
                    }
                  />


                  <section>
                    <div className="mb-4">
                      <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                        Dados por Unidade Federativa
                      </h2>

                      <p className="mt-1 text-sm leading-6 text-slate-500">
                        Alterar apenas a métrica recolore o mapa e reordena esta tabela localmente, sem nova consulta ao banco.
                      </p>
                    </div>

                    <DataTable
                      data={
                        leitosTabela
                      }
                      columns={
                        colunasLeitos
                      }
                      pageSize={
                        27
                      }
                    />
                  </section>
                </div>
              ) : (
                <div className="mt-5 rounded-xl border border-teal-200 bg-teal-50 px-4 py-4 text-sm leading-6 text-teal-900">
                  Não há dados de leitos para exibir.
                </div>
              )
            )}
        </section>
      )}
    </main>
  );
}
