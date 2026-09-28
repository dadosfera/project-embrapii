import {
  type FormEvent,
  useEffect,
  useMemo,
  useRef,
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
  data as dataBR,
  numeroCompacto,
  numeroExato,
  SEM_DADO,
} from "@/ui/format";

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

import { inicioHaMeses } from "./leitosDatas";


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


/** O Radix Select não aceita item com value "": "Todas" usa esta sentinela na UI. */
const TODAS_UFS = "__todas__";

/** Período padrão da evolução: 24 meses de calendário até a competência mais recente. */
const MESES_PADRAO = 24;


/** Coerção numérica (a API pode mandar decimal como string). Usada nos gráficos e nas contas. */
function numero(valor: unknown) {
  const convertido = Number(valor);
  return Number.isFinite(convertido) ? convertido : 0;
}


/** Para KPI: nulo continua nulo (vira "sem dado"), nunca 0. */
function numeroOuNulo(valor: unknown): number | null {
  if (valor === null || valor === undefined || valor === "") return null;
  const convertido = Number(valor);
  return Number.isFinite(convertido) ? convertido : null;
}


/** Participação com uma casa ("12,3%"). O format.ts não tem percentual, por isso fica aqui. */
function percentual(valor: number | null | undefined) {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return SEM_DADO;
  return `${valor.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}


const MESES_CURTOS = [
  "jan", "fev", "mar", "abr", "mai", "jun",
  "jul", "ago", "set", "out", "nov", "dez",
];


/** "AAAA-MM-DD" → "set/24", rótulo do eixo de competências. O format.ts não tem mês, por isso fica aqui. */
function rotuloMes(valor: string) {
  const [ano, mes] = valor.slice(0, 10).split("-").map(Number);
  if (!ano || !mes) return valor;
  return `${MESES_CURTOS[mes - 1]}/${String(ano).slice(-2)}`;
}


/** "AAAA-MM-DD" → Date local (sem passar por UTC, que deslocaria o dia). */
function dataLocal(iso: string) {
  const [ano, mes, dia] = iso.slice(0, 10).split("-").map(Number);
  return new Date(ano, mes - 1, dia);
}


function truncar(valor: unknown, limite = 28) {
  const texto = String(valor ?? "Não informado");
  return texto.length <= limite ? texto : `${texto.slice(0, limite - 1)}…`;
}


const ABAS: { id: AbaLeitos; label: string }[] = [
  { id: "uf", label: "Distribuição por UF" },
  { id: "uti", label: "Tipos de UTI" },
  { id: "evolucao", label: "Evolução histórica" },
  { id: "instituicoes", label: "Instituições" },
];


const MARGEM_HORIZONTAL = { top: 4, right: 12, bottom: 4, left: 4 };
const MARGEM_VERTICAL = { top: 8, right: 8, bottom: 8, left: 0 };
// itemSorter null: a legenda segue a ordem das séries (o padrão do Recharts 3 ordena por nome).
const LEGENDA = {
  itemSorter: null,
  wrapperStyle: { fontSize: 12, fontFamily: "var(--font-body)", color: "var(--text)" },
};


const formatarTooltip = (valor: unknown) => numeroExato(numero(valor));


export function Leitos() {
  const [intervalo, setIntervalo] = useState<IntervaloLeitos | null>(null);
  const [ufs, setUfs] = useState<string[]>([]);
  const [carregandoOpcoes, setCarregandoOpcoes] = useState(true);
  // Falha ao buscar as opções: guarda o erro real; a tentativa refaz o efeito de carga.
  const [falhaOpcoes, setFalhaOpcoes] = useState<unknown>(null);
  const [tentativaOpcoes, setTentativaOpcoes] = useState(0);
  const [modo, setModo] = useState<ModoLeitos>("ultima_competencia");
  const [uf, setUf] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [carregando, setCarregando] = useState(false);
  // Mensagem de validação da página (aviso inline).
  const [erro, setErro] = useState<string | null>(null);
  // Falha de requisição do painel: guarda o erro real para o ErrorState.
  const [falhaPainel, setFalhaPainel] = useState<unknown>(null);
  const [avisos, setAvisos] = useState<string[]>([]);
  const [filtrosConfirmados, setFiltrosConfirmados] = useState<FiltrosConfirmados | null>(null);
  const [dados, setDados] = useState<DadosLeitos | null>(null);
  const [aba, setAba] = useState<AbaLeitos>("uf");

  const formFiltros = useRef<HTMLFormElement>(null);

  // Resolve a paleta uma vez por montagem (lê as variáveis CSS do documento).
  const paleta = useMemo(() => categorica(), []);


  useEffect(() => {
    let ativo = true;

    async function carregarOpcoes() {
      setCarregandoOpcoes(true);
      setFalhaOpcoes(null);

      try {
        const resposta = await buscarOpcoesLeitos();
        if (!ativo) return;

        setIntervalo({
          data_minima: resposta.data_minima,
          data_maxima: resposta.data_maxima,
        });
        setUfs(resposta.ufs.filter(Boolean));

        if (resposta.data_minima && resposta.data_maxima) {
          const inicioCandidato = inicioHaMeses(dataLocal(resposta.data_maxima), MESES_PADRAO);
          setDataInicio(
            inicioCandidato < resposta.data_minima
              ? resposta.data_minima
              : inicioCandidato,
          );
          setDataFim(resposta.data_maxima);
        }
      } catch (error) {
        if (!ativo) return;
        setFalhaOpcoes(error);
      } finally {
        if (ativo) setCarregandoOpcoes(false);
      }
    }

    void carregarOpcoes();

    return () => {
      ativo = false;
    };
  }, [tentativaOpcoes]);


  async function aplicarFiltros(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setErro(null);
    setFalhaPainel(null);
    setAvisos([]);

    if (!dataInicio || !dataFim) {
      setErro("Informe o início e o final da evolução histórica.");
      return;
    }

    if (dataFim < dataInicio) {
      setErro("A data final não pode ser anterior à data inicial.");
      return;
    }

    setCarregando(true);
    setAba("uf");

    const filtros: FiltrosLeitos = { modo, uf };

    try {
      const resposta = await buscarPainelLeitos(filtros, dataInicio, dataFim);

      setDados({
        kpis: resposta.kpis,
        porUf: resposta.por_uf,
        tiposUti: resposta.tipos_uti,
        evolucao: resposta.evolucao,
        instituicoes: resposta.instituicoes,
      });

      setAvisos([]);

      setFiltrosConfirmados({
        modo,
        modoDescricao:
          modo === "ultima_competencia"
            ? "Competência mais recente da base"
            : "Última posição de cada instituição",
        uf,
        ufDescricao: uf || "Todas",
        dataInicio,
        dataFim,
      });
    } catch (error) {
      setFalhaPainel(error);
    } finally {
      setCarregando(false);
    }
  }


  // Sem leitos gerais não há participação a calcular: vira "sem dado", não 0%.
  const percentualSus =
    dados && numero(dados.kpis.leitos_gerais) > 0
      ? (numero(dados.kpis.leitos_sus) / numero(dados.kpis.leitos_gerais)) * 100
      : null;


  const porUfTabela = useMemo(
    () =>
      (dados?.porUf ?? []).map((item) => {
        const gerais = numero(item.leitos_gerais);
        const sus = numero(item.leitos_sus);
        const uti = numero(item.leitos_uti);
        const utiSus = numero(item.leitos_uti_sus);

        return {
          ...item,
          percentual_sus: gerais > 0 ? (sus / gerais) * 100 : null,
          percentual_uti_sus: uti > 0 ? (utiSus / uti) * 100 : null,
        };
      }),
    [dados],
  );


  const tiposTabela = useMemo(
    () =>
      (dados?.tiposUti ?? []).map((item) => {
        const total = numero(item.total);
        const sus = numero(item.sus);
        return {
          ...item,
          percentual_sus: total > 0 ? (sus / total) * 100 : null,
        };
      }),
    [dados],
  );


  const evolucaoGrafico = useMemo(
    () =>
      (dados?.evolucao ?? []).map((item) => ({
        ...item,
        competencia_rotulo: rotuloMes(item.competencia),
        leitos_gerais: numero(item.leitos_gerais),
        leitos_sus: numero(item.leitos_sus),
        leitos_uti: numero(item.leitos_uti),
        leitos_uti_sus: numero(item.leitos_uti_sus),
      })),
    [dados],
  );


  const pontosEvolucao = dotPara(evolucaoGrafico.length);


  const rankingGrafico = useMemo(
    () =>
      (dados?.instituicoes ?? []).slice(0, 20).map((item) => ({
        instituicao: item.instituicao,
        leitos_gerais: numero(item.leitos_gerais),
      })),
    [dados],
  );


  const colunasUf = useMemo<
    ColumnDef<
      LeitosPorUf & { percentual_sus: number | null; percentual_uti_sus: number | null },
      unknown
    >[]
  >(
    () => [
      { header: "UF", accessorKey: "uf" },
      {
        header: "Leitos gerais",
        accessorKey: "leitos_gerais",
        cell: ({ row }) => numeroExato(row.original.leitos_gerais),
        meta: { align: "right" },
      },
      {
        header: "Leitos SUS",
        accessorKey: "leitos_sus",
        cell: ({ row }) => numeroExato(row.original.leitos_sus),
        meta: { align: "right" },
      },
      {
        header: "Leitos de UTI",
        accessorKey: "leitos_uti",
        cell: ({ row }) => numeroExato(row.original.leitos_uti),
        meta: { align: "right" },
      },
      {
        header: "UTI SUS",
        accessorKey: "leitos_uti_sus",
        cell: ({ row }) => numeroExato(row.original.leitos_uti_sus),
        meta: { align: "right" },
      },
      {
        header: "Instituições",
        accessorKey: "instituicoes",
        cell: ({ row }) => numeroExato(row.original.instituicoes),
        meta: { align: "right" },
      },
      {
        header: "Leitos SUS (%)",
        accessorKey: "percentual_sus",
        cell: ({ row }) => percentual(row.original.percentual_sus),
        meta: { align: "right" },
      },
      {
        header: "UTI SUS (%)",
        accessorKey: "percentual_uti_sus",
        cell: ({ row }) => percentual(row.original.percentual_uti_sus),
        meta: { align: "right" },
      },
    ],
    [],
  );


  const colunasTipos = useMemo<
    ColumnDef<TipoUti & { percentual_sus: number | null }, unknown>[]
  >(
    () => [
      { header: "Tipo de UTI", accessorKey: "tipo_uti" },
      {
        header: "Total",
        accessorKey: "total",
        cell: ({ row }) => numeroExato(row.original.total),
        meta: { align: "right" },
      },
      {
        header: "SUS",
        accessorKey: "sus",
        cell: ({ row }) => numeroExato(row.original.sus),
        meta: { align: "right" },
      },
      {
        header: "SUS (%)",
        accessorKey: "percentual_sus",
        cell: ({ row }) => percentual(row.original.percentual_sus),
        meta: { align: "right" },
      },
    ],
    [],
  );


  const colunasEvolucao = useMemo<ColumnDef<EvolucaoLeitos, unknown>[]>(
    () => [
      {
        header: "Competência",
        accessorKey: "competencia",
        cell: ({ row }) => dataBR(row.original.competencia),
      },
      {
        header: "Leitos gerais",
        accessorKey: "leitos_gerais",
        cell: ({ row }) => numeroExato(row.original.leitos_gerais),
        meta: { align: "right" },
      },
      {
        header: "Leitos SUS",
        accessorKey: "leitos_sus",
        cell: ({ row }) => numeroExato(row.original.leitos_sus),
        meta: { align: "right" },
      },
      {
        header: "Leitos de UTI",
        accessorKey: "leitos_uti",
        cell: ({ row }) => numeroExato(row.original.leitos_uti),
        meta: { align: "right" },
      },
      {
        header: "UTI SUS",
        accessorKey: "leitos_uti_sus",
        cell: ({ row }) => numeroExato(row.original.leitos_uti_sus),
        meta: { align: "right" },
      },
      {
        header: "Instituições",
        accessorKey: "instituicoes",
        cell: ({ row }) => numeroExato(row.original.instituicoes),
        meta: { align: "right" },
      },
    ],
    [],
  );


  const colunasInstituicoes = useMemo<ColumnDef<InstituicaoLeitos, unknown>[]>(
    () => [
      { header: "ID", accessorKey: "instituicao_id", meta: { priority: "low" } },
      { header: "Instituição", accessorKey: "instituicao" },
      { header: "Município", accessorKey: "municipio", meta: { priority: "low" } },
      { header: "UF", accessorKey: "uf" },
      {
        header: "Competência",
        accessorKey: "competencia",
        cell: ({ row }) => dataBR(row.original.competencia),
      },
      {
        header: "Leitos gerais",
        accessorKey: "leitos_gerais",
        cell: ({ row }) => numeroExato(row.original.leitos_gerais),
        meta: { align: "right" },
      },
      {
        header: "Leitos SUS",
        accessorKey: "leitos_sus",
        cell: ({ row }) => numeroExato(row.original.leitos_sus),
        meta: { align: "right" },
      },
      {
        header: "Leitos de UTI",
        accessorKey: "leitos_uti",
        cell: ({ row }) => numeroExato(row.original.leitos_uti),
        meta: { align: "right" },
      },
      {
        header: "UTI SUS",
        accessorKey: "leitos_uti_sus",
        cell: ({ row }) => numeroExato(row.original.leitos_uti_sus),
        meta: { align: "right" },
      },
    ],
    [],
  );


  // Uma linha legível por UF (27 no país); com poucas UFs fica no mínimo de 320 px.
  const alturaUf = Math.max(320, porUfTabela.length * 24);


  const semFalhas = falhaOpcoes == null && falhaPainel == null;


  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <PageHeader
        icon="activity"
        title="Leitos"
        description="Analise a capacidade de leitos hospitalares, a participação do SUS e os diferentes tipos de UTI."
      />


      <section className="mt-7 rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-6">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--text)]">
            <Icon name="funnel" size={18} className="text-primary" />
            Filtros
          </h2>

          <p className="mt-1 text-sm leading-6 text-muted">
            O período é aplicado somente à evolução histórica.
          </p>

          {carregandoOpcoes && (
            <p className="mt-2 text-xs font-medium text-primary" role="status">
              Carregando intervalo e unidades federativas...
            </p>
          )}
        </div>


        <form
          ref={formFiltros}
          onSubmit={aplicarFiltros}
          className="mt-5"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="min-w-0">
              <label
                htmlFor="modo-leitos"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Base utilizada nos indicadores
              </label>

              <Select
                value={modo}
                onValueChange={(valor) => {
                  if (valor === "ultima_competencia" || valor === "ultima_instituicao") {
                    setModo(valor);
                  }
                }}
              >
                <SelectTrigger
                  id="modo-leitos"
                  className="mt-2 h-10 w-full min-w-0 bg-panel data-[size=default]:h-10"
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent position="popper">
                  <SelectItem value="ultima_competencia">
                    Competência mais recente da base
                  </SelectItem>
                  <SelectItem value="ultima_instituicao">
                    Última posição de cada instituição
                  </SelectItem>
                </SelectContent>
              </Select>

              <p className="mt-2 text-xs leading-5 text-muted">
                A competência mais recente compara instituições no mesmo período; a última posição aumenta a cobertura, mas pode combinar competências distintas.
              </p>
            </div>


            <div className="min-w-0">
              <label
                htmlFor="uf-leitos"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Unidade Federativa
              </label>

              <Select
                value={uf || TODAS_UFS}
                disabled={carregandoOpcoes}
                onValueChange={(valor) => setUf(valor === TODAS_UFS ? "" : valor)}
              >
                <SelectTrigger
                  id="uf-leitos"
                  className="mt-2 h-10 w-full min-w-0 bg-panel data-[size=default]:h-10"
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent position="popper" className="max-h-72">
                  <SelectItem value={TODAS_UFS}>
                    {carregandoOpcoes ? "Carregando UFs..." : "Todas"}
                  </SelectItem>

                  {ufs.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>


            <div>
              <label
                htmlFor="inicio-evolucao"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Início da evolução
              </label>

              <Input
                id="inicio-evolucao"
                type="date"
                disabled={carregandoOpcoes || !intervalo}
                value={dataInicio}
                min={intervalo?.data_minima ?? undefined}
                max={intervalo?.data_maxima ?? undefined}
                onChange={(event) => setDataInicio(event.target.value)}
                className="mt-2 h-10 bg-panel"
              />
            </div>


            <div>
              <label
                htmlFor="fim-evolucao"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Final da evolução
              </label>

              <Input
                id="fim-evolucao"
                type="date"
                disabled={carregandoOpcoes || !intervalo}
                value={dataFim}
                min={intervalo?.data_minima ?? undefined}
                max={intervalo?.data_maxima ?? undefined}
                onChange={(event) => setDataFim(event.target.value)}
                className="mt-2 h-10 bg-panel"
              />
            </div>
          </div>


          <Button
            type="submit"
            disabled={carregando || !dataInicio || !dataFim}
            className="mx-auto mt-6 flex h-10 w-full sm:w-1/2 lg:w-1/4"
          >
            {carregando
              ? "Carregando análises..."
              : "Aplicar filtros"}
          </Button>
        </form>
      </section>


      {falhaOpcoes != null && (
        <div className="mt-5">
          <ErrorState
            error={falhaOpcoes}
            onRetry={() => setTentativaOpcoes((n) => n + 1)}
          />
        </div>
      )}


      {erro && (
        <div
          role="status"
          className="mt-5 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text"
        >
          <Icon name="alert" size={18} className="mt-0.5" />
          {erro}
        </div>
      )}


      {falhaPainel != null && (
        <div className="mt-5">
          <ErrorState
            error={falhaPainel}
            onRetry={() => formFiltros.current?.requestSubmit()}
          />
        </div>
      )}


      {avisos.length > 0 && (
        <div
          role="status"
          className="mt-5 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text"
        >
          <Icon name="alert" size={18} className="mt-0.5" />
          <span>
            Algumas seções não puderam ser carregadas:{" "}
            <strong>{avisos.join(", ")}</strong>.
          </span>
        </div>
      )}


      {!dados
        && !carregando
        && !erro
        && semFalhas
        && (
          <div className="mt-5 flex items-start gap-2 rounded-[var(--radius-md)] border border-line bg-primary-tint px-4 py-3 text-sm leading-6 text-[var(--text)]">
            <Icon name="info" size={18} className="mt-0.5 text-primary" />
            <span>
              Escolha os filtros e clique em <strong>Aplicar filtros</strong> para carregar as análises.
            </span>
          </div>
        )}


      {carregando && (
        <section className="mt-6 space-y-4" aria-busy="true">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((item) => (
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
              Filtros aplicados — Base:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {filtrosConfirmados.modoDescricao}
              </strong>
              {" | "}UF:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {filtrosConfirmados.ufDescricao}
              </strong>
              {" | "}Evolução:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {dataBR(filtrosConfirmados.dataInicio)}
              </strong>
              {" até "}
              <strong className="font-semibold text-[var(--text)]">
                {dataBR(filtrosConfirmados.dataFim)}
              </strong>
            </p>


            {numero(dados.kpis.instituicoes_com_registro) === 0
            && !avisos.includes("Indicadores") ? (
              <EmptyState
                title="Sem leitos para estes filtros"
                cause="Nenhum registro de leitos foi encontrado para a base e a UF selecionadas."
              />
            ) : (
              <>
                <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-3">
                  <KpiCard
                    label="Leitos gerais"
                    value={numeroOuNulo(dados.kpis.leitos_gerais)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Leitos SUS"
                    value={numeroOuNulo(dados.kpis.leitos_sus)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Leitos de UTI"
                    value={numeroOuNulo(dados.kpis.leitos_uti)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Leitos de UTI SUS"
                    value={numeroOuNulo(dados.kpis.leitos_uti_sus)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Instituições com registro"
                    value={numeroOuNulo(dados.kpis.instituicoes_com_registro)}
                    format={numeroCompacto}
                  />

                  <KpiCard
                    label="Participação do SUS"
                    value={percentualSus}
                    format={percentual}
                    exact={percentual}
                    hint="Percentual dos leitos gerais identificados como destinados ao SUS."
                  />
                </section>


                <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-line bg-primary-tint px-4 py-3 text-sm leading-6 text-[var(--text)]">
                  <Icon name="calendar" size={18} className="mt-0.5 text-primary" />
                  <span>
                    {filtrosConfirmados.modo === "ultima_competencia" ? (
                      <>
                        Competência utilizada:{" "}
                        <strong>{dataBR(dados.kpis.competencia_maxima)}</strong>.
                      </>
                    ) : (
                      <>
                        As últimas posições das instituições estão entre{" "}
                        <strong>{dataBR(dados.kpis.competencia_minima)}</strong>
                        {" e "}
                        <strong>{dataBR(dados.kpis.competencia_maxima)}</strong>.
                      </>
                    )}
                  </span>
                </div>


                <Tabs
                  value={aba}
                  onValueChange={(valor) => setAba(valor as AbaLeitos)}
                >
                  <TabsList
                    aria-label="Análises de leitos"
                    className="w-full flex-wrap justify-start group-data-[orientation=horizontal]/tabs:h-auto sm:w-fit sm:flex-nowrap sm:group-data-[orientation=horizontal]/tabs:h-9"
                  >
                    {ABAS.map((item) => (
                      <TabsTrigger
                        key={item.id}
                        value={item.id}
                        className="min-h-8 px-4 sm:flex-none"
                      >
                        {item.label}
                      </TabsTrigger>
                    ))}
                  </TabsList>


                  <TabsContent value="uf" className="mt-3">
                    <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                      Distribuição geográfica dos leitos
                    </h2>

                    {porUfTabela.length === 0 ? (
                      <div className="mt-4">
                        <EmptyState
                          title="Sem dados por UF"
                          cause="Nenhuma UF tem leitos registrados para os filtros aplicados."
                        />
                      </div>
                    ) : (
                      <div className="mt-4 space-y-5">
                        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                          <div className="min-w-0">
                            <ChartFrame as="h3" title="Leitos gerais e leitos SUS" source="DATASUS">
                              <div className="w-full" style={{ height: alturaUf }}>
                                <ResponsiveContainer width="100%" height="100%">
                                  <BarChart data={porUfTabela} layout="vertical" margin={MARGEM_HORIZONTAL}>
                                    <CartesianGrid {...grade} horizontal={false} vertical />
                                    <XAxis {...eixo} type="number" tickFormatter={(v) => numeroCompacto(v)} />
                                    <YAxis {...eixo} type="category" dataKey="uf" width={40} tick={{ ...eixo.tick, fontSize: 11 }} />
                                    <Tooltip {...tooltip} formatter={formatarTooltip} />
                                    <Legend {...LEGENDA} />
                                    <Bar dataKey="leitos_gerais" name="Leitos gerais" fill={paleta[0]} radius={[0, 4, 4, 0]} />
                                    <Bar dataKey="leitos_sus" name="Leitos SUS" fill={paleta[1]} radius={[0, 4, 4, 0]} />
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                            </ChartFrame>
                          </div>

                          <div className="min-w-0">
                            <ChartFrame as="h3" title="Leitos de UTI e UTI SUS" source="DATASUS">
                              <div className="w-full" style={{ height: alturaUf }}>
                                <ResponsiveContainer width="100%" height="100%">
                                  <BarChart data={porUfTabela} layout="vertical" margin={MARGEM_HORIZONTAL}>
                                    <CartesianGrid {...grade} horizontal={false} vertical />
                                    <XAxis {...eixo} type="number" tickFormatter={(v) => numeroCompacto(v)} />
                                    <YAxis {...eixo} type="category" dataKey="uf" width={40} tick={{ ...eixo.tick, fontSize: 11 }} />
                                    <Tooltip {...tooltip} formatter={formatarTooltip} />
                                    <Legend {...LEGENDA} />
                                    <Bar dataKey="leitos_uti" name="Leitos de UTI" fill={paleta[0]} radius={[0, 4, 4, 0]} />
                                    <Bar dataKey="leitos_uti_sus" name="UTI SUS" fill={paleta[1]} radius={[0, 4, 4, 0]} />
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                            </ChartFrame>
                          </div>
                        </div>

                        <DataTable data={porUfTabela} columns={colunasUf} pageSize={10} />
                      </div>
                    )}
                  </TabsContent>


                  <TabsContent value="uti" className="mt-3">
                    <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                      Leitos de UTI por categoria
                    </h2>

                    {tiposTabela.length === 0 ? (
                      <div className="mt-4">
                        <EmptyState
                          title="Sem tipos de UTI"
                          cause="As instituições filtradas não informaram leitos de UTI por categoria."
                        />
                      </div>
                    ) : (
                      <div className="mt-4 space-y-5">
                        <ChartFrame as="h3" title="Total e SUS por tipo de UTI" source="DATASUS">
                          <div className="h-80 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={tiposTabela} margin={MARGEM_VERTICAL}>
                                <CartesianGrid {...grade} />
                                <XAxis {...eixo} dataKey="tipo_uti" tick={{ ...eixo.tick, fontSize: 11 }} />
                                <YAxis {...eixo} width={56} tickFormatter={(v) => numeroCompacto(v)} />
                                <Tooltip {...tooltip} formatter={formatarTooltip} />
                                <Legend {...LEGENDA} />
                                <Bar dataKey="total" name="Total" fill={paleta[0]} radius={[4, 4, 0, 0]} />
                                <Bar dataKey="sus" name="SUS" fill={paleta[1]} radius={[4, 4, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </ChartFrame>

                        <DataTable data={tiposTabela} columns={colunasTipos} pageSize={10} />
                      </div>
                    )}
                  </TabsContent>


                  <TabsContent value="evolucao" className="mt-3">
                    <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                      Evolução dos leitos por competência
                    </h2>

                    {evolucaoGrafico.length === 0 ? (
                      <div className="mt-4">
                        <EmptyState
                          title="Sem competências no período"
                          cause="Não há competências disponíveis entre as datas de início e final da evolução."
                        />
                      </div>
                    ) : (
                      <div className="mt-4 space-y-5">
                        <ChartFrame as="h3"
                          title="Leitos por competência"
                          subtitle={`${dataBR(filtrosConfirmados.dataInicio)} a ${dataBR(filtrosConfirmados.dataFim)}`}
                          source="DATASUS"
                        >
                          <div className="h-80 w-full sm:h-96">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={evolucaoGrafico} margin={MARGEM_VERTICAL}>
                                <CartesianGrid {...grade} />
                                <XAxis {...eixo} dataKey="competencia_rotulo" minTickGap={28} />
                                <YAxis {...eixo} width={56} tickFormatter={(v) => numeroCompacto(v)} />
                                <Tooltip
                                  {...tooltip}
                                  cursor={{ stroke: "var(--beast-basic-600)" }}
                                  formatter={formatarTooltip}
                                />
                                <Legend {...LEGENDA} />
                                {/* As duas séries principais (gerais × SUS) ficam em primary × info. */}
                                <Line {...linha} dataKey="leitos_gerais" name="Leitos gerais" stroke={paleta[0]} dot={pontosEvolucao} />
                                <Line {...linha} dataKey="leitos_sus" name="Leitos SUS" stroke={paleta[1]} dot={pontosEvolucao} />
                                <Line {...linha} dataKey="leitos_uti" name="Leitos de UTI" stroke={paleta[2]} dot={pontosEvolucao} />
                                <Line {...linha} dataKey="leitos_uti_sus" name="UTI SUS" stroke={paleta[3]} dot={pontosEvolucao} />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </ChartFrame>

                        <DataTable data={dados.evolucao} columns={colunasEvolucao} pageSize={12} />
                      </div>
                    )}
                  </TabsContent>


                  <TabsContent value="instituicoes" className="mt-3">
                    <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                      Instituições com mais leitos
                    </h2>

                    <p className="mt-1 text-sm leading-6 text-muted">
                      A tabela apresenta no máximo as 100 instituições com mais leitos gerais.
                    </p>

                    {dados.instituicoes.length === 0 ? (
                      <div className="mt-4">
                        <EmptyState
                          title="Sem instituições"
                          cause="Nenhuma instituição tem leitos registrados para os filtros aplicados."
                        />
                      </div>
                    ) : (
                      <div className="mt-4 space-y-5">
                        <ChartFrame as="h3" title="20 instituições com mais leitos gerais" source="DATASUS">
                          <div
                            className="w-full"
                            style={{ height: Math.max(420, rankingGrafico.length * 34) }}
                          >
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={rankingGrafico}
                                layout="vertical"
                                margin={{ top: 4, right: 16, bottom: 4, left: 4 }}
                              >
                                <CartesianGrid {...grade} horizontal={false} vertical />
                                <XAxis {...eixo} type="number" tickFormatter={(v) => numeroCompacto(v)} />
                                <YAxis
                                  {...eixo}
                                  type="category"
                                  dataKey="instituicao"
                                  width={150}
                                  tick={{ ...eixo.tick, fontSize: 11 }}
                                  tickFormatter={(valor) => truncar(valor, 22)}
                                />
                                <Tooltip {...tooltip} formatter={formatarTooltip} />
                                <Bar dataKey="leitos_gerais" name="Leitos gerais" fill={paleta[0]} radius={[0, 4, 4, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </ChartFrame>

                        <DataTable data={dados.instituicoes} columns={colunasInstituicoes} pageSize={15} />
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </>
            )}
          </section>
        )}
    </main>
  );
}
