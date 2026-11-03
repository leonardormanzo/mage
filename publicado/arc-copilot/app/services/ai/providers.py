from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from abc import ABC, abstractmethod

from app.core.config import EMBEDDING_DIMENSION


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, path: str) -> str:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    """Gera vetores de EMBEDDING_DIMENSION posições.

    `name` identifica o espaço vetorial: só se comparam vetores do mesmo `name`.
    `min_score` é a similaridade de cosseno mínima para considerar um trecho relevante.
    """

    name: str
    min_score: float

    @abstractmethod
    def embed(self, text: str, task: str = "document") -> list[float]:
        """`task` é "document" para trechos indexados e "query" para perguntas."""
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


_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "que qual quais como onde quando quem uma uns umas para por com sem sobre entre dos das nos nas "
    "aos pelo pela pelos pelas ser foi sao tem tinha este esta esse essa isso aqui ali mais menos "
    "muito pouco alem apos ate desde contra seu sua seus suas nao".split()
)
_STEM_LENGTH = 6


def _tokens(text: str) -> list[str]:
    folded = "".join(
        char
        for char in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(char) != "Mn"
    )
    return [
        token[:_STEM_LENGTH]
        for token in _TOKEN.findall(folded)
        if len(token) >= 3 and token not in _STOPWORDS
    ]


class MockEmbeddingProvider(EmbeddingProvider):
    """Vetor local por hashing de palavras (bag-of-words), sem chave nem rede.

    Mede sobreposição de vocabulário, não significado: serve para demonstração e testes.
    """

    name = "hashing-v1"
    min_score = 0.15

    def embed(self, text: str, task: str = "document") -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSION
        for token in _tokens(text):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSION
            vector[index] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class MockVisionProvider(VisionProvider):
    def describe(self, path: str) -> str:
        return "Imagem preservada. Descrição automática indisponível no modo demonstração."


class MockLLMProvider(LLMProvider):
    def answer(self, prompt: str, context: list[str]) -> str:
        if not context:
            return "Não encontrei esse dado nos registros da obra."
        return context[0]


class GeminiProvider(TranscriptionProvider, EmbeddingProvider, VisionProvider, LLMProvider):
    name = "gemini-embedding-001-768"
    min_score = 0.4
    _TASKS = {"document": "retrieval_document", "query": "retrieval_query"}

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

    def embed(self, text: str, task: str = "document") -> list[float]:
        result = self.genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type=self._TASKS[task],
            output_dimensionality=EMBEDDING_DIMENSION,
        )
        return list(result["embedding"])

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
