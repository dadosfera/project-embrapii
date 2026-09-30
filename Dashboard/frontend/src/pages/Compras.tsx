import {
  type FormEvent,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";

import type { ColumnDef } from "@tanstack/react-table";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DataTable } from "../components/DataTable";
import { CatmatPicker } from "../components/CatmatPicker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BotaoAplicar } from "@/ui/BotaoAplicar";
import { ChartFrame } from "@/ui/ChartFrame";
import { EmptyState } from "@/ui/EmptyState";
import { ErrorState } from "@/ui/ErrorState";
import { Icon } from "@/ui/Icon";
import { KpiCard } from "@/ui/KpiCard";
import { PageHeader } from "@/ui/PageHeader";
import { PeriodoAnos } from "@/ui/PeriodoAnos";
import { anosEntre, datasDoPeriodo, rotuloPeriodo } from "@/ui/periodo";
import { categorica, eixo, grade, tooltip } from "@/ui/chartTheme";
import { useEhTelaEstreita } from "@/ui/useEhTelaEstreita";
import {
  data as dataBR,
  moedaCompacta,
  moedaExata,
  numeroCompacto,
  numeroExato,
  percentual,
  quantidade,
} from "@/ui/format";

import { anotarOutliers, completarAnos, notaOutlier, type AnoCompras } from "./comprasAnual";

import {
  buscarComprasPorAno,
  buscarComprasPorModalidade,
  buscarComprasPorTipo,
  buscarComprasRecentes,
  buscarIntervaloCompras,
  buscarKpisCompras,
  buscarRankingFabricantes,
  buscarRankingFornecedores,
  listarProdutos,
  type GrupoCatmat,
  type CompraPorAno,
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
  porAno: CompraPorAno[];
  fornecedores: RankingFornecedorCompra[];
  fabricantes: RankingFabricanteCompra[];
  modalidades: CompraPorModalidade[];
  tipos: CompraPorTipo[];
  recentes: CompraRecente[];
};


type FiltrosConfirmados = {
  anoDe: number;
  anoAte: number;
  catmat_id: number | null;
  tipo: string;
  produto_descricao: string;
  tipo_descricao: string;
};


