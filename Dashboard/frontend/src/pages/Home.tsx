import { Link } from "react-router";

const modulos = [
  {
    titulo: "Medicamentos",
    descricao:
      "Consulte estoque atual, lotes próximos do vencimento, distribuição geográfica e histórico de compras.",
    href: "/medicamentos",
    status: "Disponível",
    icone: "💊",
  },
  {
    titulo: "Compras",
    descricao:
      "Analise valores, fornecedores, fabricantes, modalidades e evolução temporal das compras.",
    href: "/compras",
    status: "Disponível",
    icone: "🛒",
  },
  {
    titulo: "Leitos",
    descricao:
      "Explore capacidade hospitalar, participação SUS, tipos de UTI e distribuição por instituição.",
    href: "/leitos",
    status: "Disponível",
    icone: "🛏️",
  },
  {
    titulo: "Mapa",
    descricao:
      "Visualize indicadores de saúde por Unidade Federativa, incluindo estoque de medicamentos e disponibilidade de leitos.",
    href: "/mapa",
    status: "Disponível",
    icone: "🗺️",
  },
];

export function Home() {
  return (
    <main>
      <section className="landing-hero border-b border-teal-100/80">
        <div className="mx-auto max-w-[1440px] px-4 py-14 sm:px-6 sm:py-18 lg:px-8 lg:py-24">
          <div className="max-w-3xl">
            <span className="mb-4 inline-flex rounded-full border border-teal-100 bg-teal-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-teal-700 sm:mb-5 sm:text-xs">
              Dados em saúde
            </span>

            <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl xl:text-6xl">
              Explore os dados do projeto de forma visual e interativa.
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:mt-6 sm:text-lg sm:leading-8">
              Consulte informações de medicamentos, compras, leitos
              hospitalares e análises geográficas a partir dos dados
              armazenados no PostgreSQL, com filtros, tabelas, gráficos
              e mapas orientados à análise.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap">
              <Link
                to="/mapa"
                className="button-cta inline-flex min-h-11 items-center justify-center px-5 py-3 text-sm font-semibold transition"
              >
                Explorar mapa
              </Link>

              <a
                href="#modulos"
                className="inline-flex min-h-11 items-center justify-center rounded-xl border border-teal-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-teal-50"
              >
                Ver módulos
              </a>
            </div>
          </div>
        </div>
      </section>

      <section
        id="modulos"
        className="mx-auto max-w-[1440px] px-4 py-10 sm:px-6 sm:py-12 lg:px-8 lg:py-14"
      >
        <div className="mb-6 sm:mb-8">
          <p className="text-sm font-semibold text-slate-500">
            Módulos do dashboard
          </p>

          <h2 className="mt-2 text-xl font-semibold tracking-tight sm:text-2xl">
            Escolha uma área para começar
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 xl:grid-cols-4">
          {modulos.map((modulo) => (
            <Link
              key={modulo.titulo}
              to={modulo.href}
              className="rounded-2xl border border-teal-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-teal-200 hover:shadow-md sm:p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <span className="flex size-11 items-center justify-center rounded-2xl bg-teal-50 text-2xl">
                  {modulo.icone}
                </span>

                <span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-700">
                  {modulo.status}
                </span>
              </div>

              <h3 className="mt-6 text-lg font-semibold sm:mt-8 sm:text-xl">
                {modulo.titulo}
              </h3>

              <p className="mt-3 text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
                {modulo.descricao}
              </p>

              <div className="mt-6 text-sm font-semibold text-teal-800 sm:mt-7">
                Abrir módulo →
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
