import {
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import type { ColumnDef } from "@tanstack/react-table";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DataTable } from "../components/DataTable";

import {
  buscarOpcoesLeitos,
  buscarPainelLeitos,
  type EvolucaoLeitos,
  type FiltrosLeitos,
  type InstituicaoLeitos,
  type IntervaloLeitos,
  type KpisLeitos,
  type LeitosPorUf,
  type ModoLeitos,
  type TipoUti,
} from "../lib/api";


type AbaLeitos =
  | "uf"
  | "uti"
  | "evolucao"
  | "instituicoes";


type DadosLeitos = {
  kpis: KpisLeitos;
  porUf: LeitosPorUf[];
  tiposUti: TipoUti[];
  evolucao: EvolucaoLeitos[];
  instituicoes: InstituicaoLeitos[];
};


type FiltrosConfirmados = {
  modo: ModoLeitos;
  modoDescricao: string;
  uf: string;
  ufDescricao: string;
  dataInicio: string;
  dataFim: string;
};


const KPIS_VAZIOS: KpisLeitos = {
  leitos_gerais: 0,
  leitos_sus: 0,
  leitos_uti: 0,
  leitos_uti_sus: 0,
  instituicoes_com_registro: 0,
  competencia_minima: null,
  competencia_maxima: null,
};


