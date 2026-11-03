# Arquitetura — Arc Copilot 1.0

## Visão

O sistema é um monólito modular. FastAPI atende a API e a interface Jinja2; os serviços de domínio controlam extração, confirmação, estoque, RDO, consulta e auditoria. SQLAlchemy mantém o mesmo modelo em SQLite (demonstração) e PostgreSQL (Docker).

```text
Web / futuro WhatsApp
        │
        ▼
 FastAPI + autorização ─────► auditoria
        │
        ├── fluxo de registros ─► confirmação ─► RDO
        │                                  └───► movimentos de estoque
        ├── roteador de consultas ─► banco estruturado (quantidades)
        │                        └─► documentos/registros (texto)
        └── provedores substituíveis: mensagem, transcrição, visão, embeddings e LLM
```

## Decisões

1. **Escopo sempre explícito.** Entidades operacionais carregam `company_id` e `project_id`; as consultas de API filtram ambos e verificam associação do usuário.
2. **Saldo derivado.** Não existe campo “saldo atual”; entradas, consumos, ajustes e estornos compõem o saldo.
3. **Confirmação antes do efeito.** Extrações incompletas fazem uma pergunta por vez. Somente o estado confirmado cria movimento e item do RDO.
4. **RAG não calcula.** Perguntas quantitativas vão ao banco estruturado e devolvem os movimentos usados. Busca textual fica separada.
5. **Integrações nas bordas.** Interfaces permitem trocar mocks por Gemini e WhatsApp Cloud API sem deslocar regras do domínio.
6. **Correção por compensação.** Estornar e corrigir não editam nem apagam movimentos: criam movimentos `reversal` ligados ao original, e o registro antigo passa a `reversed` ou `corrected`. Totais ignoram movimentos já estornados.
7. **Vetores só se comparam entre si dentro do mesmo embedder.** Cada trecho guarda o nome do embedder em `metadata_json`; a busca filtra por ele. Colunas: `vector(768)` com índice HNSW no PostgreSQL e JSON no SQLite, com similaridade calculada em Python.
8. **SQLite não é produção.** Ele existe para iniciar e testar sem Docker. PostgreSQL/pgvector é o destino operacional.

## Estados

`received → processing → incomplete → awaiting_confirmation → confirmed → included_in_rdo → closed`

Também existem `cancelled` (antes da confirmação), `reversed` (estorno) e `corrected` (substituído por uma nova versão ligada por `corrected_from_id`); transições inválidas são recusadas no backend. Estorno e correção exigem o RDO do dia aberto.

## Limites atuais

- Sem `GEMINI_API_KEY`, o vetor é um hashing de palavras: mede vocabulário em comum, não significado. Os adaptadores Gemini não foram validados com chave real.
- O caminho pgvector (migrations, busca por `<=>`, índice HNSW) foi validado em PostgreSQL 17 + pgvector 0.8.0; o `docker compose` não foi executado. Com filtro por obra, o planejador pode ignorar o HNSW; em corpus grande, considere `hnsw.iterative_scan`.
- O bloqueio de tentativas de login e o limite do link de campo ficam na memória do processo e valem para um único worker.
- Upload extrai texto de PDF/DOCX, mas mapeamento visual de modelos ainda é fase posterior.
- Mídia é modelada; a primeira fatia simula transcrição para validar o fluxo sem chave.
- O webhook Meta real depende de credenciais, assinatura e payloads reais do número aprovado.

