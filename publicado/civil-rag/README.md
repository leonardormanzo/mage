# Civil RAG

Consulta a documentos técnicos de obra (memoriais, cadernos de encargos, laudos) com recuperação vetorial. A resposta cita o arquivo e a página de onde a informação saiu, e o modelo é instruído a dizer que a informação não consta quando ela não está nos documentos.

**Estado:** protótipo funcional. Não é um produto em operação.

## Como funciona

```
Documento (PDF, DOCX, TXT) → trechos de 600 caracteres com 100 de sobreposição
  → embeddings Gemini (768 dimensões) → PostgreSQL + pgvector, separado por obra
Pergunta → embedding → top 3 por distância de cosseno, filtrado pela obra
  → prompt com os trechos e suas fontes → resposta citando arquivo e página
```

| Arquivo | Papel |
|---|---|
| `civil_rag_saas/app.py` | API FastAPI e interface web |
| `civil_rag_saas/extractor.py` | Extração de texto por página |
| `civil_rag_saas/chunking.py` | Divisão em trechos com sobreposição |
| `civil_rag_saas/rag_engine.py` | Embeddings, busca e geração com fallback entre modelos |
| `civil_rag_saas/database.py` | Tabelas, índice HNSW e busca no pgvector |
| `eval/` | Avaliação da recuperação |

## Decisões técnicas

- **Busca vetorial no próprio PostgreSQL.** O pgvector evita um banco vetorial separado e permite filtrar por obra na mesma consulta. Custo: depende de um Postgres com a extensão instalada.
- **Embeddings com tipo de tarefa.** Trechos são vetorizados como `RETRIEVAL_DOCUMENT` e perguntas como `RETRIEVAL_QUERY`.
- **Dimensão fixada em 768.** O `gemini-embedding-001` devolve 3072 dimensões por padrão, e a coluna do banco é `vector(768)`. A dimensão agora é pedida explicitamente; antes, a inserção falharia por incompatibilidade.
- **Recusa explícita.** O prompt manda responder que a informação não consta quando os trechos não a contêm.

## Avaliação da recuperação

O conjunto `eval/golden.jsonl` tem 30 perguntas escritas com outras palavras, cada uma com o arquivo e o trecho de texto que contém a resposta. O script mede se esse trecho aparece entre os primeiros resultados.

```bash
python -m eval.run_eval --retriever bm25     # linha de base lexical, roda sem chave
python -m eval.run_eval --retriever gemini   # embeddings da aplicação, precisa de GEMINI_API_KEY
```

| Recuperador | hit@1 | hit@3 | hit@5 | MRR@5 |
|---|---|---|---|---|
| BM25 (linha de base) | 87% | 97% | 100% | 0,91 |
| Gemini embeddings | a medir: rode o comando acima | | | |

A aplicação usa top 3, então **hit@3** é a métrica que mais importa. Os resultados por pergunta ficam em `eval/resultados/`.

**Limites da avaliação:** o corpus é pequeno (3 documentos, 17 trechos) e fictício, então os números servem para comparar recuperadores e detectar regressões, não para prever o desempenho em documentos reais. A avaliação mede só a recuperação; a qualidade e a fidelidade da resposta gerada ainda não são medidas.

## Como rodar

Requer Python 3.11+ e um PostgreSQL com pgvector.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env            # preencha GEMINI_API_KEY e DATABASE_URL
uvicorn civil_rag_saas.app:app --reload
```

Abra `http://127.0.0.1:8000`. Há um memorial de exemplo em `civil_rag_saas/exemplos/`.

Testes (não precisam de chave nem de banco):

```bash
python -m pytest
```

## Limitações

- Fatiamento por caracteres, sem respeitar parágrafos ou itens numerados.
- Sem autenticação: qualquer pessoa com acesso à API consulta qualquer obra.
- Uma chamada de embedding por trecho, sem envio em lote.
- Os documentos de exemplo e de avaliação são fictícios.
