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
- seed completo e testes de fluxo, permissão e isolamento.

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

- OpenAI, visão, transcrição real, S3 e WhatsApp Cloud API possuem contratos/adaptadores, mas não chamadas externas validadas.
- O modo demonstração usa regras e uma transcrição simulada. Ele não deve ser apresentado como IA de produção.
- A busca documental local é textual; pgvector está previsto no container, mas a indexação vetorial real é próxima fase.
- O importador preserva e extrai documentos; o editor visual de mapeamento de modelos personalizados ainda não está implementado.
- Correção/estorno completo na interface, gestão administrativa de usuários e captura de vídeo quadro a quadro permanecem fora da primeira fatia.

Consulte [ARCHITECTURE.md](ARCHITECTURE.md) para as decisões e fronteiras técnicas.

## Próximo passo mais importante

Executar um piloto controlado com dados não sensíveis da obra: validar o vocabulário real das mensagens, campos obrigatórios do seu RDO e regras de estoque. Só depois conectar a WhatsApp Cloud API e um provedor de IA, com conjunto de testes baseado nas mensagens reais anonimizadas.

