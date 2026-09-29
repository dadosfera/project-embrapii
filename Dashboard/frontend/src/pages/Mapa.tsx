import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useSearchParams } from "react-router";

import type {
  ColumnDef,
} from "@tanstack/react-table";

import {
  DataTable,
} from "../components/DataTable";

import { CatmatPicker } from "../components/CatmatPicker";
import { BotaoAplicar } from "@/ui/BotaoAplicar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/ui/EmptyState";
import { ErrorState } from "@/ui/ErrorState";
import { Icon } from "@/ui/Icon";
import { PageHeader } from "@/ui/PageHeader";
import { numeroExato, numeroUmaCasa, quantidade } from "@/ui/format";

import {
  MapaBrasilUf,
  type DadoMapaUf,
} from "../components/MapaBrasil";

import {
  buscarEstoquePorUf,
  buscarLeitosPorUf,
  buscarGrupoCatmat,
  type CatmatItem,
  type GrupoCatmat,
  type EstoqueUf,
  type LeitosPorUf,
  type ModoLeitos,
} from "../lib/api";

import {
  normalizarEstoque,
  normalizarLeitos,
  ordenarNulosPorUltimo,
  type LinhaEstoque,
  type LinhaLeitos,
} from "./mapaDados";


type AbaMapa =
  | "estoque"
  | "leitos";


type MetricaLeitos =
  | "percentual_sus"
  | "leitos_gerais"
  | "leitos_sus"
  | "leitos_uti"
  | "leitos_uti_sus";


/** "sem registro" (não "sem dado"): mesma linguagem do mapa para UF ausente. */
function numeroExatoCel(v: number | null): string {
  return v == null ? "sem registro" : numeroExato(v);
}

function quantidadeCel(v: number | null): string {
  return v == null ? "sem registro" : quantidade(v);
}

/** Participação com uma casa ("12,3%"), igual a `Fornecedores.tsx`. */
function percentualUmaCasa(v: number): string {
  return `${numeroUmaCasa(v)}%`;
}

function percentualCel(v: number | null): string {
  return v == null ? "sem registro" : percentualUmaCasa(v);
}