const TIPOS_COMPRA = [
  { valor: "Todos", rotulo: "Todos" },
  { valor: "ADMINISTRATIVA", rotulo: "Administrativa" },
  { valor: "JUDICIAL", rotulo: "Judicial" },
] as const;


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

  // Nomes de fornecedor/fabricante vêm em CAIXA ALTA (mais largos por caractere): numa tela
  // estreita, o eixo Y fixo de 120px não cabe os mesmos ~20 caracteres que cabem no desktop
  // (o rótulo sobra pela esquerda e o overflow-hidden do contêiner corta o começo do nome).
  const estreita = useEhTelaEstreita();

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
            width={estreita ? 100 : 120}
            tickFormatter={(valor) => truncar(valor, estreita ? 12 : 20)}
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
  // Filtro de medicamento: item-base CATMAT (as compras ficam no código-base puro, ver backend/catmat_index.py).
  const [
    grupoFiltro,
    setGrupoFiltro,
  ] = useState<GrupoCatmat | null>(null);

  // Intervalo de anos disponível (vem do backend): a página abre carregada com ele inteiro.
  const [
    anoMinimo,
    setAnoMinimo,
  ] = useState<number | null>(null);

  const [
    anoMaximo,
    setAnoMaximo,
  ] = useState<number | null>(null);

  const [
    anoDe,
    setAnoDe,
  ] = useState<number | null>(null);

  const [
    anoAte,
    setAnoAte,
  ] = useState<number | null>(null);

  const [
    carregandoIntervalo,
    setCarregandoIntervalo,
  ] = useState(true);

  // Falha ao buscar o intervalo: guarda o erro real; a tentativa refaz o efeito de carga.
  const [
    falhaIntervalo,
    setFalhaIntervalo,
  ] = useState<unknown>(null);

  const [
    tentativaIntervalo,
    setTentativaIntervalo,
  ] = useState(0);

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

  // Descarta respostas de pedidos antigos (padrão de Mapa.tsx: pedidoEstoque).
  const pedido =
    useRef(0);

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


  const anos = useMemo(
    () =>
      anoMinimo != null && anoMaximo != null
        ? anosEntre(anoMinimo, anoMaximo)
        : [],
    [anoMinimo, anoMaximo],
  );


  async function carregar(f: {
    anoDe: number;
    anoAte: number;
    grupo: GrupoCatmat | null;
    tipo: string;
  }) {
    setErro(null);
    setFalhaCarga(null);

    let catmatId:
      number | null =
        null;

    let produtoDescricao =
      "Todos os produtos";

    if (f.grupo) {
      catmatId = f.grupo.catmat_id;
      produtoDescricao = `${f.grupo.nome} — CATMAT ${f.grupo.base}`;
    }

    const meu = ++pedido.current;

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

        if (meu !== pedido.current) return;

        if (
          produtos.length === 0
        ) {
          setErro(
            "O CATMAT selecionado não possui produtos vinculados.",
          );
          setCarregando(false);
          return;
        }
      }

      const filtros:
        FiltrosCompras = {
          ...datasDoPeriodo(f.anoDe, f.anoAte),
          catmat_id:
            catmatId,
          tipo_compra:
            f.tipo
            === "Todos"
              ? ""
              : f.tipo,
        };

      const [
        kpis,
        porAno,
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
          buscarComprasPorAno(
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

      if (meu !== pedido.current) return;

      setFiltrosConfirmados({
        anoDe: f.anoDe,
        anoAte: f.anoAte,
        catmat_id: catmatId,
        tipo: f.tipo,
        produto_descricao:
          produtoDescricao,
        tipo_descricao:
          f.tipo,
      });

      setDados({
        kpis,
        porAno,
        fornecedores,
        fabricantes,
        modalidades,
        tipos,
        recentes,
      });
    } catch (error) {
      if (meu === pedido.current) setFalhaCarga(error);
    } finally {
      if (meu === pedido.current) setCarregando(false);
    }
  }


  // Busca o intervalo de anos disponível na montagem e carrega a página já com ele inteiro,
  // sem exigir clique. `tentativaIntervalo` refaz o efeito quando o usuário pede "Tentar de novo".
  useEffect(() => {
    let ativo = true;

    async function carregarIntervalo() {
      setCarregandoIntervalo(true);
      setFalhaIntervalo(null);

      try {
        const resposta = await buscarIntervaloCompras();
        if (!ativo) return;

        setAnoMinimo(resposta.ano_minimo);
        setAnoMaximo(resposta.ano_maximo);

        if (resposta.ano_minimo != null && resposta.ano_maximo != null) {
          setAnoDe(resposta.ano_minimo);
          setAnoAte(resposta.ano_maximo);
          await carregar({
            anoDe: resposta.ano_minimo,
            anoAte: resposta.ano_maximo,
            grupo: null,
            tipo: "Todos",
          });
        }
      } catch (error) {
        if (!ativo) return;
        setFalhaIntervalo(error);
      } finally {
        if (ativo) setCarregandoIntervalo(false);
      }
    }

    void carregarIntervalo();

    return () => {
      ativo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tentativaIntervalo]);


  async function aoSubmeter(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (anoDe == null || anoAte == null) return;

    await carregar({
      anoDe,
      anoAte,
      grupo: grupoFiltro,
      tipo: tipoCompra,
    });
  }


  // Há alterações não aplicadas: o form (anoDe/anoAte/grupo/tipo) diverge do que está na tela.
  const pendente =
    filtrosConfirmados != null
    && (
      anoDe !== filtrosConfirmados.anoDe
      || anoAte !== filtrosConfirmados.anoAte
      || (grupoFiltro?.catmat_id ?? null) !== filtrosConfirmados.catmat_id
      || tipoCompra !== filtrosConfirmados.tipo
    );


  // O /intervalo respondeu (sem falhar), mas não trouxe nenhum ano: não há compras na base.
  const semDadosBase =
    !carregandoIntervalo
    && falhaIntervalo == null
    && (anoMinimo == null || anoMaximo == null);


  const totalComprado =
    numero(
      dados?.kpis
        .valor_total,
    );


  const anosAnotados: AnoCompras[] =
    useMemo(
      () =>
        anotarOutliers(
          filtrosConfirmados
            ? completarAnos(
                dados?.porAno ?? [],
                filtrosConfirmados.anoDe,
                filtrosConfirmados.anoAte,
              )
            : dados?.porAno ?? [],
        ),
      [dados, filtrosConfirmados],
    );


  const anosMarcados =
    useMemo(
      () =>
        anosAnotados.filter(
          (a) => a.outlier,
        ),
      [anosAnotados],
    );


  // O maior dos outliers do período (na prática, quase sempre só há um): a base do hint do KPI.
  const anoDestaque =
    useMemo(
      () =>
        anosMarcados.reduce<
          AnoCompras | null
        >(
          (maior, atual) =>
            !maior
            || (atual.maior_registro ?? 0)
              > (maior.maior_registro ?? 0)
              ? atual
              : maior,
          null,
        ),
      [anosMarcados],
    );


  const hintValorTotal =
    anoDestaque
      ? `Inclui 1 registro de ${moedaCompacta(
          anoDestaque.maior_registro,
        )} em ${anoDestaque.ano}; veja a nota no gráfico anual.`
      : undefined;


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
            quantidade(
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
            quantidade(
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
            quantidade(
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
            quantidade(
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


  // Resolve a paleta uma vez por montagem (lê as variáveis CSS do documento).
  const paleta = useMemo(() => categorica(), []);

  // Id de pattern único (SVG): útil só depois de sanear os dois-pontos que useId() gera,
  // que não são válidos num id de atributo/url().
  const idHachura = `${useId().replace(/[^a-zA-Z0-9_-]/g, "")}-hachura`;


  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
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
          ref={formFiltros}
          onSubmit={aoSubmeter}
          className="mt-6 border-t border-line pt-6"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {anos.length > 0 && anoDe != null && anoAte != null ? (
              <PeriodoAnos
                id="compras-periodo"
                anos={anos}
                de={anoDe}
                ate={anoAte}
                onChange={(de, ate) => {
                  setAnoDe(de);
                  setAnoAte(ate);
                }}
                disabled={carregando}
                className="sm:col-span-2"
              />
            ) : carregandoIntervalo ? (
              <div className="sm:col-span-2">
                <Skeleton className="h-16 w-full max-w-sm" />
              </div>
            ) : null}

            <CatmatPicker
              id="produto-compras"
              label="Medicamento (opcional)"
              value={grupoFiltro}
              onSelect={setGrupoFiltro}
              placeholder="Todos os produtos — digite para filtrar"
              className="min-w-0"
            />

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
                  {TIPOS_COMPRA.map((item) => (
                    <SelectItem key={item.valor} value={item.valor}>
                      {item.rotulo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <BotaoAplicar
            type="submit"
            carregando={carregando}
            pendente={pendente}
            className="mx-auto mt-6 flex w-full flex-col items-center sm:w-1/2 lg:w-1/4"
          />
        </form>
      </section>


      {falhaIntervalo != null && (
        <div className="mt-5">
          <ErrorState
            error={falhaIntervalo}
            onRetry={() => setTentativaIntervalo((n) => n + 1)}
          />
        </div>
      )}


      {semDadosBase && (
        <div className="mt-5">
          <EmptyState
            title="Sem compras na base"
            cause="Não há compras registradas na base de dados."
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


      {falhaCarga != null && (
        <div className="mt-5">
          <ErrorState
            error={falhaCarga}
            onRetry={() => formFiltros.current?.requestSubmit()}
          />
        </div>
      )}


      {(carregando || carregandoIntervalo) && !dados && (
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
              Período:{" "}
              <strong className="font-semibold text-[var(--text)]">
                {rotuloPeriodo(
                  filtrosConfirmados.anoDe,
                  filtrosConfirmados.anoAte,
                )}
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
                    hint={hintValorTotal}
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
                    Evolução anual das compras
                  </h2>

                  {anosAnotados.length
                    === 0 ? (
                    <div className="mt-4">
                      <EmptyState
                        title="Sem série anual"
                        cause="Não há compras no período selecionado com esses filtros."
                      />
                    </div>
                  ) : (
                    <div className="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-2">
                      <div className="min-w-0">
                        <ChartFrame as="h3"
                          title="Valor total comprado por ano"
                          source="DATASUS"
                          legend={
                            anosMarcados.length > 0 ? (
                              <span className="flex items-center gap-2 text-xs text-muted">
                                <svg width={14} height={14} aria-hidden="true" style={{ outline: "none" }}>
                                  <rect width={14} height={14} fill={`url(#${idHachura})`} />
                                </svg>
                                Barra hachurada: um único registro passa de 20% do valor do ano. O registro foi mantido.
                              </span>
                            ) : undefined
                          }
                        >
                          <div className="h-72 w-full sm:h-80">
                            <ResponsiveContainer
                              width="100%"
                              height="100%"
                            >
                              <BarChart
                                data={anosAnotados}
                                margin={{
                                  top: 24,
                                  right: 8,
                                  bottom: 8,
                                  left: 0,
                                }}
                              >
                                <defs>
                                  <pattern
                                    id={idHachura}
                                    patternUnits="userSpaceOnUse"
                                    width={6}
                                    height={6}
                                    patternTransform="rotate(45)"
                                  >
                                    <rect width={6} height={6} fill="var(--beast-primary-100)" />
                                    <line x1={0} y1={0} x2={0} y2={6} stroke={paleta[0]} strokeWidth={3} />
                                  </pattern>
                                </defs>

                                <CartesianGrid {...grade} />

                                <XAxis
                                  {...eixo}
                                  dataKey="ano"
                                  tickFormatter={(valor, indice) =>
                                    anosAnotados[indice]?.outlier ? `${valor}*` : `${valor}`
                                  }
                                />

                                <YAxis
                                  {...eixo}
                                  width={75}
                                  tickFormatter={(valor) => moedaCompacta(numero(valor))}
                                />

                                <Tooltip
                                  {...tooltip}
                                  cursor={{ fill: "var(--beast-basic-300)" }}
                                  formatter={(valor) => moedaExata(numero(valor))}
                                />

                                <Bar
                                  dataKey="valor_total"
                                  name="Valor total"
                                  radius={[4, 4, 0, 0]}
                                >
                                  {anosAnotados.map((a) => (
                                    <Cell
                                      key={a.ano}
                                      fill={a.outlier ? `url(#${idHachura})` : paleta[0]}
                                    />
                                  ))}

                                  <LabelList
                                    dataKey="valor_total"
                                    position="top"
                                    formatter={(v: unknown) => moedaCompacta(numero(v))}
                                  />
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>

                          {anosMarcados.length > 0 && (
                            <ul className="mt-3 space-y-1 text-sm leading-6 text-muted">
                              {anosMarcados.map((a) => (
                                <li key={a.ano}>{notaOutlier(a)}</li>
                              ))}
                            </ul>
                          )}
                        </ChartFrame>
                      </div>


                      <div className="min-w-0">
                        <ChartFrame as="h3"
                          title="Registros de compra por ano"
                          source="DATASUS"
                        >
                          <div className="h-72 w-full sm:h-80">
                            <ResponsiveContainer
                              width="100%"
                              height="100%"
                            >
                              <BarChart
                                data={anosAnotados}
                                margin={{
                                  top: 24,
                                  right: 8,
                                  bottom: 8,
                                  left: 0,
                                }}
                              >
                                <CartesianGrid {...grade} />

                                <XAxis
                                  {...eixo}
                                  dataKey="ano"
                                />

                                <YAxis
                                  {...eixo}
                                  width={48}
                                  tickFormatter={(valor) => numeroCompacto(numero(valor))}
                                />

                                <Tooltip
                                  {...tooltip}
                                  cursor={{ fill: "var(--beast-basic-300)" }}
                                  formatter={(valor) => numeroExato(numero(valor))}
                                />

                                <Bar
                                  dataKey="numero_compras"
                                  name="Compras"
                                  fill={paleta[0]}
                                  radius={[4, 4, 0, 0]}
                                >
                                  <LabelList
                                    dataKey="numero_compras"
                                    position="top"
                                    formatter={(v: unknown) => numeroCompacto(numero(v))}
                                  />
                                </Bar>
                              </BarChart>
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
