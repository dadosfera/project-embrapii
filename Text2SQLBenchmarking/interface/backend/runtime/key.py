"""Identidade canônica e segura de um runtime de modelo."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import math
import os
from pathlib import Path
import re

from interface.backend.adapters.paths import ContextResources, resolve_context_resources
from interface.backend.domain.capabilities import (
    ApplicationMode,
    ConfigurationSelection,
    ContextId,
    DatabaseId,
    LibraryId,
    resolve_legacy_token,
    validate_configuration,
)

DEFAULT_VANNA_MAX_NEW_TOKENS = 4096


class RuntimeKeyError(ValueError):
    """Falha segura ao construir uma chave de runtime."""

    def __init__(self, public_message: str, internal_detail: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.internal_detail = internal_detail


@dataclass(frozen=True)
class GenerationParameters:
    """Parâmetros efetivos que influenciam a geração, nunca valores secretos."""

    max_new_tokens: int | None = None
    do_sample: bool | None = None
    temperature: float | None = None
    top_p: float | None = None

    @classmethod
    def defaults_for(cls, library: LibraryId) -> GenerationParameters:
        if library is LibraryId.RAW_MODEL:
            return cls(max_new_tokens=512, do_sample=False)
        if library is LibraryId.VANNA_AI:
            try:
                vanna_max_new_tokens = int(
                    os.getenv(
                        "VANNA_MAX_NEW_TOKENS",
                        str(DEFAULT_VANNA_MAX_NEW_TOKENS),
                    )
                )
            except ValueError as exc:
                raise RuntimeKeyError(
                    "Os parâmetros de geração informados não são válidos.",
                    "VANNA_MAX_NEW_TOKENS inválido",
                ) from exc
            return cls(
                max_new_tokens=vanna_max_new_tokens,
                do_sample=True,
                temperature=1.0,
                top_p=0.9,
            )
        if library is LibraryId.XIYAN_SQL:
            return cls(
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.1,
                top_p=0.8,
            )
        return cls()

    def as_dict(self) -> dict[str, int | float | bool | None]:
        return {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.do_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

    def validate(self) -> None:
        if self.max_new_tokens is not None and (
            isinstance(self.max_new_tokens, bool)
            or not isinstance(self.max_new_tokens, int)
            or self.max_new_tokens <= 0
        ):
            raise RuntimeKeyError(
                "Os parâmetros de geração informados não são válidos.",
                "max_new_tokens incompatível",
            )
        if self.do_sample is not None and not isinstance(self.do_sample, bool):
            raise RuntimeKeyError(
                "Os parâmetros de geração informados não são válidos.",
                "do_sample incompatível",
            )
        if self.temperature is not None and (
            isinstance(self.temperature, bool)
            or not isinstance(self.temperature, (int, float))
            or not math.isfinite(self.temperature)
            or self.temperature < 0
        ):
            raise RuntimeKeyError(
                "Os parâmetros de geração informados não são válidos.",
                "temperature incompatível",
            )
        if self.top_p is not None and (
            isinstance(self.top_p, bool)
            or not isinstance(self.top_p, (int, float))
            or not math.isfinite(self.top_p)
            or not 0 < self.top_p <= 1
        ):
            raise RuntimeKeyError(
                "Os parâmetros de geração informados não são válidos.",
                "top_p incompatível",
            )


def _fingerprint_file(path: str | None, resource_name: str) -> str | None:
    if path is None:
        return None
    candidate = Path(path)
    if not candidate.is_file():
        raise RuntimeKeyError(
            "Um recurso de contexto necessário não está disponível.",
            f"{resource_name} indisponível",
        )
    digest = hashlib.sha256()
    with candidate.open("rb") as resource:
        for chunk in iter(lambda: resource.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _token_fingerprint(hf_token: str | None) -> str:
    if hf_token is None:
        return "absent"
    return f"sha256:{hashlib.sha256(hf_token.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class RuntimeKey:
    """Chave imutável que separa qualquer runtime metodologicamente distinto."""

    library: LibraryId
    model_id: str
    database: DatabaseId
    context: ContextId
    mode: ApplicationMode
    local_model: bool
    random_seed: int
    legacy_token: str
    generation_parameters: GenerationParameters
    documentation_fingerprint: str | None
    examples_fingerprint: str | None
    xiyan_prompt_language: str | None
    token_fingerprint: str

    def __post_init__(self) -> None:
        """Impede chaves diretas que não representem o runtime v1 real."""

        if isinstance(self.random_seed, bool) or not isinstance(self.random_seed, int):
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "seed incompatível",
            )
        if self.local_model is not True:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "a interface exige local_model=True",
            )
        validation = validate_configuration(self.configuration, self.mode)
        if not validation.is_valid:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "RuntimeKey direta não passou pelo catálogo",
            )
        legacy_token = resolve_legacy_token(self.library.value, self.context.value)
        if not legacy_token.is_valid or legacy_token.value != self.legacy_token:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "token legado incompatível",
            )
        canonical_parameters = GenerationParameters.defaults_for(self.library)
        if self.generation_parameters != canonical_parameters:
            raise RuntimeKeyError(
                "Os parâmetros de geração informados não são válidos.",
                "override de parâmetros não aplicado pelo adapter",
            )
        self.generation_parameters.validate()
        expected_xiyan_language = "cn" if self.library is LibraryId.XIYAN_SQL else None
        if self.xiyan_prompt_language != expected_xiyan_language:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "idioma XiYan incompatível",
            )
        if self.token_fingerprint != "absent" and not re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            self.token_fingerprint,
        ):
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "fingerprint de token incompatível",
            )

    @property
    def configuration(self) -> ConfigurationSelection:
        return ConfigurationSelection(
            database=self.database.value,
            library=self.library.value,
            model_id=self.model_id,
            context=self.context.value,
        )

    @classmethod
    def from_configuration(
        cls,
        configuration: ConfigurationSelection,
        mode: ApplicationMode | str,
        *,
        random_seed: int,
        hf_token: str | None,
        local_model: bool = True,
        generation_parameters: GenerationParameters | None = None,
        project_root: Path | None = None,
    ) -> RuntimeKey:
        try:
            selected_mode = ApplicationMode(mode)
        except ValueError as exc:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "modo inválido na RuntimeKey",
            ) from exc

        validation = validate_configuration(configuration, selected_mode)
        if not validation.is_valid:
            detail = validation.error.code.value if validation.error else "inválido"
            raise RuntimeKeyError(
                validation.error.message
                if validation.error
                else "A configuração selecionada não é suportada.",
                f"catálogo rejeitou configuração: {detail}",
            )
        if isinstance(random_seed, bool) or not isinstance(random_seed, int):
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "seed incompatível",
            )

        library = LibraryId(configuration.library)
        context = ContextId(configuration.context)
        canonical_parameters = GenerationParameters.defaults_for(library)
        if (
            generation_parameters is not None
            and generation_parameters != canonical_parameters
        ):
            raise RuntimeKeyError(
                "Os parâmetros de geração informados não são válidos.",
                "override de parâmetros não aplicado pelo adapter",
            )
        parameters = canonical_parameters
        parameters.validate()
        legacy_token = resolve_legacy_token(configuration.library, configuration.context)
        if not legacy_token.is_valid or legacy_token.value is None:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "token legado não resolvido",
            )

        try:
            resources: ContextResources = resolve_context_resources(
                configuration,
                root=project_root,
            )
            documentation_fingerprint = _fingerprint_file(
                resources.doc_path,
                "documentação",
            )
            examples_fingerprint = _fingerprint_file(
                resources.examples_path,
                "exemplos",
            )
        except RuntimeKeyError:
            raise
        except Exception as exc:
            raise RuntimeKeyError(
                "Um recurso de contexto necessário não está disponível.",
                f"falha ao resolver recursos: {type(exc).__name__}",
            ) from exc

        if local_model is not True:
            raise RuntimeKeyError(
                "A configuração selecionada não é suportada.",
                "a interface exige local_model=True",
            )

        return cls(
            library=library,
            model_id=configuration.model_id,
            database=DatabaseId(configuration.database),
            context=context,
            mode=selected_mode,
            local_model=local_model,
            random_seed=random_seed,
            legacy_token=legacy_token.value,
            generation_parameters=parameters,
            documentation_fingerprint=documentation_fingerprint,
            examples_fingerprint=examples_fingerprint,
            xiyan_prompt_language=("cn" if library is LibraryId.XIYAN_SQL else None),
            token_fingerprint=_token_fingerprint(hf_token),
        )

    def matches_token(self, hf_token: str | None) -> bool:
        return hmac.compare_digest(self.token_fingerprint, _token_fingerprint(hf_token))

    def as_dict(self) -> dict[str, object]:
        """Representação serializável que não contém o token bruto."""

        return {
            "library": self.library.value,
            "model_id": self.model_id,
            "database": self.database.value,
            "context": self.context.value,
            "mode": self.mode.value,
            "local_model": self.local_model,
            "random_seed": self.random_seed,
            "legacy_token": self.legacy_token,
            "generation_parameters": self.generation_parameters.as_dict(),
            "documentation_fingerprint": self.documentation_fingerprint,
            "examples_fingerprint": self.examples_fingerprint,
            "xiyan_prompt_language": self.xiyan_prompt_language,
            "token_fingerprint": self.token_fingerprint,
        }
