import {
  type ColumnDef,
} from "@tanstack/react-table";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { DataTable } from "../components/DataTable";
import { MapaBrasilUf, type DadoMapaUf } from "../components/MapaBrasil";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/ui/EmptyState";
import { ErrorState } from "@/ui/ErrorState";
import { KpiCard } from "@/ui/KpiCard";
import { PageHeader } from "@/ui/PageHeader";
import {
  moedaExata,
  numeroCompacto,
  numeroExato,
  quantidade,
  SEM_DADO,
} from "@/ui/format";
import { PeriodoAnos } from "@/ui/PeriodoAnos";
import { anosEntre, datasDoPeriodo } from "@/ui/periodo";
import { buscarIntervaloCompras } from "../lib/api";
import {
  buscarMapaFornecedoresPorUf,
  buscarRankingFornecedores,
  type MapaFornecedorUf,
  type RankingFornecedor,
} from "../lib/fornecedoresApi";


/** Compras vêm do DATASUS; origem e sócios do fornecedor, do CNPJ na Receita Federal. */
const FONTE =
  "DATASUS (compras); origem do fornecedor: Receita Federal, dados abertos de CNPJ via BrasilAPI";


/** Participação com uma casa ("12,3%"). O format.ts não tem percentual, por isso fica aqui. */
function percentual(valor: number | null | undefined) {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return SEM_DADO;
  return `${valor.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

/**
 * Mesma casa decimal de `percentual`, mas sem o "%": é o `formatar` do mapa, que já recebe
 * `unidade="%"` e monta "5,7 %" / "Legenda (%)" sozinho — com `percentual` viraria "5,7% %".
 */
function numeroUmaCasa(valor: number) {
  return valor.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}


/** `null` quando não há compra no período (UF sem registro), em vez de 0%. */
function calcularPercentualEstrangeiro(item: MapaFornecedorUf): number | null {
  const totalEstrangeiro =
    item.quantidade_estrangeiro + item.quantidade_grupo_estrangeiro;
  const total = item.quantidade_nacional + totalEstrangeiro;
  if (total <= 0) return null;
  return (totalEstrangeiro / total) * 100;
}


const ESTILOS_ORIGEM: Record<RankingFornecedor["nacional_estrangeiro"], string> = {
  NACIONAL: "border-transparent bg-primary-soft text-primary",
  ESTRANGEIRO: "border-warning-border bg-[var(--warning-soft)] text-warning-text",
  GRUPO_ESTRANGEIRO: "border-[var(--danger-border)] bg-[var(--danger-soft)] text-[var(--danger-text)]",
  DESCONHECIDO: "border-line bg-subtle text-muted",
};

const ROTULOS_ORIGEM: Record<RankingFornecedor["nacional_estrangeiro"], string> = {
  NACIONAL: "Nacional",
  ESTRANGEIRO: "Estrangeiro",
  GRUPO_ESTRANGEIRO: "Subsidiária estrangeira",
  DESCONHECIDO: "Não classificado",
};


function RotuloOrigem({ origem }: { origem: RankingFornecedor["nacional_estrangeiro"] }) {
  return (
    <Badge variant="outline" className={ESTILOS_ORIGEM[origem]}>
      {ROTULOS_ORIGEM[origem]}
    </Badge>
  );
}


/** Texto longo (nome do fornecedor, sócio) quebra linha em vez de alargar a tabela. */
function TextoLongo({ valor }: { valor: string | null }) {
  return (
    <span className="block min-w-44 max-w-sm whitespace-normal">
      {valor ?? "—"}
    </span>
  );
}


export function Fornecedores() {
  const [anoMinimo, setAnoMinimo] = useState<number | null>(null);
  const [anoMaximo, setAnoMaximo] = useState<number | null>(null);
  const [anoDe, setAnoDe] = useState<number | null>(null);
  const [anoAte, setAnoAte] = useState<number | null>(null);

  const [carregandoIntervalo, setCarregandoIntervalo] = useState(true);
  const [falhaIntervalo, setFalhaIntervalo] = useState<unknown>(null);
  const [tentativaIntervalo, setTentativaIntervalo] = useState(0);

  const [ufFiltro, setUfFiltro] = useState("");

  const [dadosMapa, setDadosMapa] = useState<MapaFornecedorUf[]>([]);
  const [ranking, setRanking] = useState<RankingFornecedor[]>([]);

  const [carregandoMapa, setCarregandoMapa] = useState(true);
  const [carregandoRanking, setCarregandoRanking] = useState(true);
  // Falhas de requisição: guardam o erro real; cada tentativa refaz o efeito correspondente.
  const [falhaMapa, setFalhaMapa] = useState<unknown>(null);
  const [falhaRanking, setFalhaRanking] = useState<unknown>(null);
  const [tentativaMapa, setTentativaMapa] = useState(0);
  const [tentativaRanking, setTentativaRanking] = useState(0);

  const anos = useMemo(
    () =>
      anoMinimo != null && anoMaximo != null
        ? anosEntre(anoMinimo, anoMaximo)
        : [],
    [anoMinimo, anoMaximo],
  );

  // Busca o intervalo de anos disponível na montagem: a página abre carregada com ele
  // inteiro (2020–2025), sem exigir clique — Fornecedores não tem botão "Aplicar".
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
        }
      } catch (error) {
        if (ativo) setFalhaIntervalo(error);
      } finally {
        if (ativo) setCarregandoIntervalo(false);
      }
    }

    void carregarIntervalo();

    return () => {
      ativo = false;
    };
  }, [tentativaIntervalo]);

  useEffect(() => {
    if (anoDe == null || anoAte == null) return;

    let ativo = true;
    const { data_inicio, data_fim } = datasDoPeriodo(anoDe, anoAte);

    async function carregarMapa() {
      try {
        setCarregandoMapa(true);
        setFalhaMapa(null);
        const resposta = await buscarMapaFornecedoresPorUf(data_inicio, data_fim);
        if (ativo) setDadosMapa(resposta);
      } catch (error) {
        if (ativo) setFalhaMapa(error);
      } finally {
        if (ativo) setCarregandoMapa(false);
      }
    }

    void carregarMapa();

    return () => {
      ativo = false;
    };
  }, [anoDe, anoAte, tentativaMapa]);

  useEffect(() => {
    if (anoDe == null || anoAte == null) return;

    let ativo = true;
    const { data_inicio, data_fim } = datasDoPeriodo(anoDe, anoAte);

    async function carregarRanking() {
      try {
        setCarregandoRanking(true);
        setFalhaRanking(null);
        const resposta = await buscarRankingFornecedores(
          data_inicio,
          data_fim,
          ufFiltro || undefined,
          100,
        );
        if (ativo) setRanking(resposta);
      } catch (error) {
        if (ativo) setFalhaRanking(error);
      } finally {
        if (ativo) setCarregandoRanking(false);
      }
    }

    void carregarRanking();

    return () => {
      ativo = false;
    };
  }, [anoDe, anoAte, ufFiltro, tentativaRanking]);

  const dadosMapaFormatados: DadoMapaUf[] = useMemo(
    () =>
      dadosMapa.map((item) => ({
        uf: item.uf,
        valor: calcularPercentualEstrangeiro(item),
      })),
    [dadosMapa],
  );

  const resumoGeral = useMemo(() => {
    const totalNacional = dadosMapa.reduce(
      (acc, item) => acc + item.quantidade_nacional,
      0,
    );
    const totalEstrangeiroDireto = dadosMapa.reduce(
      (acc, item) => acc + item.quantidade_estrangeiro,
      0,
    );
    const totalGrupoEstrangeiro = dadosMapa.reduce(
      (acc, item) => acc + item.quantidade_grupo_estrangeiro,
      0,
    );
    const totalEstrangeiro = totalEstrangeiroDireto + totalGrupoEstrangeiro;
    const total = totalNacional + totalEstrangeiro;

    return {
      totalNacional,
      totalEstrangeiro,
      totalGrupoEstrangeiro,
      // Sem itens no período não há participação a calcular: "sem dado", não 0%.
      percentualEstrangeiro: total > 0 ? (totalEstrangeiro / total) * 100 : null,
    };
  }, [dadosMapa]);

  const colunas = useMemo<ColumnDef<RankingFornecedor, unknown>[]>(
    () => [
      {
        accessorKey: "fornecedor",
        header: "Fornecedor",
        cell: ({ getValue }) => <TextoLongo valor={getValue<string | null>()} />,
      },
      {
        accessorKey: "cnpj",
        header: "CNPJ",
        cell: ({ getValue }) => getValue<string | null>() ?? "—",
        meta: { priority: "low" },
      },
      {
        accessorKey: "nacional_estrangeiro",
        header: "Origem",
        cell: ({ getValue }) => (
          <RotuloOrigem
            origem={getValue<RankingFornecedor["nacional_estrangeiro"]>()}
          />
        ),
      },
      {
        accessorKey: "grupo_estrangeiro_socio",
        header: "Sócio no exterior",
        cell: ({ getValue }) => <TextoLongo valor={getValue<string | null>()} />,
        meta: { priority: "low" },
      },
      {
        accessorKey: "valor_total",
        header: "Valor total",
        cell: ({ getValue }) => moedaExata(getValue<number>()),
        meta: { align: "right" },
      },
      {
        accessorKey: "quantidade_itens",
        header: "Itens fornecidos",
        cell: ({ getValue }) => quantidade(getValue<number>()),
        meta: { align: "right" },
      },
      {
        accessorKey: "numero_compras",
        header: "Nº de compras",
        cell: ({ getValue }) => numeroExato(getValue<number>()),
        meta: { align: "right" },
      },
    ],
    [],
  );

  const semMapa = falhaMapa != null;

  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] space-y-6 px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <PageHeader
        icon="briefcase"
        title="Fornecedores"
        description="Distribuição de compras por origem do fornecedor (nacional ou estrangeiro), por estado."
      />

      <section
        aria-label="Filtros"
        className="grid grid-cols-1 gap-4 rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:flex sm:flex-wrap sm:items-end"
      >
        {anos.length > 0 && anoDe != null && anoAte != null ? (
          <PeriodoAnos
            id="fornecedores-periodo"
            anos={anos}
            de={anoDe}
            ate={anoAte}
            onChange={(de, ate) => {
              setAnoDe(de);
              setAnoAte(ate);
            }}
          />
        ) : (
          <Skeleton className="h-16 w-full max-w-sm" />
        )}
      </section>

      {falhaIntervalo != null && (
        <ErrorState
          error={falhaIntervalo}
          onRetry={() => setTentativaIntervalo((n) => n + 1)}
        />
      )}

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
        <KpiCard
          label="Itens de fornecedores nacionais"
          value={semMapa ? null : resumoGeral.totalNacional}
          format={numeroCompacto}
          loading={carregandoMapa}
        />

        <KpiCard
          label="Itens de fornecedores estrangeiros"
          value={semMapa ? null : resumoGeral.totalEstrangeiro}
          format={numeroCompacto}
          hint="Inclui subsidiárias de grupos estrangeiros."
          loading={carregandoMapa}
        />

        <KpiCard
          label="% estrangeiro (geral)"
          value={semMapa ? null : resumoGeral.percentualEstrangeiro}
          format={percentual}
          exact={percentual}
          loading={carregandoMapa}
        />
      </section>

      {carregandoMapa ? (
        <div aria-busy="true" className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
          <Skeleton className="h-6 w-72 max-w-full" />
          <Skeleton className="mt-5 h-[420px]" />
          <p className="sr-only">Carregando mapa...</p>
        </div>
      ) : falhaMapa != null ? (
        <ErrorState
          error={falhaMapa}
          onRetry={() => setTentativaMapa((n) => n + 1)}
        />
      ) : (
        <MapaBrasilUf
          dados={dadosMapaFormatados}
          titulo="Origem dos fornecedores por estado"
          descricao="Percentual de itens comprados de fornecedores estrangeiros, por UF da mantenedora compradora. Estados mais escuros têm maior participação de fornecedores estrangeiros. Clique numa UF para filtrar o ranking."
          tituloValor="% de itens estrangeiros"
          unidade="%"
          formatar={numeroUmaCasa}
          fonte={FONTE}
          ufFixada={ufFiltro || null}
          onFixarUf={(uf) => setUfFiltro(uf ?? "")}
        />
      )}

      <section>
        <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
          Ranking de fornecedores
        </h2>
        <p className="mt-1 text-sm leading-6 text-muted">
          100 maiores fornecedores no período, ordenados por valor total comprado.
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted">
          {ufFiltro ? (
            <>
              <span>
                Tabela filtrada por <strong className="text-[var(--text)]">{ufFiltro}</strong>
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setUfFiltro("")}
              >
                Limpar UF
              </Button>
            </>
          ) : (
            <span>Tabela: todas as UFs. Clique numa UF do mapa para filtrar.</span>
          )}
        </div>

        <div className="mt-3">
          {carregandoRanking ? (
            <div aria-busy="true" className="space-y-2">
              <Skeleton className="h-10" />
              {[1, 2, 3, 4, 5, 6].map((item) => (
                <Skeleton key={item} className="h-9" />
              ))}
            </div>
          ) : falhaRanking != null ? (
            <ErrorState
              error={falhaRanking}
              onRetry={() => setTentativaRanking((n) => n + 1)}
            />
          ) : ranking.length === 0 ? (
            <EmptyState
              title="Sem fornecedores no período"
              cause={
                ufFiltro
                  ? `Não há compras com fornecedor identificado em ${ufFiltro} entre as datas selecionadas.`
                  : "Não há compras com fornecedor identificado entre as datas selecionadas."
              }
            />
          ) : (
            <>
              <DataTable data={ranking} columns={colunas} pageSize={15} />
              <p className="mt-3 text-xs text-muted">
                Fonte: {FONTE}
              </p>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
