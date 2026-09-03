from dataclasses import dataclass

from dotenv import load_dotenv
from torch.cuda import temperature

from benchmark_generator.llm.llm_service import LLMService, OpenAIService
from benchmark_generator.llm.prompt_builder import PromptBuilder


@dataclass(frozen=True)
class LLMContext:
    """
    Central configuration for all LLM-based generators.
    """
    llm_service: LLMService
    prompt_builder: PromptBuilder


def get_default_llm_context() -> LLMContext:
    """
    Default LLM context used across the codebase.
    """
    import os
    load_dotenv()
    return LLMContext(
        llm_service=OpenAIService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-5-mini",
        ),
        prompt_builder=PromptBuilder(),
    )

default_llm_context = get_default_llm_context()