function numero(valor: unknown) {
  const convertido = Number(valor);

  return Number.isFinite(convertido)
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

  const [
    ano,
    mes,
    dia,
  ] = valor
    .slice(0, 10)
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


function dataIso(
  data: Date,
) {
  const ano =
    data.getFullYear();

  const mes =
    String(
      data.getMonth() + 1,
    ).padStart(
      2,
      "0",
    );

  const dia =
    String(
      data.getDate(),
    ).padStart(
      2,
      "0",
    );

  return `${ano}-${mes}-${dia}`;
}


function subtrairDias(
  iso: string,
  dias: number,
) {
  const [
    ano,
    mes,
    dia,
  ] = iso
    .slice(0, 10)
    .split("-")
    .map(Number);

  const data =
    new Date(
      ano,
      mes - 1,
      dia,
    );

  data.setDate(
    data.getDate() - dias,
  );

  return dataIso(data);
}


function formatarCompetencia(
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


function Kpi({
  titulo,
  valor,
  descricao,
}: {
  titulo: string;
  valor: string;
  descricao?: string;
}) {
  return (
    <article className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
      <p className="text-sm leading-5 text-slate-500">
        {titulo}
      </p>

      <p className="mt-3 break-words text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
        {valor}
      </p>

      {descricao && (
        <p className="mt-2 text-xs leading-5 text-slate-400">
          {descricao}
        </p>
      )}
    </article>
  );
}


function Vazio({
  children,
}: {
  children: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-teal-200 bg-teal-50/40 px-4 py-9 text-center text-sm leading-6 text-slate-500">
      {children}
    </div>
  );
}


function truncar(
  valor: unknown,
  limite = 28,
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


export function Leitos() {
  const [
    intervalo,
    setIntervalo,
  ] =
    useState<
      IntervaloLeitos | null
    >(null);

  const [
    ufs,
    setUfs,
  ] = useState<string[]>([]);

  const [
    carregandoOpcoes,
    setCarregandoOpcoes,
  ] = useState(true);

  const [
    modo,
    setModo,
  ] =
    useState<ModoLeitos>(
      "ultima_competencia",
    );

  const [
    uf,
    setUf,
  ] = useState("");

  const [
    dataInicio,
    setDataInicio,
  ] = useState("");

  const [
    dataFim,
    setDataFim,
  ] = useState("");

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
    avisos,
    setAvisos,
  ] =
    useState<
      string[]
    >([]);

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
      DadosLeitos | null
    >(null);

  const [
    aba,
    setAba,
  ] =
    useState<AbaLeitos>(
      "uf",
    );


  useEffect(
    () => {
      let ativo = true;

      async function carregarOpcoes() {
        setCarregandoOpcoes(
          true,
        );

        try {
          const resposta =
            await buscarOpcoesLeitos();

          if (!ativo) {
            return;
          }

          setIntervalo({
            data_minima:
              resposta.data_minima,
            data_maxima:
              resposta.data_maxima,
          });

          setUfs(
            resposta.ufs
              .filter(Boolean),
          );

          if (
            resposta.data_minima
            && resposta.data_maxima
          ) {
            const inicioCandidato =
              subtrairDias(
                resposta.data_maxima,
                730,
              );

            setDataInicio(
              inicioCandidato
              < resposta.data_minima
                ? resposta.data_minima
                : inicioCandidato,
            );

            setDataFim(
              resposta.data_maxima,
            );
          }
        } catch (error) {
          if (!ativo) {
            return;
          }

          setErro(
            error
              instanceof Error
              ? error.message
              : "Não foi possível carregar as opções de leitos.",
          );
        } finally {
          if (ativo) {
            setCarregandoOpcoes(
              false,
            );
          }
        }
      }

      void carregarOpcoes();

      return () => {
        ativo = false;
      };
    },
    [],
  );


  async function aplicarFiltros(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setErro(null);
    setAvisos([]);

    if (
      !dataInicio
      || !dataFim
    ) {
      setErro(
        "Informe o início e o final da evolução histórica.",
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

    setCarregando(true);
    setAba("uf");

    const filtros:
      FiltrosLeitos = {
        modo,
        uf,
      };

    try {
      const resposta =
        await buscarPainelLeitos(
          filtros,
          dataInicio,
          dataFim,
        );

      setDados({
        kpis:
          resposta.kpis,
        porUf:
          resposta.por_uf,
        tiposUti:
          resposta.tipos_uti,
        evolucao:
          resposta.evolucao,
        instituicoes:
          resposta.instituicoes,
      });

      setAvisos([]);

      setFiltrosConfirmados({
        modo,
        modoDescricao:
          modo
          === "ultima_competencia"
            ? "Competência mais recente da base"
            : "Última posição de cada instituição",
        uf,
        ufDescricao:
          uf || "Todas",
        dataInicio,
        dataFim,
      });
    } catch (error) {
      setErro(
        error
          instanceof Error
          ? error.message
          : "Não foi possível carregar as análises de leitos.",
      );
    } finally {
      setCarregando(false);
    }
  }


  const percentualSus =
    dados
    && numero(
      dados.kpis
        .leitos_gerais,
    ) > 0
      ? (
          numero(
            dados.kpis
              .leitos_sus,
          )
          / numero(
            dados.kpis
              .leitos_gerais,
          )
        ) * 100
      : 0;


  const porUfTabela =
    useMemo(
      () =>
        (
          dados?.porUf
          ?? []
        ).map(
          (item) => {
            const gerais =
              numero(
                item.leitos_gerais,
              );

            const sus =
              numero(
                item.leitos_sus,
              );

            const uti =
              numero(
                item.leitos_uti,
              );

            const utiSus =
              numero(
                item.leitos_uti_sus,
              );

            return {
              ...item,
              percentual_sus:
                gerais > 0
                  ? (
                      sus
                      / gerais
                    ) * 100
                  : 0,
              percentual_uti_sus:
                uti > 0
                  ? (
                      utiSus
                      / uti
                    ) * 100
                  : 0,
            };
          },
        ),
      [dados],
    );


  const tiposTabela =
    useMemo(
      () =>
        (
          dados?.tiposUti
          ?? []
        ).map(
          (item) => {
            const total =
              numero(
                item.total,
              );

            const sus =
              numero(
                item.sus,
              );

            return {
              ...item,
              percentual_sus:
                total > 0
                  ? (
                      sus
                      / total
                    ) * 100
                  : 0,
            };
          },
        ),
      [dados],
    );


  const evolucaoGrafico =
    useMemo(
      () =>
        (
          dados?.evolucao
          ?? []
        ).map(
          (item) => ({
            ...item,
            competencia_rotulo:
              formatarCompetencia(
                item.competencia,
              ),
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
          }),
        ),
      [dados],
    );


  const rankingGrafico =
    useMemo(
      () =>
        (
          dados?.instituicoes
          ?? []
        )
          .slice(
            0,
            20,
          )
          .map(
            (item) => ({
              instituicao:
                item.instituicao,
              leitos_gerais:
                numero(
                  item.leitos_gerais,
                ),
            }),
          ),
      [dados],
    );


  const colunasUf =
    useMemo<
      ColumnDef<
        LeitosPorUf
        & {
          percentual_sus:
            number;
          percentual_uti_sus:
            number;
        },
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
            formatarNumero(
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
            formatarNumero(
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
            formatarNumero(
              row.original
                .leitos_uti,
            ),
        },
        {
          header: "UTI SUS",
          accessorKey:
            "leitos_uti_sus",
          cell: ({
            row,
          }) =>
            formatarNumero(
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
            formatarNumero(
              row.original
                .instituicoes,
            ),
        },
        {
          header:
            "Leitos SUS (%)",
          accessorKey:
            "percentual_sus",
          cell: ({
            row,
          }) =>
            formatarPercentual(
              row.original
                .percentual_sus,
            ),
        },
        {
          header:
            "UTI SUS (%)",
          accessorKey:
            "percentual_uti_sus",
          cell: ({
            row,
          }) =>
            formatarPercentual(
              row.original
                .percentual_uti_sus,
            ),
        },
      ],
      [],
    );


  const colunasTipos =
    useMemo<
      ColumnDef<
        TipoUti
        & {
          percentual_sus:
            number;
        },
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Tipo de UTI",
          accessorKey:
            "tipo_uti",
        },
        {
          header: "Total",
          accessorKey: "total",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original.total,
            ),
        },
        {
          header: "SUS",
          accessorKey: "sus",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original.sus,
            ),
        },
        {
          header: "SUS (%)",
          accessorKey:
            "percentual_sus",
          cell: ({
            row,
          }) =>
            formatarPercentual(
              row.original
                .percentual_sus,
            ),
        },
      ],
      [],
    );


  const colunasEvolucao =
    useMemo<
      ColumnDef<
        EvolucaoLeitos,
        unknown
      >[]
    >(
      () => [
        {
          header:
            "Competência",
          accessorKey:
            "competencia",
          cell: ({
            row,
          }) =>
            formatarData(
              row.original
                .competencia,
            ),
        },
        {
          header:
            "Leitos gerais",
          accessorKey:
            "leitos_gerais",
          cell: ({
            row,
          }) =>
            formatarNumero(
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
            formatarNumero(
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
            formatarNumero(
              row.original
                .leitos_uti,
            ),
        },
        {
          header: "UTI SUS",
          accessorKey:
            "leitos_uti_sus",
          cell: ({
            row,
          }) =>
            formatarNumero(
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
            formatarNumero(
              row.original
                .instituicoes,
            ),
        },
      ],
      [],
    );


  const colunasInstituicoes =
    useMemo<
      ColumnDef<
        InstituicaoLeitos,
        unknown
      >[]
    >(
      () => [
        {
          header: "ID",
          accessorKey:
            "instituicao_id",
        },
        {
          header:
            "Instituição",
          accessorKey:
            "instituicao",
        },
        {
          header:
            "Município",
          accessorKey:
            "municipio",
        },
        {
          header: "UF",
          accessorKey: "uf",
        },
        {
          header:
            "Competência",
          accessorKey:
            "competencia",
          cell: ({
            row,
          }) =>
            formatarData(
              row.original
                .competencia,
            ),
        },
        {
          header:
            "Leitos gerais",
          accessorKey:
            "leitos_gerais",
          cell: ({
            row,
          }) =>
            formatarNumero(
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
            formatarNumero(
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
            formatarNumero(
              row.original
                .leitos_uti,
            ),
        },
        {
          header: "UTI SUS",
          accessorKey:
            "leitos_uti_sus",
          cell: ({
            row,
          }) =>
            formatarNumero(
              row.original
                .leitos_uti_sus,
            ),
        },
      ],
      [],
    );


  const abas: {
    id: AbaLeitos;
    label: string;
  }[] = [
    {
      id: "uf",
      label:
        "Distribuição por UF",
    },
    {
      id: "uti",
      label:
        "Tipos de UTI",
    },
    {
      id: "evolucao",
      label:
        "Evolução histórica",
    },
    {
      id: "instituicoes",
      label:
        "Instituições",
    },
  ];


  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-700">
          Capacidade hospitalar
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          🛏️ Leitos
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
          Analise a capacidade de leitos hospitalares,
          a participação do SUS e os diferentes tipos de UTI.
        </p>
      </header>


      <section className="mt-7 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-6">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Filtros
          </h2>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            O período é aplicado somente à evolução histórica.
          </p>

          {carregandoOpcoes && (
            <p className="mt-2 text-xs font-medium text-teal-700">
              Carregando intervalo e unidades federativas...
            </p>
          )}
        </div>


        <form
          onSubmit={
            aplicarFiltros
          }
          className="mt-5"
        >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="modo-leitos"
                  className="block text-sm font-semibold text-slate-800"
                >
                  Base utilizada nos indicadores
                </label>

                <select
                  id="modo-leitos"
                  value={modo}
                  onChange={(
                    event,
                  ) => {
                    const valor =
                      event.target.value;

                    if (
                      valor
                      === "ultima_competencia"
                      || valor
                      === "ultima_instituicao"
                    ) {
                      setModo(valor);
                    }
                  }}
                  className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
                >
                  <option value="ultima_competencia">
                    Competência mais recente da base
                  </option>

                  <option value="ultima_instituicao">
                    Última posição de cada instituição
                  </option>
                </select>

                <p className="mt-2 text-xs leading-5 text-slate-400">
                  A competência mais recente compara instituições no mesmo período; a última posição aumenta a cobertura, mas pode combinar competências distintas.
                </p>
              </div>


              <div>
                <label
                  htmlFor="uf-leitos"
                  className="block text-sm font-semibold text-slate-800"
                >
                  Unidade Federativa
                </label>

                <select
                  id="uf-leitos"
                  value={uf}
                  disabled={
                    carregandoOpcoes
                  }
                  onChange={(
                    event,
                  ) =>
                    setUf(
                      event.target
                        .value,
                    )
                  }
                  className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-50"
                >
                  <option value="">
                    {carregandoOpcoes
                      ? "Carregando UFs..."
                      : "Todas"}
                  </option>

                  {ufs.map(
                    (item) => (
                      <option
                        key={item}
                        value={item}
                      >
                        {item}
                      </option>
                    ),
                  )}
                </select>
              </div>


              <div>
                <label
                  htmlFor="inicio-evolucao"
                  className="block text-sm font-semibold text-slate-800"
                >
                  Início da evolução
                </label>

                <input
                  id="inicio-evolucao"
                  type="date"
                  disabled={
                    carregandoOpcoes
                    || !intervalo
                  }
                  value={
                    dataInicio
                  }
                  min={
                    intervalo
                      ?.data_minima
                    ?? undefined
                  }
                  max={
                    intervalo
                      ?.data_maxima
                    ?? undefined
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
                  htmlFor="fim-evolucao"
                  className="block text-sm font-semibold text-slate-800"
                >
                  Final da evolução
                </label>

                <input
                  id="fim-evolucao"
                  type="date"
                  disabled={
                    carregandoOpcoes
                    || !intervalo
                  }
                  value={
                    dataFim
                  }
                  min={
                    intervalo
                      ?.data_minima
                    ?? undefined
                  }
                  max={
                    intervalo
                      ?.data_maxima
                    ?? undefined
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
            </div>


            <button
              type="submit"
              disabled={
                carregando
                || !dataInicio
                || !dataFim
              }
              className="mx-auto mt-6 block min-h-12 w-full rounded-xl bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-teal-900/10 transition hover:-translate-y-0.5 hover:bg-teal-800 hover:shadow-lg focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none disabled:hover:translate-y-0 sm:w-1/2 lg:w-1/4"
            >
              {carregando
                ? "Carregando análises..."
                : "Aplicar filtros"}
            </button>
        </form>
      </section>


      {erro && (
        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800">
          {erro}
        </div>
      )}


      {avisos.length > 0 && (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
          Algumas seções não puderam ser carregadas:{" "}
          <strong>
            {avisos.join(
              ", ",
            )}
          </strong>.
        </div>
      )}


      {!dados
        && !carregando
        && !erro
        && (
          <div className="mt-5 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm leading-6 text-teal-800">
            Escolha os filtros e clique em <strong>Aplicar filtros</strong> para carregar as análises.
          </div>
        )}


      {carregando && (
        <section className="mt-6 space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {[
              1,
              2,
              3,
              4,
              5,
              6,
            ].map(
              (item) => (
                <div
                  key={item}
                  className="h-28 animate-pulse rounded-2xl bg-teal-50"
                />
              ),
            )}
          </div>

          <div className="h-80 animate-pulse rounded-2xl bg-teal-50" />
        </section>
      )}


      {dados
        && filtrosConfirmados
        && !carregando
        && (
          <section className="mt-6 space-y-8">
            <p className="text-sm leading-6 text-slate-500">
              Filtros aplicados — Base:{" "}
              <strong className="font-semibold text-slate-700">
                {
                  filtrosConfirmados
                    .modoDescricao
                }
              </strong>
              {" | "}UF:{" "}
              <strong className="font-semibold text-slate-700">
                {
                  filtrosConfirmados
                    .ufDescricao
                }
              </strong>
              {" | "}Evolução:{" "}
              <strong className="font-semibold text-slate-700">
                {formatarData(
                  filtrosConfirmados
                    .dataInicio,
                )}
              </strong>
              {" até "}
              <strong className="font-semibold text-slate-700">
                {formatarData(
                  filtrosConfirmados
                    .dataFim,
                )}
              </strong>
            </p>


            {numero(
              dados.kpis
                .instituicoes_com_registro,
            ) === 0
            && !avisos.includes(
              "Indicadores",
            ) ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm leading-6 text-amber-900">
                Nenhum registro de leitos foi encontrado para os filtros selecionados.
              </div>
            ) : (
              <>
                <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <Kpi
                    titulo="Leitos gerais"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .leitos_gerais,
                      )
                    }
                  />

                  <Kpi
                    titulo="Leitos SUS"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .leitos_sus,
                      )
                    }
                  />

                  <Kpi
                    titulo="Leitos de UTI"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .leitos_uti,
                      )
                    }
                  />

                  <Kpi
                    titulo="Leitos de UTI SUS"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .leitos_uti_sus,
                      )
                    }
                  />

                  <Kpi
                    titulo="Instituições com registro"
                    valor={
                      formatarNumero(
                        dados.kpis
                          .instituicoes_com_registro,
                      )
                    }
                  />

                  <Kpi
                    titulo="Participação do SUS"
                    valor={
                      formatarPercentual(
                        percentualSus,
                      )
                    }
                    descricao="Percentual dos leitos gerais identificados como destinados ao SUS."
                  />
                </section>


                <div className="rounded-xl bg-teal-50/70 px-4 py-3 text-sm leading-6 text-teal-900">
                  {filtrosConfirmados
                    .modo
                    === "ultima_competencia"
                    ? (
                      <>
                        Competência utilizada:{" "}
                        <strong>
                          {formatarData(
                            dados.kpis
                              .competencia_maxima,
                          )}
                        </strong>.
                      </>
                    ) : (
                      <>
                        As últimas posições das instituições estão entre{" "}
                        <strong>
                          {formatarData(
                            dados.kpis
                              .competencia_minima,
                          )}
                        </strong>
                        {" e "}
                        <strong>
                          {formatarData(
                            dados.kpis
                              .competencia_maxima,
                          )}
                        </strong>.
                      </>
                    )}
                </div>


                <section>
                  <div className="overflow-x-auto">
                    <div
                      className="inline-flex min-w-max rounded-xl border border-teal-100 bg-white p-1 shadow-sm"
                      role="tablist"
                      aria-label="Análises de leitos"
                    >
                      {abas.map(
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
                                item.id,
                              )
                            }
                            className={[
                              "rounded-lg px-4 py-2 text-sm font-medium transition",
                              aba
                                === item.id
                                ? "bg-teal-700 text-white"
                                : "text-slate-600 hover:bg-teal-50 hover:text-teal-800",
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
                    === "uf"
                    && (
                      <div className="mt-5">
                        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                          Distribuição geográfica dos leitos
                        </h2>

                        {porUfTabela.length
                          === 0 ? (
                          <div className="mt-4">
                            <Vazio>
                              Não há dados geográficos para exibir.
                            </Vazio>
                          </div>
                        ) : (
                          <div className="mt-4 space-y-5">
                            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                              <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                                <p className="mb-4 text-sm font-semibold text-slate-700">
                                  Leitos gerais e leitos SUS
                                </p>

                                <div className="h-80 w-full">
                                  <ResponsiveContainer
                                    width="100%"
                                    height="100%"
                                  >
                                    <BarChart
                                      data={
                                        porUfTabela
                                      }
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
                                        fontSize={10}
                                      />

                                      <YAxis
                                        type="category"
                                        dataKey="uf"
                                        width={48}
                                        fontSize={10}
                                      />

                                      <Tooltip />

                                      <Legend />

                                      <Bar
                                        dataKey="leitos_gerais"
                                        name="Leitos gerais"
                                        fill="var(--color-brand-blue)"
                                        radius={[
                                          0,
                                          4,
                                          4,
                                          0,
                                        ]}
                                      />

                                      <Bar
                                        dataKey="leitos_sus"
                                        name="Leitos SUS"
                                        fill="var(--step-5)"
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
                              </article>


                              <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                                <p className="mb-4 text-sm font-semibold text-slate-700">
                                  Leitos de UTI e UTI SUS
                                </p>

                                <div className="h-80 w-full">
                                  <ResponsiveContainer
                                    width="100%"
                                    height="100%"
                                  >
                                    <BarChart
                                      data={
                                        porUfTabela
                                      }
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
                                        fontSize={10}
                                      />

                                      <YAxis
                                        type="category"
                                        dataKey="uf"
                                        width={48}
                                        fontSize={10}
                                      />

                                      <Tooltip />

                                      <Legend />

                                      <Bar
                                        dataKey="leitos_uti"
                                        name="Leitos de UTI"
                                        fill="var(--color-brand-blue)"
                                        radius={[
                                          0,
                                          4,
                                          4,
                                          0,
                                        ]}
                                      />

                                      <Bar
                                        dataKey="leitos_uti_sus"
                                        name="UTI SUS"
                                        fill="var(--step-5)"
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
                              </article>
                            </div>

                            <div className="w-full">
                              <DataTable
                                data={
                                  porUfTabela
                                }
                                columns={
                                  colunasUf
                                }
                                pageSize={
                                  10
                                }
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}


                  {aba
                    === "uti"
                    && (
                      <div className="mt-5">
                        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                          Leitos de UTI por categoria
                        </h2>

                        {tiposTabela.length
                          === 0 ? (
                          <div className="mt-4">
                            <Vazio>
                              Não há informações de tipos de UTI.
                            </Vazio>
                          </div>
                        ) : (
                          <div className="mt-4 space-y-5">
                            <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                              <div className="h-80 w-full">
                                <ResponsiveContainer
                                  width="100%"
                                  height="100%"
                                >
                                  <BarChart
                                    data={
                                      tiposTabela
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
                                      vertical={false}
                                    />

                                    <XAxis
                                      dataKey="tipo_uti"
                                      fontSize={10}
                                    />

                                    <YAxis
                                      fontSize={10}
                                    />

                                    <Tooltip />

                                    <Legend />

                                    <Bar
                                      dataKey="total"
                                      name="Total"
                                      fill="var(--color-brand-blue)"
                                      radius={[
                                        5,
                                        5,
                                        0,
                                        0,
                                      ]}
                                    />

                                    <Bar
                                      dataKey="sus"
                                      name="SUS"
                                      fill="var(--step-5)"
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

                            <div className="w-full">
                              <DataTable
                                data={
                                  tiposTabela
                                }
                                columns={
                                  colunasTipos
                                }
                                pageSize={
                                  10
                                }
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}


                  {aba
                    === "evolucao"
                    && (
                      <div className="mt-5">
                        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                          Evolução dos leitos por competência
                        </h2>

                        {evolucaoGrafico.length
                          === 0 ? (
                          <div className="mt-4">
                            <Vazio>
                              Não há competências disponíveis no período selecionado.
                            </Vazio>
                          </div>
                        ) : (
                          <div className="mt-4 space-y-5">
                            <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                              <div className="h-80 w-full sm:h-96">
                                <ResponsiveContainer
                                  width="100%"
                                  height="100%"
                                >
                                  <LineChart
                                    data={
                                      evolucaoGrafico
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
                                      vertical={false}
                                    />

                                    <XAxis
                                      dataKey="competencia_rotulo"
                                      minTickGap={28}
                                      fontSize={10}
                                    />

                                    <YAxis
                                      width={64}
                                      fontSize={10}
                                    />

                                    <Tooltip />

                                    <Legend />

                                    <Line
                                      type="monotone"
                                      dataKey="leitos_gerais"
                                      name="Leitos gerais"
                                      stroke="var(--color-brand-blue)"
                                      strokeWidth={2.5}
                                      dot={false}
                                    />

                                    <Line
                                      type="monotone"
                                      dataKey="leitos_sus"
                                      name="Leitos SUS"
                                      stroke="var(--step-5)"
                                      strokeWidth={2.5}
                                      dot={false}
                                    />

                                    <Line
                                      type="monotone"
                                      dataKey="leitos_uti"
                                      name="Leitos de UTI"
                                      stroke="var(--step-2)"
                                      strokeWidth={2}
                                      dot={false}
                                    />

                                    <Line
                                      type="monotone"
                                      dataKey="leitos_uti_sus"
                                      name="UTI SUS"
                                      stroke="var(--step-1)"
                                      strokeWidth={2}
                                      dot={false}
                                    />
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            </article>

                            <div className="w-full">
                              <DataTable
                                data={
                                  dados.evolucao
                                }
                                columns={
                                  colunasEvolucao
                                }
                                pageSize={
                                  12
                                }
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}


                  {aba
                    === "instituicoes"
                    && (
                      <div className="mt-5">
                        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                          Instituições com mais leitos
                        </h2>

                        <p className="mt-1 text-sm leading-6 text-slate-500">
                          A tabela apresenta no máximo as 100 instituições com mais leitos gerais.
                        </p>

                        {dados.instituicoes.length
                          === 0 ? (
                          <div className="mt-4">
                            <Vazio>
                              Não há instituições para exibir.
                            </Vazio>
                          </div>
                        ) : (
                          <div className="mt-4 space-y-5">
                            <article className="min-w-0 rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-5">
                              <p className="mb-4 text-sm font-semibold text-slate-700">
                                20 instituições com mais leitos gerais
                              </p>

                              <div
                                className="w-full"
                                style={{
                                  height:
                                    Math.max(
                                      420,
                                      rankingGrafico
                                        .length
                                      * 34,
                                    ),
                                }}
                              >
                                <ResponsiveContainer
                                  width="100%"
                                  height="100%"
                                >
                                  <BarChart
                                    data={
                                      rankingGrafico
                                    }
                                    layout="vertical"
                                    margin={{
                                      top: 4,
                                      right: 16,
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
                                      fontSize={10}
                                    />

                                    <YAxis
                                      type="category"
                                      dataKey="instituicao"
                                      width={160}
                                      tickFormatter={(
                                        valor,
                                      ) =>
                                        truncar(
                                          valor,
                                          24,
                                        )
                                      }
                                      tickLine={false}
                                      fontSize={10}
                                    />

                                    <Tooltip />

                                    <Bar
                                      dataKey="leitos_gerais"
                                      name="Leitos gerais"
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
                            </article>

                            <div className="w-full">
                              <DataTable
                                data={
                                  dados.instituicoes
                                }
                                columns={
                                  colunasInstituicoes
                                }
                                pageSize={
                                  15
                                }
                              />
                            </div>
                          </div>
                        )}
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
