import type { CatalogResponse, ConfigurationSelection } from "../api/types";
import { Icon } from "./Icon";

export interface ConfigurationLabels {
  database: string;
  library: string;
  model: string;
  context: string;
}

export function getConfigurationLabels(configuration: ConfigurationSelection, catalog?: CatalogResponse): ConfigurationLabels {
  const label = (items: { id: string; label: string }[] | undefined, id: string) => items?.find((item) => item.id === id)?.label || id;
  return {
    database: label(catalog?.databases, configuration.database),
    library: label(catalog?.libraries, configuration.library),
    model: label(catalog?.models, configuration.model_id),
    context: label(catalog?.contexts, configuration.context)
  };
}

export function ConfigurationSummary({
  configuration,
  catalog,
  seed,
  onOpen
}: {
  configuration: ConfigurationSelection;
  catalog?: CatalogResponse;
  seed?: number;
  onOpen: () => void;
}) {
  const labels = getConfigurationLabels(configuration, catalog);
  const items = [labels.database, labels.library, labels.model, labels.context, ...(seed === undefined ? [] : [`Seed ${seed}`])];

  return (
    <button
      type="button"
      className="configuration-summary"
      onClick={onOpen}
      aria-label={`Abrir configuração: ${items.join(", ")}`}
    >
      <Icon name="settings" size={15} />
      <span>{items.map((item, index) => <span className="summary-item" key={`${item}-${index}`}>{item}</span>)}</span>
      <Icon name="chevron-right" size={15} />
    </button>
  );
}
