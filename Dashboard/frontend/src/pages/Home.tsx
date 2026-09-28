import { useEffect, useState } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { buscarOpcoesLeitos, type OpcoesLeitos } from "@/lib/api";
import { Icon } from "@/ui/Icon";
import type { IconName } from "@/ui/icons";
import { KpiCard } from "@/ui/KpiCard";
import { SEM_DADO, numeroExato } from "@/ui/format";

const modulos: { titulo: string; descricao: string; href: string; status: string; icone: IconName }[] = [
  {
    titulo: "Medicamentos",
    descricao:
      "Consulte estoque atual, lotes próximos do vencimento, distribuição geográfica e histórico de compras.",
    href: "/medicamentos",
    status: "Disponível",
    icone: "droplet",
  },
  {
    titulo: "Compras",
    descricao:
      "Analise valores, fornecedores, fabricantes, modalidades e evolução temporal das compras.",
    href: "/compras",
    status: "Disponível",
    icone: "cart",
  },
  {
    titulo: "Leitos",
    descricao:
      "Explore capacidade hospitalar, participação SUS, tipos de UTI e distribuição por instituição.",
    href: "/leitos",
    status: "Disponível",
    icone: "activity",
  },
  {
    titulo: "Mapa",
    descricao:
      "Visualize indicadores de saúde por Unidade Federativa, incluindo estoque de medicamentos e disponibilidade de leitos.",
    href: "/mapa",
    status: "Disponível",
    icone: "map",
  },
  {
    titulo: "Fornecedores",
    descricao: "Origem dos fornecedores das compras públicas, por UF.",
    href: "/fornecedores",
    status: "Disponível",
    icone: "briefcase",
  },
];

/** "AAAA-MM-DD" → "MM/AAAA" (competência é mensal). */
function competencia(v: string | null | undefined): string {
  const m = v ? /^(\d{4})-(\d{2})/.exec(v) : null;
  return m ? `${m[2]}/${m[1]}` : SEM_DADO;
}

/** Quantidade de meses de competência entre o mínimo e o máximo, contando os dois. */
function mesesDeCobertura(min: string | null, max: string | null): number | null {
  const a = min ? /^(\d{4})-(\d{2})/.exec(min) : null;
  const b = max ? /^(\d{4})-(\d{2})/.exec(max) : null;
  if (!a || !b) return null;
  return (Number(b[1]) - Number(a[1])) * 12 + (Number(b[2]) - Number(a[2])) + 1;
}

export function Home() {
  const [opcoes, setOpcoes] = useState<OpcoesLeitos | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let ativo = true;
    buscarOpcoesLeitos()
      .then((r) => {
        if (ativo) setOpcoes(r);
      })
      // A cobertura é complementar: sem ela o hero mostra "sem dado", nunca 0.
      .catch(() => undefined)
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  const meses = opcoes ? mesesDeCobertura(opcoes.data_minima, opcoes.data_maxima) : null;

  return (
    <main>
      <section className="landing-hero border-b border-line">
        <div className="mx-auto grid max-w-[1440px] gap-8 px-4 py-10 sm:px-6 sm:py-14 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] lg:items-end lg:px-8 lg:py-16">
          <div className="max-w-3xl">
            <span className="mb-4 inline-flex rounded-full bg-primary-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-primary sm:text-xs">
              Dados em saúde
            </span>

            <h1 className="text-3xl font-semibold tracking-tight text-[var(--text)] sm:text-4xl lg:text-5xl">
              Explore os dados do projeto de forma visual e interativa.
            </h1>

            <p className="mt-4 max-w-2xl text-base leading-7 text-muted sm:text-lg sm:leading-8">
              Medicamentos, compras, leitos hospitalares e fornecedores, com dados armazenados no
              Snowflake da plataforma Dadosfera, em filtros, tabelas, gráficos e mapas.
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Button asChild size="lg" className="min-h-11">
                <Link to="/mapa">
                  <Icon name="map" size={18} />
                  Explorar mapa
                </Link>
              </Button>

              <Button
                type="button"
                variant="outline"
                size="lg"
                className="min-h-11"
                onClick={() => document.getElementById("modulos")?.scrollIntoView({ behavior: "smooth" })}
              >
                Ver módulos
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <KpiCard
              label="UFs com leitos"
              value={opcoes ? opcoes.ufs.length : null}
              format={numeroExato}
              loading={carregando}
            />
            <KpiCard
              label="Meses de competência"
              value={meses}
              format={numeroExato}
              loading={carregando}
              hint={
                opcoes && meses != null
                  ? `${competencia(opcoes.data_minima)} a ${competencia(opcoes.data_maxima)}`
                  : undefined
              }
            />
          </div>
        </div>
      </section>

      <section
        id="modulos"
        className="mx-auto max-w-[1440px] scroll-mt-20 px-4 py-10 sm:px-6 sm:py-12 lg:px-8 lg:py-14"
      >
        <div className="mb-6 sm:mb-8">
          <p className="text-sm font-semibold text-muted">Módulos do dashboard</p>

          <h2 className="mt-2 text-xl font-semibold tracking-tight text-[var(--text)] sm:text-2xl">
            Escolha uma área para começar
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3 xl:grid-cols-5">
          {modulos.map((modulo) => (
            <Link
              key={modulo.titulo}
              to={modulo.href}
              className="group flex flex-col rounded-[var(--radius-md)] border border-line bg-panel p-5 shadow-[var(--shadow-card)] transition-colors hover:border-[var(--border-strong)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)] sm:p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <span className="flex size-11 items-center justify-center rounded-[var(--radius-md)] bg-primary-soft text-primary">
                  <Icon name={modulo.icone} size={22} />
                </span>

                <span className="rounded-full bg-subtle px-2.5 py-1 text-xs font-medium text-muted">
                  {modulo.status}
                </span>
              </div>

              <h3 className="mt-6 text-lg font-semibold text-[var(--text)] sm:text-xl">{modulo.titulo}</h3>

              <p className="mt-3 flex-1 text-sm leading-6 text-muted sm:text-base sm:leading-7">
                {modulo.descricao}
              </p>

              <div className="mt-6 text-sm font-semibold text-primary group-hover:underline">
                Abrir módulo →
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
