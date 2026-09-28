import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  geoMercator,
  geoPath,
} from "d3-geo";

import { assetUrl } from "../lib/base";
import { Skeleton } from "@/components/ui/skeleton";
import { ChartFrame } from "@/ui/ChartFrame";
import { ErrorState } from "@/ui/ErrorState";
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


export type DadoMapaUf = {
  uf: string;
  valor: number;
};


type MapaBrasilUfProps = {
  dados: DadoMapaUf[];
  titulo?: string;
  descricao?: string;
  tituloValor?: string;
  fonte?: string;
};


const LARGURA = 800;
const ALTURA = 720;


let geojsonCache:
  FeatureCollectionUf | null =
  null;

let geojsonPromise:
  Promise<FeatureCollectionUf>
  | null = null;


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
              throw new Error(
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
              throw new Error(
                "O arquivo GeoJSON não possui o formato esperado.",
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


export function MapaBrasilUf({
  dados,
  titulo = "Mapa do Brasil",
  descricao = "Distribuição por Unidade Federativa.",
  tituloValor = "Valor",
  fonte = "DATASUS",
}: MapaBrasilUfProps) {
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

  // Resolve a escala sequencial uma vez por montagem (lê as variáveis CSS do documento).
  const escala =
    useMemo(
      () => sequencial(),
      [],
    );

  const [
    estadoAtivo,
    setEstadoAtivo,
  ] =
    useState<
      string | null
    >(null);


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
            number
          >();

        dados.forEach(
          (item) => {
            mapa.set(
              item.uf
                .trim()
                .toUpperCase(),
              numero(
                item.valor,
              ),
            );
          },
        );

        return mapa;
      },
      [dados],
    );


  const maiorValor =
    useMemo(
      () =>
        Math.max(
          0,
          ...Array.from(
            dadosPorUf.values(),
          ),
        ),
      [dadosPorUf],
    );


  const caminhos =
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
              ?? 0;

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

              opacidade:
                0.14
                + 0.86
                * (
                  valor
                  / (maiorValor || 1)
                ),

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
        maiorValor,
      ],
    );


  const estadoSelecionado =
    useMemo(
      () =>
        caminhos.find(
          (estado) =>
            estado.id
            === estadoAtivo,
        )
        ?? null,
      [
        caminhos,
        estadoAtivo,
      ],
    );


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
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_220px]">
        <div className="mx-auto w-full max-w-4xl">
          <svg
            viewBox={`0 0 ${LARGURA} ${ALTURA}`}
            role="img"
            aria-label="Mapa do Brasil dividido por Unidades Federativas"
            className="h-auto w-full"
          >
            {caminhos.map((estado) => (
              <path
                key={estado.id}
                d={estado.d}
                fill={escala.at(-1)}
                fillOpacity={estado.opacidade}
                stroke={estadoAtivo === estado.id ? "var(--text)" : "var(--panel)"}
                strokeWidth={estadoAtivo === estado.id ? 2 : 1}
                vectorEffect="non-scaling-stroke"
                className="cursor-pointer"
                onMouseEnter={() => setEstadoAtivo(estado.id)}
                onMouseLeave={() => setEstadoAtivo(null)}
              >
                <title>
                  {estado.nome}
                  {estado.sigla ? ` (${estado.sigla})` : ""}
                  {` — ${tituloValor}: ${numeroExato(estado.valor)}`}
                </title>
              </path>
            ))}
          </svg>
        </div>


        <aside className="self-start rounded-[var(--radius-md)] border border-line bg-surface p-4">
          <p className="text-xs font-semibold text-muted">
            Estado
          </p>

          {estadoSelecionado ? (
            <>
              <p className="mt-2 text-lg font-semibold text-[var(--text)]">
                {estadoSelecionado.nome}
              </p>

              <p className="mt-1 text-sm text-muted">
                {estadoSelecionado.sigla}
              </p>

              <div className="mt-5">
                <p className="text-xs font-medium text-muted">
                  {tituloValor}
                </p>

                <p className="mt-1 text-2xl font-bold tabular-nums tracking-tight text-primary">
                  {numeroExato(estadoSelecionado.valor)}
                </p>
              </div>
            </>
          ) : (
            <p className="mt-2 text-sm leading-6 text-muted">
              Passe o mouse sobre uma UF para ver o valor.
            </p>
          )}
        </aside>
      </div>


      <div className="mt-5">
        <div
          aria-hidden="true"
          className="h-2 w-full rounded-full"
          style={{
            background:
              `linear-gradient(to right, ${escala[0]}, ${escala.at(-1)})`,
          }}
        />

        <div className="mt-2 flex items-center justify-between gap-4 text-xs tabular-nums text-muted">
          <span>0</span>
          <span>{numeroExato(maiorValor)}</span>
        </div>
      </div>
    </ChartFrame>
  );
}
