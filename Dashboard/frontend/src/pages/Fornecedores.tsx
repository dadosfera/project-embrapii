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
import {
  buscarMapaFornecedoresPorUf,
  buscarRankingFornecedores,
  type MapaFornecedorUf,
  type RankingFornecedor,
} from "../lib/fornecedoresApi";

const formatadorMoeda = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

const formatadorNumero = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 0,
});

const formatadorPercentual = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 1,
});

function calcularPercentualEstrangeiro(item: MapaFornecedorUf): number {
  const totalEstrangeiro =
    item.quantidade_estrangeiro + item.quantidade_grupo_estrangeiro;
  const total = item.quantidade_nacional + totalEstrangeiro;
  if (total <= 0) return 0;
  return (totalEstrangeiro / total) * 100;
}

function RotuloOrigem({ origem }: { origem: RankingFornecedor["nacional_estrangeiro"] }) {
  const estilos: Record<string, string> = {
    NACIONAL: "bg-teal-50 text-teal-700 border-teal-200",
    ESTRANGEIRO: "bg-amber-50 text-amber-700 border-amber-200",
    GRUPO_ESTRANGEIRO: "bg-orange-50 text-orange-700 border-orange-200",
    DESCONHECIDO: "bg-slate-50 text-slate-500 border-slate-200",
  };

  const rotulos: Record<string, string> = {
    NACIONAL: "Nacional",
    ESTRANGEIRO: "Estrangeiro",
    GRUPO_ESTRANGEIRO: "Subsidiária estrangeira",
    DESCONHECIDO: "Não classificado",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${estilos[origem]}`}
    >
      {rotulos[origem]}
    </span>
  );
}

export  function Fornecedores() {
  const hoje = new Date().toISOString().slice(0, 10);

  const [dataInicio, setDataInicio] = useState("2015-01-01");
  const [dataFim, setDataFim] = useState(hoje);
  const [ufFiltro, setUfFiltro] = useState("");

  const [dadosMapa, setDadosMapa] = useState<MapaFornecedorUf[]>([]);
  const [ranking, setRanking] = useState<RankingFornecedor[]>([]);

  const [carregandoMapa, setCarregandoMapa] = useState(true);
  const [carregandoRanking, setCarregandoRanking] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;

    async function carregarMapa() {
      try {
        setCarregandoMapa(true);
        setErro(null);
        const resposta = await buscarMapaFornecedoresPorUf(dataInicio, dataFim);
        if (ativo) setDadosMapa(resposta);
      } catch (error) {
        if (ativo) {
          setErro(
            error instanceof Error
              ? error.message
              : "Não foi possível carregar os dados do mapa.",
          );
        }
      } finally {
        if (ativo) setCarregandoMapa(false);
      }
    }

    void carregarMapa();

    return () => {
      ativo = false;
    };
  }, [dataInicio, dataFim]);

  useEffect(() => {
    let ativo = true;

    async function carregarRanking() {
      try {
        setCarregandoRanking(true);
        const resposta = await buscarRankingFornecedores(
          dataInicio,
          dataFim,
          ufFiltro || undefined,
          100,
        );
        if (ativo) setRanking(resposta);
      } catch (error) {
        if (ativo) {
          setErro(
            error instanceof Error
              ? error.message
              : "Não foi possível carregar o ranking de fornecedores.",
          );
        }
      } finally {
        if (ativo) setCarregandoRanking(false);
      }
    }

    void carregarRanking();

    return () => {
      ativo = false;
    };
  }, [dataInicio, dataFim, ufFiltro]);

  const dadosMapaFormatados: DadoMapaUf[] = useMemo(
    () =>
      dadosMapa.map((item) => ({
        uf: item.uf,
        valor: calcularPercentualEstrangeiro(item),
      })),
    [dadosMapa],
  );

  const ufsDisponiveis = useMemo(
    () =>
      dadosMapa
        .map((item) => item.uf)
        .filter((uf) => uf !== "Nao informado")
        .sort(),
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
      percentualEstrangeiro: total > 0 ? (totalEstrangeiro / total) * 100 : 0,
    };
  }, [dadosMapa]);

  const colunas = useMemo<ColumnDef<RankingFornecedor, unknown>[]>(
    () => [
      {
        accessorKey: "fornecedor",
        header: "Fornecedor",
      },
      {
        accessorKey: "cnpj",
        header: "CNPJ",
        cell: ({ getValue }) => getValue<string | null>() ?? "—",
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
        cell: ({ getValue }) => getValue<string | null>() ?? "—",
      },
      {
        accessorKey: "valor_total",
        header: "Valor total",
        cell: ({ getValue }) => formatadorMoeda.format(getValue<number>()),
      },
      {
        accessorKey: "quantidade_itens",
        header: "Itens fornecidos",
        cell: ({ getValue }) => formatadorNumero.format(getValue<number>()),
      },
      {
        accessorKey: "numero_compras",
        header: "Nº de compras",
        cell: ({ getValue }) => formatadorNumero.format(getValue<number>()),
      },
    ],
    [],
  );

  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] space-y-6 px-4 py-7 sm:px-6 sm:py-9 lg:px-8 lg:py-10">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Fornecedores</h1>
        <p className="mt-1 text-sm leading-6 text-slate-500">
          Distribuição de compras por origem do fornecedor (nacional ou
          estrangeiro), por estado.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-xl border border-teal-100 bg-white p-4">
        <div>
          <label className="block text-xs font-medium text-slate-500">
            Data inicial
          </label>
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="mt-1 rounded-lg border border-slate-200 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500">
            Data final
          </label>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="mt-1 rounded-lg border border-slate-200 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500">
            UF (tabela)
          </label>
          <select
            value={ufFiltro}
            onChange={(e) => setUfFiltro(e.target.value)}
            className="mt-1 rounded-lg border border-slate-200 px-3 py-2 text-sm"
          >
            <option value="">Todas</option>
            {ufsDisponiveis.map((uf) => (
              <option key={uf} value={uf}>
                {uf}
              </option>
            ))}
          </select>
        </div>
      </div>

      {erro && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {erro}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-teal-100 bg-white p-4">
          <p className="text-xs font-medium text-slate-500">
            Itens de fornecedores nacionais
          </p>
          <p className="mt-1 text-2xl font-semibold text-teal-800">
            {formatadorNumero.format(resumoGeral.totalNacional)}
          </p>
        </div>

        <div className="rounded-xl border border-teal-100 bg-white p-4">
          <p className="text-xs font-medium text-slate-500">
            Itens de fornecedores estrangeiros
          </p>
          <p className="mt-1 text-2xl font-semibold text-amber-700">
            {formatadorNumero.format(resumoGeral.totalEstrangeiro)}
          </p>
        </div>

        <div className="rounded-xl border border-teal-100 bg-white p-4">
          <p className="text-xs font-medium text-slate-500">
            % estrangeiro (geral)
          </p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {formatadorPercentual.format(resumoGeral.percentualEstrangeiro)}%
          </p>
        </div>
      </div>

      {carregandoMapa ? (
        <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-teal-700">
            Carregando mapa...
          </p>
        </div>
      ) : (
        <MapaBrasilUf
          dados={dadosMapaFormatados}
          titulo="Origem dos fornecedores por estado"
          descricao="Percentual de itens comprados de fornecedores estrangeiros, por UF da mantenedora compradora. Estados mais escuros têm maior participação de fornecedores estrangeiros."
          tituloValor="% de itens estrangeiros"
        />
      )}

      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          Ranking de fornecedores
        </h2>
        <p className="mt-1 text-sm leading-6 text-slate-500">
          Ordenado por valor total comprado no período selecionado.
        </p>

        <div className="mt-3">
          {carregandoRanking ? (
            <div className="rounded-xl border border-dashed border-teal-100 bg-teal-50/50 px-4 py-8 text-center text-sm text-slate-500">
              Carregando ranking...
            </div>
          ) : (
            <DataTable data={ranking} columns={colunas} pageSize={15} />
          )}
        </div>
      </div>
    </main>
  );
}
