import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type MouseEvent,
} from "react";

import {
  geoMercator,
  geoPath,
} from "d3-geo";

import { assetUrl } from "../lib/base";
import { UiError } from "../lib/http";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ChartFrame } from "@/ui/ChartFrame";
import { ChoroplethLegend } from "@/ui/ChoroplethLegend";
import { ErrorState } from "@/ui/ErrorState";
import { escalaQuantis, type ClasseMapa } from "@/ui/escalaMapa";
import { sequencial } from "@/ui/chartTheme";
import { numeroExato } from "@/ui/format";

type Coordenadas =
  | number[]
  | Coordenadas[];


type Geometria = {
  type:
    | "Polygon"
    | "MultiPolygon";
  coordinates: Coordenadas;
};


type PropriedadesUf = {
  codigo?: string;
  sigla?: string;
  nome?: string;
  regiao?: string;
  area_km2?: number;
};


type FeatureUf = {
  type: "Feature";
  properties:
    PropriedadesUf;
  geometry:
    Geometria;
};


type FeatureCollectionUf = {
  type:
    "FeatureCollection";
  features:
    FeatureUf[];
};


/** `null` ou UF ausente de `dados` = sem registro (distinto de 0). */
export type DadoMapaUf = {
  uf: string;
  valor: number | null;
};


type MapaBrasilUfProps = {
  dados: DadoMapaUf[];
  titulo?: string;
  descricao?: string;
  tituloValor?: string;
  fonte?: string;
  /** "unidades", "leitos", "%"... Some depois do valor formatado. */
  unidade?: string;
  formatar?: (v: number) => string;
  /** Controlado (ex.: Fornecedores). Se `undefined`, o componente guarda estado interno. */
  ufFixada?: string | null;
  onFixarUf?: (uf: string | null) => void;
};


const LARGURA = 800;
const ALTURA = 720;


let geojsonCache:
  FeatureCollectionUf | null =
  null;

let geojsonPromise:
  Promise<FeatureCollectionUf>
  | null = null;


function valorSeguro(
  valor: number | null | undefined,
): number | null {
  if (valor == null) {
    return null;
  }

  const convertido = Number(valor);

  return Number.isFinite(convertido)
    ? convertido
    : null;
}


async function obterGeojson():
Promise<FeatureCollectionUf> {
  if (geojsonCache) {
    return geojsonCache;
  }

  if (!geojsonPromise) {
    geojsonPromise =
      fetch(
        assetUrl("maps/brasil-ufs.geojson"),
      )
        .then(
          async (response) => {
            if (!response.ok) {
              throw new UiError(
                `Não foi possível carregar o mapa (${response.status}).`,
              );
            }

            return (
              await response.json()
            ) as FeatureCollectionUf;
          },
        )
        .then(
          (dados) => {
            if (
              dados.type
                !== "FeatureCollection"
              || !Array.isArray(
                dados.features,
              )
            ) {
              throw new UiError(
                "O arquivo GeoJSON do mapa não possui o formato esperado.",
              );
            }

            geojsonCache =
              dados;

            return dados;
          },
        )
        .catch(
          (error) => {
            geojsonPromise =
              null;

            throw error;
          },
        );
  }

  return geojsonPromise;
}


type EstadoCaminho = {
  id: string;
  sigla: string;
  nome: string;
  valor: number | null;
  classe: ClasseMapa;
  d: string;
};


function rotuloAria(
  estado: EstadoCaminho,
  unidade: string,
  formatar: (v: number) => string,
): string {
  const base =
    estado.sigla
      ? `${estado.nome} (${estado.sigla})`
      : estado.nome;

  if (estado.classe.tipo === "sem-registro") {
    return `${base}: sem registro`;
  }

  const valor = estado.classe.tipo === "zero" ? 0 : (estado.valor ?? 0);

  return `${base}: ${formatar(valor)} ${unidade}`;
}


