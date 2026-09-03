from logging import getLogger
from typing import Protocol, TypeVar, Type
import requests

import openai
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMService(Protocol):
    def generate_response(self, prompt: str) -> str:
        ...

    def generate_structured_response(self, prompt: str, response_model: type[T]) -> T:
        ...


class OpenAIService(LLMService):
    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.logger = getLogger("OpenAIService")

    def generate_response(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.8
        )

        self.logger.info("Generated response with %d tokens", response.usage.total_tokens)
        return response.output_text

    def generate_structured_response(self, prompt: str, response_model: type[T]) -> T:
        response = self.client.responses.parse(
            model=self.model,
            input=prompt,
            text_format=response_model)

        self.logger.info("Generated structured response with %d tokens", response.usage.total_tokens)
        if (parsed := response.output_parsed) is not None:
            return parsed

        raise ValueError("Failed to parse structured response")


class OllamaService(LLMService):
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate_response(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        response.raise_for_status()
        return response.json()["response"]

    def generate_structured_response(self, prompt: str, response_model: Type[T]) -> T:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": response_model.model_json_schema()
            },
            timeout=300
        )

        response.raise_for_status()
        data = response.json()

        raw_output = data.get("response")
        if raw_output is None:
            raise RuntimeError("Resposta inesperada da API do Ollama.")

        try:
            return response_model.model_validate_json(raw_output)
        except Exception as e:
            raise RuntimeError(
                f"Falha ao validar JSON retornado.\nOutput:\n{raw_output}\nErro:\n{e}"
            )