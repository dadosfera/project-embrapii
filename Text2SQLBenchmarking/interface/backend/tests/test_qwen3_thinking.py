from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import src.vannaai as vanna_module
from interface.backend.domain.capabilities import LibraryId
from interface.backend.runtime.key import (
    DEFAULT_VANNA_MAX_NEW_TOKENS as RUNTIME_DEFAULT_VANNA_MAX_NEW_TOKENS,
    GenerationParameters,
)

sys.modules.pop("src.vannaai", None)


def test_legacy_models_do_not_disable_thinking_in_the_chat_template():
    root = Path(__file__).parents[3] / "src"
    assert "enable_thinking=False" not in (root / "rawmodel.py").read_text(encoding="utf-8")
    assert "enable_thinking=False" not in (root / "vannaai.py").read_text(encoding="utf-8")


def test_vanna_preserves_post_generation_thinking_removal():
    source = (Path(__file__).parents[3] / "src" / "vannaai.py").read_text(encoding="utf-8")
    assert 'if "</think>" in response:' in source
    assert 'response.split("</think>")[-1].strip()' in source


def _stub_vanna():
    vanna = object.__new__(vanna_module.MyVanna)
    input_ids = SimpleNamespace(shape=(1, 3))
    input_ids.to = Mock(return_value=input_ids)
    vanna.tokenizer = SimpleNamespace(
        apply_chat_template=Mock(return_value=input_ids),
        eos_token_id=0,
        decode=Mock(return_value="<think>SELECT secreto FROM interno</think> SELECT 1"),
    )
    vanna.model = SimpleNamespace(device="cpu", generate=Mock(return_value=[[0, 0, 0, 1]]))
    vanna.log = Mock()
    return vanna


def test_vanna_default_matches_runtime_key_default(monkeypatch):
    monkeypatch.delenv("VANNA_MAX_NEW_TOKENS", raising=False)

    assert vanna_module.DEFAULT_VANNA_MAX_NEW_TOKENS == 4096
    assert RUNTIME_DEFAULT_VANNA_MAX_NEW_TOKENS == 4096
    assert (
        GenerationParameters.defaults_for(LibraryId.VANNA_AI).max_new_tokens
        == vanna_module.DEFAULT_VANNA_MAX_NEW_TOKENS
    )


def test_vanna_keeps_thinking_enabled_and_uses_canonical_parameters(monkeypatch):
    monkeypatch.delenv("VANNA_MAX_NEW_TOKENS", raising=False)
    vanna = _stub_vanna()

    assert vanna.submit_prompt([{"role": "user", "content": "q"}]) == "SELECT 1"
    vanna.tokenizer.apply_chat_template.assert_called_once_with(
        [{"role": "user", "content": "q"}], add_generation_prompt=True, return_tensors="pt"
    )
    assert vanna.model.generate.call_args.kwargs == {
        "max_new_tokens": 4096,
        "eos_token_id": 0,
        "do_sample": True,
        "temperature": 1,
        "top_p": 0.9,
    }


def test_vanna_environment_override_remains_effective(monkeypatch):
    monkeypatch.setenv("VANNA_MAX_NEW_TOKENS", "777")
    vanna = _stub_vanna()

    vanna.submit_prompt([{"role": "user", "content": "q"}])

    assert vanna.model.generate.call_args.kwargs["max_new_tokens"] == 777