export function MapaBrasilUf({
  dados,
  titulo = "Mapa do Brasil",
  descricao = "Distribuição por Unidade Federativa.",
  tituloValor = "Valor",
  fonte = "DATASUS",
  unidade = "valor",
  formatar = numeroExato,
  ufFixada,
  onFixarUf,
}: MapaBrasilUfProps) {
  const idBase = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const idPatternSemRegistro = `${idBase}-sem-registro`;

  const containerRef = useRef<HTMLDivElement | null>(null);

  const [
    geojson,
    setGeojson,
  ] =
    useState<
      FeatureCollectionUf | null
    >(
      geojsonCache,
    );

  const [
    carregando,
    setCarregando,
  ] =
    useState(
      !geojsonCache,
    );

  // Falha ao baixar o GeoJSON: guarda o erro real; a tentativa refaz o efeito de carga.
  const [
    erro,
    setErro,
  ] =
    useState<unknown>(null);

  const [
    tentativa,
    setTentativa,
  ] = useState(0);

  const [estadoHover, setEstadoHover] = useState<string | null>(null);
  const [fixadaInterna, setFixadaInterna] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ sigla: string; x: number; y: number } | null>(null);

  const fixada = ufFixada !== undefined ? ufFixada : fixadaInterna;

  function fixar(nova: string | null) {
    if (ufFixada === undefined) {
      setFixadaInterna(nova);
    }
    onFixarUf?.(nova);
  }

  function alternarFixacao(sigla: string) {
    fixar(fixada === sigla ? null : sigla);
  }


  useEffect(
    () => {
      let ativo = true;

      if (geojsonCache) {
        setGeojson(
          geojsonCache,
        );
        setCarregando(
          false,
        );
        return;
      }

      async function carregarMapa() {
        try {
          setCarregando(true);
          setErro(null);

          const resposta =
            await obterGeojson();

          if (ativo) {
            setGeojson(
              resposta,
            );
          }
        } catch (error) {
          if (!ativo) {
            return;
          }

          setErro(error);
        } finally {
          if (ativo) {
            setCarregando(
              false,
            );
          }
        }
      }

      void carregarMapa();

      return () => {
        ativo = false;
      };
    },
    [tentativa],
  );


  const dadosPorUf =
    useMemo(
      () => {
        const mapa =
          new Map<
            string,
            number | null
          >();

        dados.forEach(
          (item) => {
            mapa.set(
              item.uf
                .trim()
                .toUpperCase(),
              valorSeguro(
                item.valor,
              ),
            );
          },
        );

        return mapa;
      },
      [dados],
    );


  // Quantis calculados sobre todas as UFs do mapa (não só as presentes em `dados`): uma UF do
  // GeoJSON ausente de `dados` entra como `null` (sem registro), igual a uma UF presente com
  // `valor: null`.
  const escala =
    useMemo(
      () => {
        if (!geojson) {
          return escalaQuantis([]);
        }

        const valores = geojson.features.map((feature) => {
          const sigla = (feature.properties.sigla ?? "").trim().toUpperCase();
          return dadosPorUf.get(sigla) ?? null;
        });

        return escalaQuantis(valores);
      },
      [geojson, dadosPorUf],
    );

  const cores = useMemo(() => sequencial(), []);


  const caminhos: EstadoCaminho[] =
    useMemo(
      () => {
        if (!geojson) {
          return [];
        }

        const projection =
          geoMercator()
            .fitSize(
              [
                LARGURA,
                ALTURA,
              ],
              geojson as never,
            );

        const path =
          geoPath(
            projection,
          );

        return geojson.features.map(
          (
            feature,
            indice,
          ) => {
            const sigla =
              (
                feature.properties
                  .sigla
                ?? ""
              )
                .trim()
                .toUpperCase();

            const valor =
              dadosPorUf.get(
                sigla,
              )
              ?? null;

            return {
              id:
                sigla
                || String(
                  indice,
                ),

              sigla,

              nome:
                feature.properties
                  .nome
                ?? sigla
                ?? "UF",

              valor,

              classe: escala.classeDe(valor),

              d:
                path(
                  feature as never,
                )
                ?? "",
            };
          },
        );
      },
      [
        geojson,
        dadosPorUf,
        escala,
      ],
    );

  const caminhoPorSigla = useMemo(
    () => new Map(caminhos.map((estado) => [estado.sigla, estado])),
    [caminhos],
  );

  // "0" e "sem registro" não são "maiores": só faixas de valor positivo entram na lista.
  const cincoMaiores = useMemo(
    () =>
      [...caminhos]
        .filter((estado) => estado.classe.tipo === "faixa")
        .sort((a, b) => (b.valor ?? 0) - (a.valor ?? 0))
        .slice(0, 5),
    [caminhos],
  );

  const siglaAtiva = estadoHover ?? fixada;
  const estadoAtivo = siglaAtiva ? caminhoPorSigla.get(siglaAtiva) ?? null : null;
  const estadoFixado = fixada ? caminhoPorSigla.get(fixada) ?? null : null;
  const estadoHoverObj = estadoHover && estadoHover !== fixada ? caminhoPorSigla.get(estadoHover) ?? null : null;
  const estadoTooltip = tooltip ? caminhoPorSigla.get(tooltip.sigla) ?? null : null;

  function corDe(classe: ClasseMapa): string {
    if (classe.tipo === "sem-registro") return `url(#${idPatternSemRegistro})`;
    if (classe.tipo === "zero") return "var(--beast-basic-300)";
    return cores[classe.indice] ?? cores.at(-1) ?? "var(--beast-basic-300)";
  }

  function onMouseMove(evento: MouseEvent<SVGPathElement>, sigla: string) {
    const rect = containerRef.current?.getBoundingClientRect();
    setTooltip({
      sigla,
      x: evento.clientX - (rect?.left ?? 0),
      y: evento.clientY - (rect?.top ?? 0),
    });
  }

  function onKeyDownPath(evento: KeyboardEvent<SVGPathElement>, sigla: string) {
    if (evento.key === "Enter" || evento.key === " " || evento.key === "Spacebar") {
      evento.preventDefault();
      alternarFixacao(sigla);
    }
  }

  // No nível do contêiner (não só no path focado): Escape limpa a UF fixada onde quer que o
  // foco esteja dentro do mapa (um path, o botão "Limpar seleção", um item de "5 maiores"...).
  function onKeyDownContainer(evento: KeyboardEvent<HTMLDivElement>) {
    if (evento.key === "Escape") {
      fixar(null);
    }
  }


  if (carregando) {
    return (
      <div aria-busy="true" className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
        <Skeleton className="h-6 w-64 max-w-full" />
        <Skeleton className="mt-5 h-[420px]" />
        <p className="sr-only">Carregando mapa do Brasil...</p>
      </div>
    );
  }


  if (erro != null) {
    return (
      <ErrorState
        error={erro}
        onRetry={() => setTentativa((n) => n + 1)}
      />
    );
  }


  return (
    <ChartFrame
      title={titulo}
      subtitle={descricao}
      source={fonte}
    >
      <div
        className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_220px]"
        onKeyDown={onKeyDownContainer}
      >
        <div ref={containerRef} className="relative mx-auto w-full max-w-4xl">
          <svg
            viewBox={`0 0 ${LARGURA} ${ALTURA}`}
            role="group"
            aria-label={`Mapa do Brasil: ${titulo}`}
            className="h-auto w-full"
          >
            {/* Mesma proporção da hachura CSS da legenda (.hachura-sem-registro no index.css):
                3px claro (basic-200) + 1px escuro (basic-600) a cada 4px, a 45°. */}
            <defs>
              <pattern
                id={idPatternSemRegistro}
                width={4}
                height={4}
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <rect width={4} height={4} fill="var(--beast-basic-200)" />
                <rect x={3} width={1} height={4} fill="var(--beast-basic-600)" />
              </pattern>
            </defs>

            {caminhos.map((estado) => (
              <path
                key={estado.id}
                d={estado.d}
                fill={corDe(estado.classe)}
                vectorEffect="non-scaling-stroke"
                className="cursor-pointer"
                style={{ outline: "none" }}
                tabIndex={0}
                role="button"
                aria-pressed={fixada === estado.sigla}
                aria-label={rotuloAria(estado, unidade, formatar)}
                onMouseEnter={() => setEstadoHover(estado.sigla)}
                onMouseMove={(evento) => onMouseMove(evento, estado.sigla)}
                onMouseLeave={() => {
                  setEstadoHover(null);
                  setTooltip(null);
                }}
                onFocus={() => setEstadoHover(estado.sigla)}
                onBlur={() => setEstadoHover(null)}
                onClick={() => alternarFixacao(estado.sigla)}
                onKeyDown={(evento) => onKeyDownPath(evento, estado.sigla)}
              />
            ))}

            {estadoFixado ? (
              <path
                d={estadoFixado.d}
                fill="none"
                stroke="var(--focus-ring)"
                strokeWidth={3}
                pointerEvents="none"
                aria-hidden="true"
              />
            ) : null}

            {estadoHoverObj ? (
              <path
                d={estadoHoverObj.d}
                fill="none"
                stroke="var(--text)"
                strokeWidth={3}
                pointerEvents="none"
                aria-hidden="true"
              />
            ) : null}
          </svg>

          {tooltip && estadoTooltip ? (
            <div
              aria-hidden="true"
              className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-[var(--radius-md)] border border-line bg-panel px-2 py-1 text-xs whitespace-nowrap text-[var(--text)] shadow-[var(--shadow-card)]"
              style={{ left: tooltip.x, top: tooltip.y - 8 }}
            >
              {(() => {
                const base = estadoTooltip.sigla ? `${estadoTooltip.nome} (${estadoTooltip.sigla})` : estadoTooltip.nome;
                const valorTexto =
                  estadoTooltip.classe.tipo === "sem-registro"
                    ? "sem registro"
                    : `${formatar(estadoTooltip.classe.tipo === "zero" ? 0 : (estadoTooltip.valor ?? 0))} ${unidade}`;
                return `${base}: ${valorTexto}`;
              })()}
            </div>
          ) : null}
        </div>


        <aside aria-live="polite" className="self-start rounded-[var(--radius-md)] border border-line bg-surface p-4">
          <p className="text-xs font-semibold text-muted">
            Estado
          </p>

          {estadoAtivo ? (
            <>
              <p className="mt-2 text-lg font-semibold text-[var(--text)]">
                {estadoAtivo.nome}
              </p>

              <p className="mt-1 text-sm text-muted">
                {estadoAtivo.sigla}
              </p>

              <div className="mt-5">
                <p className="text-xs font-medium text-muted">
                  {tituloValor}
                </p>

                <p className="mt-1 text-2xl font-bold tabular-nums tracking-tight text-primary">
                  {estadoAtivo.classe.tipo === "sem-registro"
                    ? "sem registro"
                    : `${formatar(estadoAtivo.classe.tipo === "zero" ? 0 : (estadoAtivo.valor ?? 0))} ${unidade}`}
                </p>
              </div>

              {fixada === estadoAtivo.sigla ? (
                <Button
                  variant="ghost"
                  className="mt-4"
                  onClick={() => fixar(null)}
                >
                  Limpar seleção
                </Button>
              ) : null}
            </>
          ) : (
            <>
              <p className="mt-2 text-sm font-semibold text-[var(--text)]">
                5 maiores
              </p>

              {cincoMaiores.length > 0 ? (
                <ol className="mt-2 flex flex-col gap-1">
                  {cincoMaiores.map((estado) => (
                    <li key={estado.id}>
                      <Button
                        variant="ghost"
                        className="w-full justify-between px-2"
                        onClick={() => alternarFixacao(estado.sigla)}
                      >
                        <span className="truncate">{estado.nome}</span>
                        <span className="tabular-nums">{formatar(estado.valor ?? 0)}</span>
                      </Button>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="mt-2 text-sm text-muted">Nenhuma UF com valor</p>
              )}
            </>
          )}
        </aside>
      </div>


      <div className="mt-5">
        <ChoroplethLegend
          escala={escala}
          cores={cores}
          unidade={unidade}
          formatar={formatar}
        />
      </div>
    </ChartFrame>
  );
}
