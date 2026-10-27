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
5. **Integrações nas bordas.** Interfaces permitem trocar mocks por OpenAI, S3 e WhatsApp Cloud API sem deslocar regras do domínio.
6. **SQLite não é produção.** Ele existe para iniciar e testar sem Docker. PostgreSQL/pgvector é o destino operacional.

## Estados

`received → processing → incomplete → awaiting_confirmation → confirmed → included_in_rdo → closed`

Também existem `corrected` e `cancelled`; transições inválidas são recusadas no backend.

## Limites atuais

- O mecanismo local de documentos é busca textual rastreável, não embedding semântico real.
- O adaptador OpenAI está declarado, porém chamadas pagas não foram ativadas nem validadas.
- Upload extrai texto de PDF/DOCX, mas mapeamento visual de modelos ainda é fase posterior.
- Mídia é modelada; a primeira fatia simula transcrição para validar o fluxo sem chave.
- O webhook Meta real depende de credenciais, assinatura e payloads reais do número aprovado.

