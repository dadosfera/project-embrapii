from pathlib import Path

from benchmark_generator.llm.prompt.loader.protocol import PromptLoader


class FilePromptLoader(PromptLoader):
    """
    Propmt loader that reads Jinja2 templates from the filesystem. The templates are organized in a directory structure like:
    prompts/
        locale_1/
            template1.jinja2
            template2.jinja2
        locale_2/
            template1.jinja2
            template2.jinja2
    """
    def __init__(self, base_dir: str = "prompts"):
        self.base_dir = Path(base_dir)

    def load(self, template_name: str, locale: str = "pt_BR") -> str:
        path = self.base_dir / locale / f"{template_name}.jinja2"
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text(encoding="utf-8")


class InMemoryPromptLoader(PromptLoader):
    """
    Prompt loader that retrieves templates from an in-memory dictionary. The keys are expected to be in the format "locale/template_name".

    :note: This loader is useful for testing or when templates are stored in a non-file-based system (e.g., database, remote service).
    """
    def __init__(self, templates: dict[str, str]):
        self.templates = templates

    def load(self, template_name: str, locale: str = "pt_BR") -> str:
        key = f"{locale}/{template_name}"
        return self.templates.get(key, self.templates.get(template_name, ""))