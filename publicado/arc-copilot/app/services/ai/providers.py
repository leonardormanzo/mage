from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, path: str) -> str:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class VisionProvider(ABC):
    @abstractmethod
    def describe(self, path: str) -> str:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    def answer(self, prompt: str, context: list[str]) -> str:
        raise NotImplementedError


class MockTranscriptionProvider(TranscriptionProvider):
    def transcribe(self, path: str) -> str:
        return "Usamos 20 sacos de cimento na alvenaria do segundo pavimento."


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic local vector for demos; not a semantic production embedding."""

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.lower().encode()).digest()
        values = [(byte - 127.5) / 127.5 for byte in digest[:16]]
        norm = math.sqrt(sum(value * value for value in values)) or 1
        return [value / norm for value in values]


class MockVisionProvider(VisionProvider):
    def describe(self, path: str) -> str:
        return "Imagem preservada. Descrição automática indisponível no modo demonstração."


class MockLLMProvider(LLMProvider):
    def answer(self, prompt: str, context: list[str]) -> str:
        if not context:
            return "Não encontrei esse dado nos registros da obra."
        return context[0]


class GeminiProvider(TranscriptionProvider, EmbeddingProvider, VisionProvider, LLMProvider):
    def __init__(self, api_key: str | None):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada")
        import google.generativeai as genai
        self.genai = genai
        self.genai.configure(api_key=api_key)

    def transcribe(self, path: str) -> str:
        audio_file = self.genai.upload_file(path=path)
        model = self.genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content([
            "Por favor, transcreva o áudio de forma literal.",
            audio_file
        ])
        audio_file.delete()
        return response.text

    def embed(self, text: str) -> list[float]:
        result = self.genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]

    def describe(self, path: str) -> str:
        img_file = self.genai.upload_file(path=path)
        model = self.genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content([
            "Descreva esta imagem de obra de forma concisa. Se for sobre um serviço ou ocorrência, detalhe os materiais, equipamentos e situação geral visível.",
            img_file
        ])
        img_file.delete()
        return response.text

    def answer(self, prompt: str, context: list[str]) -> str:
        model = self.genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction="Você é o assistente Arc Copilot. Baseie-se APENAS no contexto fornecido para responder. Se a resposta não estiver no contexto, responda que não encontrou."
        )
        
        context_parts = []
        if context:
            context_str = "\n".join(f"- {c}" for c in context)
            context_parts.append(f"Contexto disponível:\n{context_str}")
        else:
            return "Não encontrei esse dado nos registros da obra."
            
        context_parts.append(prompt)
        
        response = model.generate_content(
            context_parts,
            generation_config=self.genai.types.GenerationConfig(temperature=0.0)
        )
        return response.text