const ROTULOS_METRICA:
  Record<
    MetricaLeitos,
    string
  > = {
    percentual_sus:
      "Participação do SUS (%)",

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


const AVISO =
  "flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text";


export function Mapa() {
  const [aba, setAba] = useState<AbaMapa>("estoque");


  // =========================================
  // ESTOQUE
  // =========================================

  // Medicamento na URL (?catmat=<código-base>), igual à página Medicamentos.
  const [searchParams, setSearchParams] = useSearchParams();
  const chaveUrl = searchParams.get("catmat");
  const [grupo, setGrupo] = useState<GrupoCatmat | null>(null);
  const [carregandoEstoque, setCarregandoEstoque] = useState(false);
  const [estoqueBruto, setEstoqueBruto] = useState<EstoqueUf[] | null>(null);
  const [catmatAplicado, setCatmatAplicado] = useState<CatmatItem | null>(null);
  // Mensagens da página (validação, busca sem resultado): aviso inline.
  const [erroEstoque, setErroEstoque] = useState<string | null>(null);
  // Falhas de requisição: guardam o erro real para o ErrorState.
  const [falhaEstoque, setFalhaEstoque] = useState<unknown>(null);


  // =========================================
  // LEITOS
  // =========================================

  const [modoLeitos, setModoLeitos] = useState<ModoLeitos>("ultima_competencia");
  const [modoLeitosAplicado, setModoLeitosAplicado] = useState<ModoLeitos | null>(null);
  const [metricaLeitos, setMetricaLeitos] = useState<MetricaLeitos>("percentual_sus");
  const [carregandoLeitos, setCarregandoLeitos] = useState(false);
  const [leitosBruto, setLeitosBruto] = useState<LeitosPorUf[] | null>(null);
  const [falhaLeitos, setFalhaLeitos] = useState<unknown>(null);


  // Cache de consultas enquanto a rota permanecer aberta.
  const cacheEstoque = useRef(new Map<string, EstoqueUf[]>());
  const cacheLeitos = useRef(new Map<ModoLeitos, LeitosPorUf[]>());

  const pedidoEstoque = useRef(0);


  function selecionarGrupo(novo: GrupoCatmat | null) {
    if (novo) setGrupo(novo);
    setSearchParams(novo ? { catmat: novo.base } : {});
  }


  useEffect(() => {
    if (!chaveUrl) {
      setGrupo(null);
      return;
    }
    if (grupo?.base === chaveUrl) return;
    let vivo = true;
    buscarGrupoCatmat(chaveUrl)
      .then((g) => vivo && setGrupo(g))
      .catch(() => vivo && setErroEstoque(`O código CATMAT ${chaveUrl} não existe no catálogo.`));
    return () => {
      vivo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveUrl]);


  useEffect(() => {
    if (grupo) {
      void buscarMapaEstoque(grupo);
    } else {
      pedidoEstoque.current++;
      setEstoqueBruto(null);
      setCatmatAplicado(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grupo]);


  // Soma todas as variantes do item-base (escopo grupo), como em Medicamentos.
  async function buscarMapaEstoque(g: GrupoCatmat) {
    const meu = ++pedidoEstoque.current;
    setCarregandoEstoque(true);
    setErroEstoque(null);
    setFalhaEstoque(null);

    try {
      const armazenado = cacheEstoque.current.get(g.base);
      const resposta = armazenado ?? await buscarEstoquePorUf(g.catmat_id, "grupo");
      if (meu !== pedidoEstoque.current) return;

      if (!armazenado) {
        cacheEstoque.current.set(g.base, resposta);
      }

      setEstoqueBruto(resposta);
      setCatmatAplicado({ catmat_id: g.catmat_id, codigo_catmat: g.base, descricao_catmat: g.nome } as CatmatItem);
    } catch (error) {
      if (meu === pedidoEstoque.current) setFalhaEstoque(error);
    } finally {
      if (meu === pedidoEstoque.current) setCarregandoEstoque(false);
    }
  }


  async function buscarMapaLeitos() {
    setCarregandoLeitos(true);
    setFalhaLeitos(null);

    try {
      const armazenado = cacheLeitos.current.get(modoLeitos);
      const resposta = armazenado ?? await buscarLeitosPorUf({ modo: modoLeitos, uf: "" });

      if (!armazenado) {
        cacheLeitos.current.set(modoLeitos, resposta);
      }

      setLeitosBruto(resposta);
      setModoLeitosAplicado(modoLeitos);
    } catch (error) {
      setFalhaLeitos(error);
    } finally {
      setCarregandoLeitos(false);
    }
  }


  // Aba Leitos: carrega ao abrir, com o modo padrão, sem exigir clique.
  useEffect(() => {
    if (aba === "leitos" && !leitosBruto && !carregandoLeitos && falhaLeitos == null) {
      void buscarMapaLeitos();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aba, leitosBruto, carregandoLeitos, falhaLeitos]);


  const estoqueNormalizado = useMemo(
    () => (estoqueBruto ? normalizarEstoque(estoqueBruto) : []),
    [estoqueBruto],
  );

  const dadosMapaEstoque = useMemo<DadoMapaUf[]>(
    () => estoqueNormalizado.map((item) => ({ uf: item.uf, valor: item.estoque_total })),
    [estoqueNormalizado],
  );

  const estoqueTabela = useMemo(
    () => ordenarNulosPorUltimo(estoqueNormalizado, (item) => item.estoque_total),
    [estoqueNormalizado],
  );

  const leitosNormalizado = useMemo(
    () => (leitosBruto ? normalizarLeitos(leitosBruto) : []),
    [leitosBruto],
  );

  const dadosMapaLeitos = useMemo<DadoMapaUf[]>(
    () => leitosNormalizado.map((item) => ({ uf: item.uf, valor: item[metricaLeitos] })),
    [leitosNormalizado, metricaLeitos],
  );

  const leitosTabela = useMemo(
    () => ordenarNulosPorUltimo(leitosNormalizado, (item) => item[metricaLeitos]),
    [leitosNormalizado, metricaLeitos],
  );

  const unidadeLeitos = metricaLeitos === "percentual_sus" ? "%" : "leitos";
  const formatarLeitos = metricaLeitos === "percentual_sus" ? numeroUmaCasa : numeroExato;


  const colunasEstoque = useMemo<ColumnDef<LinhaEstoque, unknown>[]>(
    () => [
      { header: "UF", accessorKey: "uf" },
      {
        header: "Estoque",
        accessorKey: "estoque_total",
        cell: ({ row }) => quantidadeCel(row.original.estoque_total),
        meta: { align: "right" },
      },
      {
        header: "Instituições",
        accessorKey: "num_instituicoes",
        cell: ({ row }) => numeroExatoCel(row.original.num_instituicoes),
        meta: { align: "right" },
      },
    ],
    [],
  );


  const colunasLeitos = useMemo<ColumnDef<LinhaLeitos, unknown>[]>(
    () => [
      { header: "UF", accessorKey: "uf" },
      {
        header: "Leitos gerais",
        accessorKey: "leitos_gerais",
        cell: ({ row }) => numeroExatoCel(row.original.leitos_gerais),
        meta: { align: "right" },
      },
      {
        header: "Leitos SUS",
        accessorKey: "leitos_sus",
        cell: ({ row }) => numeroExatoCel(row.original.leitos_sus),
        meta: { align: "right" },
      },
      {
        header: "Leitos SUS (%)",
        accessorKey: "percentual_sus",
        cell: ({ row }) => percentualCel(row.original.percentual_sus),
        meta: { align: "right" },
      },
      {
        header: "Leitos de UTI",
        accessorKey: "leitos_uti",
        cell: ({ row }) => numeroExatoCel(row.original.leitos_uti),
        meta: { align: "right" },
      },
      {
        header: "Leitos de UTI SUS",
        accessorKey: "leitos_uti_sus",
        cell: ({ row }) => numeroExatoCel(row.original.leitos_uti_sus),
        meta: { align: "right" },
      },
      {
        header: "Instituições",
        accessorKey: "instituicoes",
        cell: ({ row }) => numeroExatoCel(row.original.instituicoes),
        meta: { align: "right" },
      },
    ],
    [],
  );


  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <PageHeader
        icon="map"
        title="Mapa do Brasil"
        description="Explore diferentes indicadores de saúde por Unidade Federativa."
      />


      <Tabs
        value={aba}
        onValueChange={(valor) => setAba(valor as AbaMapa)}
        className="mt-7"
      >
        <TabsList
          aria-label="Análises geográficas"
          className="w-full flex-wrap justify-start group-data-[orientation=horizontal]/tabs:h-auto sm:w-fit sm:flex-nowrap sm:group-data-[orientation=horizontal]/tabs:h-9"
        >
          <TabsTrigger value="estoque" className="min-h-8 px-4 sm:flex-none">
            Estoque por estado
          </TabsTrigger>

          <TabsTrigger value="leitos" className="min-h-8 px-4 sm:flex-none">
            Leitos por estado
          </TabsTrigger>
        </TabsList>


        <TabsContent value="estoque" className="mt-3">
          <div className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--text)]">
                Estoque de medicamento por estado
              </h2>

              <p className="mt-1 text-sm leading-6 text-muted">
                Escolha um medicamento: o mapa soma o estoque de todos os códigos do item (apresentações e componentes do BNAFAR).
              </p>
            </div>


            <CatmatPicker
              id="mapa-busca-catmat"
              label="Medicamento / CATMAT"
              value={grupo}
              onSelect={selecionarGrupo}
              className="mt-5"
            />


            {erroEstoque && (
              <div role="status" className={`mt-4 ${AVISO}`}>
                <Icon name="alert" size={18} className="mt-0.5" />
                {erroEstoque}
              </div>
            )}
          </div>


          {falhaEstoque != null && (
            <div className="mt-5">
              <ErrorState
                error={falhaEstoque}
                onRetry={grupo ? () => void buscarMapaEstoque(grupo) : undefined}
              />
            </div>
          )}


          {carregandoEstoque && (
            <Skeleton aria-busy="true" className="mt-5 h-[520px]" />
          )}


          {estoqueBruto
            && !carregandoEstoque
            && catmatAplicado
            && (
              estoqueBruto.length > 0 ? (
                <div className="mt-5 space-y-6">
                  <MapaBrasilUf
                    dados={dadosMapaEstoque}
                    titulo="Estoque por Unidade Federativa"
                    descricao={`${
                      catmatAplicado.descricao_catmat ?? "Medicamento selecionado"
                    } — CATMAT ${catmatAplicado.codigo_catmat ?? "N/I"}`}
                    tituloValor="Estoque"
                    unidade="unidades"
                    formatar={quantidade}
                  />


                  <section>
                    <div className="mb-4">
                      <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                        Dados por Unidade Federativa
                      </h2>

                      <p className="mt-1 text-sm leading-6 text-muted">
                        UFs sem registro aparecem hachuradas no mapa e como "sem registro" na tabela; 0 indica registro com estoque zerado.
                      </p>
                    </div>

                    <DataTable
                      data={estoqueTabela}
                      columns={colunasEstoque}
                      pageSize={27}
                    />
                  </section>
                </div>
              ) : (
                <div className="mt-5">
                  <EmptyState
                    title="Sem estoque por UF"
                    cause="Nenhuma instituição registrou estoque deste medicamento."
                  />
                </div>
              )
            )}
        </TabsContent>


        <TabsContent value="leitos" className="mt-3">
          <div className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--text)]">
                Disponibilidade de leitos por estado
              </h2>

              <p className="mt-1 text-sm leading-6 text-muted">
                A base é aplicada com o botão Aplicar; a métrica muda o mapa na hora.
              </p>
            </div>


            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="min-w-0">
                <label
                  htmlFor="mapa-modo-leitos"
                  className="block text-sm font-semibold text-[var(--text)]"
                >
                  Base utilizada
                </label>

                <Select
                  value={modoLeitos}
                  onValueChange={(valor) => setModoLeitos(valor as ModoLeitos)}
                >
                  <SelectTrigger
                    id="mapa-modo-leitos"
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
              </div>


              <div className="min-w-0">
                <label
                  htmlFor="mapa-metrica-leitos"
                  className="block text-sm font-semibold text-[var(--text)]"
                >
                  Métrica exibida no mapa
                </label>

                <Select
                  value={metricaLeitos}
                  onValueChange={(valor) => setMetricaLeitos(valor as MetricaLeitos)}
                >
                  <SelectTrigger
                    id="mapa-metrica-leitos"
                    className="mt-2 h-10 w-full min-w-0 bg-panel data-[size=default]:h-10"
                  >
                    <SelectValue />
                  </SelectTrigger>

                  <SelectContent position="popper">
                    <SelectItem value="percentual_sus">Participação do SUS (%)</SelectItem>
                    <SelectItem value="leitos_gerais">Leitos gerais</SelectItem>
                    <SelectItem value="leitos_sus">Leitos SUS</SelectItem>
                    <SelectItem value="leitos_uti">Leitos de UTI</SelectItem>
                    <SelectItem value="leitos_uti_sus">Leitos de UTI SUS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>


            <BotaoAplicar
              type="button"
              onClick={buscarMapaLeitos}
              carregando={carregandoLeitos}
              pendente={modoLeitosAplicado != null && modoLeitos !== modoLeitosAplicado}
              className="mx-auto mt-5 flex w-full flex-col items-center sm:w-1/2 lg:w-1/4"
            />
          </div>


          {falhaLeitos != null && (
            <div className="mt-5">
              <ErrorState
                error={falhaLeitos}
                onRetry={buscarMapaLeitos}
              />
            </div>
          )}


          {carregandoLeitos && (
            <Skeleton aria-busy="true" className="mt-5 h-[520px]" />
          )}


          {leitosBruto
            && !carregandoLeitos
            && modoLeitosAplicado
            && (
              leitosBruto.length > 0 ? (
                <div className="mt-5 space-y-6">
                  <MapaBrasilUf
                    dados={dadosMapaLeitos}
                    titulo={ROTULOS_METRICA[metricaLeitos]}
                    descricao={ROTULOS_MODO[modoLeitosAplicado]}
                    tituloValor={ROTULOS_METRICA[metricaLeitos]}
                    unidade={unidadeLeitos}
                    formatar={formatarLeitos}
                  />


                  <section>
                    <div className="mb-4">
                      <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                        Dados por Unidade Federativa
                      </h2>

                      <p className="mt-1 text-sm leading-6 text-muted">
                        Alterar apenas a métrica recolore o mapa e reordena esta tabela localmente, sem nova consulta ao banco.
                      </p>
                    </div>

                    <DataTable
                      data={leitosTabela}
                      columns={colunasLeitos}
                      pageSize={27}
                    />
                  </section>
                </div>
              ) : (
                <div className="mt-5">
                  <EmptyState
                    title="Sem leitos por UF"
                    cause="A base selecionada não trouxe leitos para nenhuma Unidade Federativa."
                  />
                </div>
              )
            )}
        </TabsContent>
      </Tabs>
    </main>
  );
}
