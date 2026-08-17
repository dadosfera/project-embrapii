import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  geoMercator,
  geoPath,
} from "d3-geo";

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
};


const LARGURA = 800;
const ALTURA = 720;


const formatadorNumero =
  new Intl.NumberFormat(
    "pt-BR",
    {
      maximumFractionDigits: 0,
    },
  );


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
        "/maps/brasil-ufs.geojson",
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

  const [
    erro,
    setErro,
  ] =
    useState<
      string | null
    >(null);

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

          setErro(
            error
              instanceof Error
              ? error.message
              : "Não foi possível carregar o mapa do Brasil.",
          );
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
    [],
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
      <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-teal-700">
          Carregando mapa do Brasil...
        </p>
      </div>
    );
  }


  if (erro) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm leading-6 text-red-800">
        {erro}
      </div>
    );
  }


  return (
    <section className="rounded-2xl border border-teal-100 bg-white p-4 shadow-sm sm:p-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          {titulo}
        </h2>

        <p className="mt-1 text-sm leading-6 text-slate-500">
          {descricao}
        </p>
      </div>


      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_220px]">
        <div className="mx-auto w-full max-w-4xl">
          <svg
            viewBox={`0 0 ${LARGURA} ${ALTURA}`}
            role="img"
            aria-label="Mapa do Brasil dividido por Unidades Federativas"
            className="h-auto w-full"
          >
            {caminhos.map(
              (estado) => (
                <path
                  key={
                    estado.id
                  }
                  d={
                    estado.d
                  }
                  fill="var(--color-brand-blue)"
                  fillOpacity={estado.opacidade}
                  stroke="var(--panel)"
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                  className="cursor-pointer"
                  onMouseEnter={() =>
                    setEstadoAtivo(
                      estado.id,
                    )
                  }
                  onMouseLeave={() =>
                    setEstadoAtivo(
                      null,
                    )
                  }
                >
                  <title>
                    {estado.nome}
                    {estado.sigla
                      ? ` (${estado.sigla})`
                      : ""}
                    {` — ${tituloValor}: ${formatadorNumero.format(
                      estado.valor,
                    )}`}
                  </title>
                </path>
              ),
            )}
          </svg>
        </div>


        <aside className="rounded-xl border border-teal-100 bg-teal-50/50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-teal-700">
            Estado
          </p>

          {estadoSelecionado ? (
            <>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {estadoSelecionado.nome}
              </p>

              <p className="mt-1 text-sm text-slate-500">
                {estadoSelecionado.sigla}
              </p>

              <div className="mt-5">
                <p className="text-xs font-medium text-slate-500">
                  {tituloValor}
                </p>

                <p className="mt-1 text-2xl font-semibold tracking-tight text-teal-800">
                  {formatadorNumero.format(
                    estadoSelecionado.valor,
                  )}
                </p>
              </div>
            </>
          ) : (
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Passe o mouse sobre uma UF para ver o valor.
            </p>
          )}
        </aside>
      </div>


      <div className="mt-5">
        <div
          className="h-2 w-full rounded-full"
          style={{
            background:
              "linear-gradient(to right, color-mix(in srgb, var(--color-brand-blue) 14%, var(--panel)), var(--color-brand-blue))",
          }}
        />

        <div className="mt-2 flex items-center justify-between gap-4 text-xs text-slate-500">
          <span>
            0
          </span>

          <span>
            {formatadorNumero.format(
              maiorValor,
            )}
          </span>
        </div>
      </div>
    </section>
  );
}
