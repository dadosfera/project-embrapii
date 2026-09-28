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
import { EmptyState } from "@/ui/EmptyState";
import { ErrorState } from "@/ui/ErrorState";
import { Icon } from "@/ui/Icon";
import { PageHeader } from "@/ui/PageHeader";
import { numeroExato, quantidade } from "@/ui/format";

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


const AVISO =
  "flex items-start gap-2 rounded-[var(--radius-md)] border border-warning-border bg-[var(--warning-soft)] px-4 py-3 text-sm leading-6 text-warning-text";


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
  const [aba, setAba] = useState<AbaMapa>("estoque");


  // =========================================
  // ESTOQUE
  // =========================================

  const [termoMedicamento, setTermoMedicamento] = useState("");
  const [buscandoCatmat, setBuscandoCatmat] = useState(false);
  const [opcoesCatmat, setOpcoesCatmat] = useState<CatmatItem[]>([]);
  const [catmatSelecionado, setCatmatSelecionado] = useState("");
  const [carregandoEstoque, setCarregandoEstoque] = useState(false);
  const [estoqueBruto, setEstoqueBruto] = useState<EstoqueUf[] | null>(null);
  const [catmatAplicado, setCatmatAplicado] = useState<CatmatItem | null>(null);
  // Mensagens da página (validação, busca sem resultado): aviso inline.
  const [erroEstoque, setErroEstoque] = useState<string | null>(null);
  // Falhas de requisição: guardam o erro real para o ErrorState.
  const [falhaBusca, setFalhaBusca] = useState<unknown>(null);
  const [falhaEstoque, setFalhaEstoque] = useState<unknown>(null);


  // =========================================
  // LEITOS
  // =========================================

  const [modoLeitos, setModoLeitos] = useState<ModoLeitos>("ultima_competencia");
  const [modoLeitosAplicado, setModoLeitosAplicado] = useState<ModoLeitos | null>(null);
  const [metricaLeitos, setMetricaLeitos] = useState<MetricaLeitos>("leitos_gerais");
  const [carregandoLeitos, setCarregandoLeitos] = useState(false);
  const [leitosBruto, setLeitosBruto] = useState<LeitosPorUf[] | null>(null);
  const [falhaLeitos, setFalhaLeitos] = useState<unknown>(null);


  // Cache de consultas enquanto a rota permanecer aberta.
  const cacheEstoque = useRef(new Map<number, EstoqueUf[]>());
  const cacheLeitos = useRef(new Map<ModoLeitos, LeitosPorUf[]>());

  const formBusca = useRef<HTMLFormElement>(null);


  const itemCatmatSelecionado = useMemo(
    () => opcoesCatmat.find((item) => String(item.catmat_id) === catmatSelecionado) ?? null,
    [opcoesCatmat, catmatSelecionado],
  );


  async function localizarCatmat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const termo = termoMedicamento.trim();

    if (!termo) {
      setErroEstoque("Digite um medicamento para localizar itens no CATMAT.");
      return;
    }

    setBuscandoCatmat(true);
    setErroEstoque(null);
    setFalhaBusca(null);
    setFalhaEstoque(null);
    setOpcoesCatmat([]);
    setCatmatSelecionado("");

    try {
      const resposta = await buscarMedicamentos(termo);

      setOpcoesCatmat(resposta);

      if (resposta.length === 0) {
        setErroEstoque("Nenhum item do CATMAT foi encontrado para essa busca.");
        return;
      }

      setCatmatSelecionado(String(resposta[0].catmat_id));
    } catch (error) {
      setFalhaBusca(error);
    } finally {
      setBuscandoCatmat(false);
    }
  }


  async function buscarMapaEstoque() {
    if (!itemCatmatSelecionado) {
      setErroEstoque("Selecione um item do CATMAT antes de buscar.");
      return;
    }

    setCarregandoEstoque(true);
    setErroEstoque(null);
    setFalhaEstoque(null);

    const catmatId = itemCatmatSelecionado.catmat_id;

    try {
      const armazenado = cacheEstoque.current.get(catmatId);
      const resposta = armazenado ?? await buscarEstoquePorUf(catmatId);

      if (!armazenado) {
        cacheEstoque.current.set(catmatId, resposta);
      }

      setEstoqueBruto(resposta);
      setCatmatAplicado(itemCatmatSelecionado);
    } catch (error) {
      setFalhaEstoque(error);
    } finally {
      setCarregandoEstoque(false);
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


  const estoqueNormalizado = useMemo(
    () => (estoqueBruto ? normalizarEstoque(estoqueBruto) : []),
    [estoqueBruto],
  );

  const dadosMapaEstoque = useMemo<DadoMapaUf[]>(
    () => estoqueNormalizado.map((item) => ({ uf: item.uf, valor: item.estoque_total })),
    [estoqueNormalizado],
  );

  const estoqueTabela = useMemo(
    () => [...estoqueNormalizado].sort((a, b) => b.estoque_total - a.estoque_total),
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
    () => [...leitosNormalizado].sort((a, b) => b[metricaLeitos] - a[metricaLeitos]),
    [leitosNormalizado, metricaLeitos],
  );


  const colunasEstoque = useMemo<ColumnDef<LinhaEstoque, unknown>[]>(
    () => [
      { header: "UF", accessorKey: "uf" },
      {
        header: "Estoque",
        accessorKey: "estoque_total",
        cell: ({ row }) => quantidade(row.original.estoque_total),
        meta: { align: "right" },
      },
      {
        header: "Instituições",
        accessorKey: "num_instituicoes",
        cell: ({ row }) => numeroExato(row.original.num_instituicoes),
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
        header: "Leitos de UTI SUS",
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
                Localize um item no CATMAT e carregue a distribuição de estoque das instituições.
              </p>
            </div>


            <form
              ref={formBusca}
              onSubmit={localizarCatmat}
              className="mt-5"
            >
              <label
                htmlFor="mapa-busca-catmat"
                className="block text-sm font-semibold text-[var(--text)]"
              >
                Medicamento / CATMAT
              </label>

              <div className="mt-2 flex flex-col gap-3 sm:flex-row">
                <Input
                  id="mapa-busca-catmat"
                  type="search"
                  value={termoMedicamento}
                  onChange={(event) => setTermoMedicamento(event.target.value)}
                  placeholder="Ex.: dipirona, insulina, seringa..."
                  className="h-10 min-w-0 bg-panel sm:flex-1"
                />

                <Button
                  type="submit"
                  variant="outline"
                  disabled={buscandoCatmat || !termoMedicamento.trim()}
                  className="h-10 w-full px-5 sm:w-auto sm:min-w-36"
                >
                  <Icon name="search" size={16} />
                  {buscandoCatmat
                    ? "Localizando..."
                    : "Localizar itens"}
                </Button>
              </div>
            </form>


            {opcoesCatmat.length > 0 && (
              <div className="mt-5">
                <label
                  htmlFor="mapa-catmat-selecionado"
                  className="block text-sm font-semibold text-[var(--text)]"
                >
                  Item
                </label>

                {/* Continua <select> nativo: o smoke usa selectOption() no campo "Item". */}
                <select
                  id="mapa-catmat-selecionado"
                  value={catmatSelecionado}
                  onChange={(event) => setCatmatSelecionado(event.target.value)}
                  className="mt-2 h-10 w-full min-w-0 rounded-[var(--radius-md)] border border-line bg-panel px-3 text-sm text-[var(--text)] shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                >
                  {opcoesCatmat.map((item) => (
                    <option key={item.catmat_id} value={item.catmat_id}>
                      {item.descricao_catmat ?? "Descrição não informada"}
                      {" — CATMAT "}
                      {item.codigo_catmat ?? "N/I"}
                    </option>
                  ))}
                </select>


                <Button
                  type="button"
                  onClick={buscarMapaEstoque}
                  disabled={carregandoEstoque || !itemCatmatSelecionado}
                  className="mx-auto mt-5 flex h-10 w-full sm:w-1/2 lg:w-1/4"
                >
                  {carregandoEstoque
                    ? "Carregando..."
                    : "Buscar"}
                </Button>
              </div>
            )}


            {erroEstoque && (
              <div role="status" className={`mt-4 ${AVISO}`}>
                <Icon name="alert" size={18} className="mt-0.5" />
                {erroEstoque}
              </div>
            )}
          </div>


          {falhaBusca != null && (
            <div className="mt-5">
              <ErrorState
                error={falhaBusca}
                onRetry={() => formBusca.current?.requestSubmit()}
              />
            </div>
          )}


          {falhaEstoque != null && (
            <div className="mt-5">
              <ErrorState
                error={falhaEstoque}
                onRetry={itemCatmatSelecionado ? buscarMapaEstoque : undefined}
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
                  />


                  <section>
                    <div className="mb-4">
                      <h2 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                        Dados por Unidade Federativa
                      </h2>

                      <p className="mt-1 text-sm leading-6 text-muted">
                        A tabela e o mapa usam a mesma resposta da consulta. UFs sem registro são mantidas com valor zero.
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
                Escolha a base utilizada. A métrica pode ser alterada depois sem realizar uma nova consulta.
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
                    <SelectItem value="leitos_gerais">Leitos gerais</SelectItem>
                    <SelectItem value="leitos_sus">Leitos SUS</SelectItem>
                    <SelectItem value="leitos_uti">Leitos de UTI</SelectItem>
                    <SelectItem value="leitos_uti_sus">Leitos de UTI SUS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>


            <Button
              type="button"
              onClick={buscarMapaLeitos}
              disabled={carregandoLeitos}
              className="mx-auto mt-5 flex h-10 w-full sm:w-1/2 lg:w-1/4"
            >
              {carregandoLeitos
                ? "Carregando..."
                : "Buscar"}
            </Button>
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
