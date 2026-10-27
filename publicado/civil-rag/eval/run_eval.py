"""Avaliação da recuperação (retrieval) do Civil RAG.

Para cada pergunta do conjunto `golden.jsonl`, recupera os trechos mais
próximos do corpus e verifica se algum deles é do arquivo esperado e contém o
trecho de evidência. Mede só a recuperação, não a resposta gerada pelo LLM.

Uso (a partir da raiz do repositório):
    python -m eval.run_eval --retriever bm25      # roda sem chave, linha de base lexical
    python -m eval.run_eval --retriever gemini    # usa GEMINI_API_KEY do .env

Métricas:
    hit@k  fração das perguntas com o trecho certo entre os k primeiros
    MRR@5  média de 1/posição do primeiro trecho certo (0 se fora do top 5)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from civil_rag_saas.chunking import fatiar_texto

RAIZ = Path(__file__).resolve().parent
CORPUS = RAIZ / "corpus"
GOLDEN = RAIZ / "golden.jsonl"
CACHE = RAIZ / "cache_embeddings.json"
RESULTADOS = RAIZ / "resultados"
KS = (1, 3, 5)

STOPWORDS = set(
    "a o as os de da do das dos e em no na nos nas um uma para por com que qual quais "
    "como quanto quantos quantas ser sera serao deve devem precisa ter tem vai vao "
    "se ao aos à às ou mais seu sua isso esse essa nesse nessa".split()
)


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip()


def carregar_corpus() -> list[dict]:
    """Divide cada documento do corpus com o mesmo fatiamento usado na indexação."""
    trechos = []
    for arq in sorted(CORPUS.glob("*.txt")):
        texto = arq.read_text(encoding="utf-8")
        for i, t in enumerate(fatiar_texto(texto)):
            trechos.append({"arquivo": arq.name, "indice": i, "texto": t})
    return trechos


def carregar_golden() -> list[dict]:
    with GOLDEN.open(encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def trecho_correto(trecho: dict, item: dict) -> bool:
    return trecho["arquivo"] == item["arquivo"] and normalizar(item["evidencia"]) in normalizar(trecho["texto"])


# --- Recuperadores ----------------------------------------------------------

def tokens(texto: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if t not in STOPWORDS]


class BM25:
    """BM25 clássico (k1=1.5, b=0.75), usado como linha de base lexical."""

    def __init__(self, trechos: list[dict], k1: float = 1.5, b: float = 0.75):
        self.docs = [Counter(tokens(t["texto"])) for t in trechos]
        self.lens = [sum(d.values()) for d in self.docs]
        self.media = sum(self.lens) / len(self.lens)
        n = len(self.docs)
        df = Counter(term for d in self.docs for term in d)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.k1, self.b = k1, b

    def ranking(self, pergunta: str) -> list[int]:
        q = tokens(pergunta)
        scores = []
        for i, d in enumerate(self.docs):
            s = 0.0
            for t in q:
                if t in d:
                    tf = d[t]
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.lens[i] / self.media))
            scores.append(s)
        return sorted(range(len(scores)), key=lambda i: -scores[i])


def cosseno(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return num / den if den else 0.0


class Gemini:
    """Mesmos embeddings da aplicação; o cosseno aqui equivale ao `<=>` do pgvector."""

    def __init__(self, trechos: list[dict]):
        from civil_rag_saas.rag_engine import EMBEDDING_DIM, EMBEDDING_MODEL, gerar_embedding

        self._embed = gerar_embedding
        self._tag = f"{EMBEDDING_MODEL}:{EMBEDDING_DIM}"
        self.cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        self.vetores = [self._vetor(t["texto"], "RETRIEVAL_DOCUMENT") for t in trechos]

    def _vetor(self, texto: str, tarefa: str) -> list[float]:
        chave = hashlib.sha256(f"{self._tag}|{tarefa}|{texto}".encode()).hexdigest()
        if chave not in self.cache:
            self.cache[chave] = self._embed(texto, tarefa)
            CACHE.write_text(json.dumps(self.cache), encoding="utf-8")
        return self.cache[chave]

    def ranking(self, pergunta: str) -> list[int]:
        q = self._vetor(pergunta, "RETRIEVAL_QUERY")
        scores = [cosseno(q, v) for v in self.vetores]
        return sorted(range(len(scores)), key=lambda i: -scores[i])


# --- Avaliação --------------------------------------------------------------

def avaliar(nome: str, recuperador, trechos: list[dict], golden: list[dict]) -> dict:
    por_pergunta = []
    for item in golden:
        ranking = recuperador.ranking(item["pergunta"])
        posicao = next((p for p, i in enumerate(ranking, start=1) if trecho_correto(trechos[i], item)), None)
        por_pergunta.append({"id": item["id"], "pergunta": item["pergunta"], "posicao": posicao})

    n = len(golden)
    metricas = {f"hit@{k}": sum(1 for r in por_pergunta if r["posicao"] and r["posicao"] <= k) / n for k in KS}
    metricas["MRR@5"] = sum(1 / r["posicao"] for r in por_pergunta if r["posicao"] and r["posicao"] <= 5) / n
    return {"recuperador": nome, "perguntas": n, "trechos": len(trechos), "metricas": metricas, "por_pergunta": por_pergunta}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retriever", choices=["bm25", "gemini"], default="bm25")
    args = parser.parse_args()

    trechos = carregar_corpus()
    golden = carregar_golden()
    recuperador = BM25(trechos) if args.retriever == "bm25" else Gemini(trechos)
    resultado = avaliar(args.retriever, recuperador, trechos, golden)

    RESULTADOS.mkdir(exist_ok=True)
    (RESULTADOS / f"{args.retriever}.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    m = resultado["metricas"]
    print(f"Recuperador: {args.retriever} | {resultado['perguntas']} perguntas | {resultado['trechos']} trechos")
    print("| hit@1 | hit@3 | hit@5 | MRR@5 |")
    print("|---|---|---|---|")
    print(f"| {m['hit@1']:.0%} | {m['hit@3']:.0%} | {m['hit@5']:.0%} | {m['MRR@5']:.2f} |")
    falhas = [r for r in resultado["por_pergunta"] if not r["posicao"] or r["posicao"] > 3]
    if falhas:
        print("\nFora do top 3:")
        for r in falhas:
            print(f"  {r['id']} (posição {r['posicao']}): {r['pergunta']}")


if __name__ == "__main__":
    main()
