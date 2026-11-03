# Arc Copilot 1.0

Aplicação funcional para transformar mensagens de campo em registros confirmados, movimentações de estoque, RDO e respostas com fontes. A primeira entrega privilegia um fluxo vertical completo e uma base segura para evolução até o uso real em obra.

## O que já funciona

- Login com senha PBKDF2 e sessão HTTP-only;
- perfis trabalhador, mestre e engenheiro com autorização no backend;
- isolamento por empresa, obra e associação de usuário;
- simulador web de conversa responsivo;
- extração determinística de consumo/entrada e serviço no modo demonstração;
- pergunta de um campo ausente por vez e confirmação antes de persistir efeitos;
- idempotência pelo ID externo da mensagem;
- roteamento do webhook mock pelo número de destino;
- estoque derivado de movimentos confirmados;
- RDO diário, pendências, fechamento por mestre/engenheiro, reabertura por engenheiro e PDF;
- upload e indexação textual de TXT, PDF e DOCX;
- consulta quantitativa pelo banco e consulta documental com fontes;
- auditoria de operações críticas;
- cancelamento, estorno e correção de registros, com motivo e auditoria; o estoque é compensado por movimentos de estorno, sem apagar histórico;
- gestão de usuários pelo engenheiro: criar, trocar perfil e obras, desativar e redefinir senha, com bloqueio após tentativas de login falhas;
- busca vetorial nos documentos da obra: pgvector com índice HNSW no PostgreSQL e, no SQLite da demonstração, vetor local por hashing de palavras;
- seed completo e testes de fluxo, permissão, isolamento, estorno, usuários e busca.

## Rodar agora no Windows, sem Docker

Requer Python 3.12.

```powershell
cd arc-copilot
.\scripts\setup.ps1
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Abra `http://127.0.0.1:8000`.

Credenciais locais (todas usam `ArcDemo123!`):

- `engenheiro@arc.local`
- `mestre@arc.local`
- `trabalhador@arc.local`

Essas credenciais são apenas demonstrativas. Troque-as e defina uma `SECRET_KEY` forte antes de inserir dados reais.

## PostgreSQL/pgvector com Docker

Quando o Docker Desktop estiver instalado:

```powershell
docker compose up --build
```

O Compose inicia PostgreSQL 16 com pgvector, executa a migration, aplica o seed e publica a aplicação na porta 8000. O ambiente atual em que esta versão foi criada não possuía Docker; portanto o Compose foi escrito, mas não executado aqui.

## Comandos

Com `make` disponível:

```text
make setup    cria a venv e instala dependências
make migrate  aplica migrations
make seed     cria dados demonstrativos
make test     executa os testes
make lint     executa o Ruff
make up       sobe app + PostgreSQL
make down     encerra os containers
```

No PowerShell, os equivalentes são:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m scripts.seed
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Documentação interativa: `http://127.0.0.1:8000/docs`.

## Fluxo demonstrável

1. Entre como trabalhador.
2. Abra **Conversa** e envie `Usamos 20 sacos.`
3. Responda `Cimento` e depois `Alvenaria do segundo pavimento`.
4. Confira o resumo e confirme.
5. Veja o saldo em **Materiais** e o item no **RDO do dia**.
6. Entre como mestre para fechar o RDO.
7. Pergunte `Qual é o saldo de cimento?`; a resposta lista os movimentos usados.

## Segurança e operação real

- Defina HTTPS, segredo de sessão forte, política de backup e PostgreSQL antes do piloto.
- A autenticação atual cobre sessão local; recuperação de senha, MFA e revogação centralizada ainda não estão implementados.
- Revise papéis por obra, limites de upload e política de retenção antes de receber dados reais.
- Pela LGPD, documente finalidade, base legal, retenção e acesso a fotos, vídeos e áudios. Avise os trabalhadores e obtenha consentimento quando aplicável.
- Não registre segredos em `.env` versionado nem em logs.
- Faça análise de segurança e teste de restauração de backup antes de tratar este MVP como sistema de produção.

## Limitações honestas do MVP

- Gemini (extração, embeddings, resposta, transcrição e visão) e WhatsApp Cloud API têm adaptadores, mas nenhuma chamada externa foi validada com chave real. Não há adaptador OpenAI nem S3: arquivos ficam em disco local.
- O modo demonstração usa regras e uma transcrição simulada. Ele não deve ser apresentado como IA de produção.
- O vetor do modo demonstração mede vocabulário em comum, não significado. Busca semântica só existe com `GEMINI_API_KEY`, e vetores de modelos diferentes nunca são comparados: ao trocar de modelo, reenvie os documentos.
- O caminho pgvector foi validado em um PostgreSQL 17 com pgvector 0.8.0 (Neon, projeto descartável): migrations do zero e sobre banco legado, downgrade, busca vetorial pela API com isolamento entre obras e uso do índice HNSW no `<=>`. Não foi executado o `docker compose` nem a imagem `pgvector/pgvector:pg16`. Com filtro por obra, o planejador pode escolher varredura exata em vez do HNSW; em corpus grande, habilite `hnsw.iterative_scan` (pgvector 0.8+).
- O importador preserva e extrai documentos; o editor visual de mapeamento de modelos personalizados ainda não está implementado.
- O estorno exige o RDO do dia aberto: com o RDO fechado, o engenheiro precisa reabri-lo antes.
- Recuperação de senha por e-mail, MFA e captura de vídeo quadro a quadro permanecem fora do escopo; a senha é redefinida por um engenheiro.

Consulte [ARCHITECTURE.md](ARCHITECTURE.md) para as decisões e fronteiras técnicas.

## Demonstração pública

O `render.yaml` publica uma instância de demonstração no Render (plano gratuito) com `DEMO_MODE=true`:

1. No Render, escolha **New → Blueprint** e aponte para este repositório.
2. O serviço sobe com SQLite efêmero, dados fictícios e as três contas demonstrativas na tela de login.
3. Em `DEMO_MODE` o upload é limitado a 1 MB, as contas fixas não podem ser desativadas nem ter a senha trocada, e os dados voltam ao seed a cada reinício.

Nunca use `DEMO_MODE` com dados reais.

## Próximo passo

Rodar um piloto controlado com dados não sensíveis de obra, para validar o vocabulário real das mensagens, os campos obrigatórios do RDO e as regras de estoque. Só depois conectar a WhatsApp Cloud API e um provedor de IA, com testes baseados em mensagens reais anonimizadas.

