from typing import Protocol, runtime_checkable

@runtime_checkable
class PromptLoader(Protocol):
    def load(self, template_name: str, locale: str = "pt_BR") -> str:
        ...