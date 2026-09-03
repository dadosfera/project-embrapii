import type { CatalogResponse, ConfigurationSelection, Mode } from "../api/types";
import { Icon } from "./Icon";

interface Props {
  catalog: CatalogResponse;
  configuration: ConfigurationSelection;
  mode: Mode;
  seed: number;
  disabled: boolean;
  onChange: (next: ConfigurationSelection) => void;
  onSeedChange: (seed: number) => void;
}

export function ConfigurationPanel({ catalog, configuration, mode, seed, disabled, onChange, onSeedChange }: Props) {
  const selectableLibraries = mode === "chat"
    ? catalog.libraries.filter((item) => item.availability.chat.available)
    : catalog.libraries;
  const library = selectableLibraries.find((item) => item.id === configuration.library) || selectableLibraries[0];
  const allowedModels = catalog.models.filter((item) => library?.model_ids.includes(item.id));
  const allowedContexts = catalog.contexts.filter((item) => library?.contexts.includes(item.id));
  const availability = library?.availability[mode];

  return (
    <section className="configuration-panel" aria-labelledby="configuration-fields-title">
      <h3 className="sr-only" id="configuration-fields-title">Campos de configuração</h3>

      <div className="configuration-field">
        <label htmlFor="database"><Icon name="database" size={17} />Base de dados</label>
        <select id="database" value={configuration.database} disabled={disabled} onChange={(event) => onChange({ ...configuration, database: event.target.value })}>
          {catalog.databases.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
        </select>
      </div>

      <div className="configuration-field">
        <label htmlFor="library"><Icon name="library" size={17} />Biblioteca</label>
        <select id="library" value={configuration.library} disabled={disabled} onChange={(event) => onChange({ ...configuration, library: event.target.value })}>
          {selectableLibraries.map((item) => {
            const optionAvailability = item.availability[mode];
            return <option value={item.id} key={item.id} disabled={!optionAvailability.available}>{item.label}</option>;
          })}
        </select>
        {!availability?.available && availability?.reason && (
          <p className="unavailable-reason" role="note">Indisponível neste modo: {availability.reason.message}</p>
        )}
      </div>

      <div className="configuration-field">
        <label htmlFor="model"><Icon name="model" size={17} />Modelo</label>
        <select id="model" value={configuration.model_id} disabled={disabled} onChange={(event) => onChange({ ...configuration, model_id: event.target.value })}>
          {allowedModels.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
        </select>
      </div>

      <div className="configuration-field">
        <label htmlFor="context"><Icon name="context" size={17} />Contexto</label>
        <select id="context" value={configuration.context} disabled={disabled} onChange={(event) => onChange({ ...configuration, context: event.target.value })}>
          {allowedContexts.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
        </select>
      </div>

      {mode === "benchmark" && (
        <div className="configuration-field">
          <label htmlFor="benchmark-seed"><Icon name="seed" size={17} />Seed</label>
          <input id="benchmark-seed" type="number" step="1" value={seed} disabled={disabled} onChange={(event) => onSeedChange(Number(event.target.value))} />
        </div>
      )}
    </section>
  );
}
