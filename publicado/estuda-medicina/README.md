# Estuda Medicina

Assistente de estudos para alunos de medicina: lê questões por foto e explica a
resposta, ajuda a estudar buscando em conteúdo indexado (RAG), permite buscar
provas antigas de um banco de questões e cadastra os alunos com acesso. Página
única, sem backend — pensado mobile-first para funcionar bem no navegador do
celular.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer
servidor estático:

```sh
npx serve .
```

## O que já funciona de verdade nesta demo

- **Busca de provas antigas**: filtra o banco de exemplo (`examBank`, dentro
  do próprio `index.html`) por instituição, disciplina, ano ou palavra-chave.
- **Busca nos materiais de estudo (RAG)**: a etapa de recuperação — encontrar
  os trechos relevantes para a pergunta do aluno — roda de verdade no
  navegador, sobre 5 textos de exemplo (`studyDocs`).
- **Cadastro de alunos**: cadastrar, ativar/inativar e remover aluno funciona
  de verdade e persiste entre recarregamentos — mas só neste navegador, via
  `localStorage` (ver limites abaixo).
- Interface completa, responsiva, com tema claro/escuro automático.

## O que é simulado (modo demonstração)

- **Leitura da foto da questão**: a foto é exibida na tela, mas o texto da
  questão, as alternativas e a explicação vêm de um banco de 3 respostas de
  exemplo (`demoQuestionBank`) — a IA real ainda não lê a imagem enviada. Em
  produção isso exigiria um backend (função serverless, por exemplo) que
  recebe a imagem e chama a API da Claude com visão, sem expor a chave de API
  no navegador.
- **Síntese da resposta de estudo**: depois de encontrar os trechos
  relevantes (isso é real), o resumo final "gerado pela IA" é um texto
  montado a partir do próprio trecho, não uma resposta gerada por modelo.
- Toda resposta simulada aparece marcada com o selo **"demo"** na interface —
  nunca finge ser uma resposta real sem avisar.
- **Vídeo ao vivo**: não está nesta versão. Responder perguntas por vídeo em
  tempo real exige infraestrutura de streaming + um modelo multimodal com
  suporte a vídeo, o que é mais caro e complexo que a leitura de foto — fica
  documentado como próxima fase.
- **Cadastro de alunos** funciona, mas com as limitações de rodar só no
  navegador: não sincroniza entre dispositivos (o mesmo aluno cadastrado no
  computador da secretaria não aparece no celular de outra pessoa), não tem
  login/autenticação, qualquer pessoa com acesso ao navegador pode
  editar/apagar cadastros, e os dados somem se o usuário limpar os dados do
  site. Serve para validar o fluxo (campos, ativar/inativar, busca) antes de
  ligar a um banco de dados de verdade.

## Como conectar a IA de verdade

1. Criar um backend leve (função serverless ou servidor simples) que recebe a
   foto/pergunta do app e chama a API da Anthropic — a chave de API **nunca**
   deve ficar no navegador.
2. Modelo recomendado: **Claude Sonnet 5** (`claude-sonnet-5`) para leitura de
   foto e RAG — boa leitura de imagem e resposta explicativa a um custo bem
   menor que o topo de linha. Para casos mais difíceis (provas dissertativas
   longas, questões ambíguas), considerar **Claude Opus 5** (`claude-opus-5`)
   como opção de maior qualidade.
3. Trocar `mockAnalyzeQuestionPhoto()`, `mockSynthesizeAnswer()` e o
   `examBank` por chamadas reais à API / ao banco de dados de provas da
   instituição.

## Proposta de banco de dados real de alunos

Quando o backend existir, o cadastro de alunos deixa de ser `localStorage` e
vira tabelas de verdade (ex: Postgres/SQLite). Estrutura mínima sugerida:

- **instituicoes**: `id`, `nome`, `plano` (define limite de interações/mês),
  `status` (ativa/inativa).
- **alunos**: `id`, `instituicao_id`, `nome`, `email` (único, idealmente
  validado pelo domínio institucional), `curso`, `periodo`, `status`
  (ativo/inativo/pendente), `criado_em`.
- **uso_mensal** (ou log de interações): `aluno_id`, `tipo` (foto/estudo),
  `tokens_entrada`, `tokens_saida`, `custo_estimado`, `criado_em` — essa
  tabela é o que transforma a "proposta de precificação" abaixo em uma
  cobrança real, medida por instituição.

Autenticação pode começar simples (login por e-mail institucional + link
mágico, sem senha) já que o público é fechado (alunos matriculados).

## Proposta de precificação institucional

O custo real de token é bem menor do que um preço "acessível" para o aluno —
então há bastante espaço entre cobrir custo e cobrar um valor confortável.
Estimativa com preços atuais da Anthropic (Claude Sonnet 5: US$ 3 / 1M tokens
de entrada, US$ 15 / 1M tokens de saída):

| Interação | Entrada estimada | Saída estimada | Custo por interação |
|---|---|---|---|
| Foto de questão (imagem + explicação) | ~1.800 tokens | ~600 tokens | ≈ US$ 0,014 |
| Pergunta de estudo (RAG, poucos trechos) | ~2.500 tokens | ~400 tokens | ≈ US$ 0,014 |
| Busca de prova antiga (sem IA) | — | — | US$ 0,00 |

### Custo estimado por aluno/mês

| Cenário | Uso/mês | Custo em US$ | Custo em R$ (câmbio ~R$ 5,50) |
|---|---|---|---|
| Moderado, preço promocional (até ago/2026) | ~50 interações | ≈ US$ 0,47 | ≈ R$ 2,56 |
| Moderado, preço padrão (após a promoção) | ~50 interações | ≈ US$ 0,70 | ≈ R$ 3,85 |
| Pesado (época de prova, uso em dobro) | ~100 interações | ≈ US$ 1,40 | ≈ R$ 7,70 |

### Preço sugerido: R$ 30/aluno ativo/mês

Nos três cenários acima, R$ 30/mês cobre o custo de token com folga:

| Cenário | Custo | Lucro | Margem |
|---|---|---|---|
| Moderado, preço promo | R$ 2,56 | R$ 27,44 | ~91% |
| Moderado, preço padrão | R$ 3,85 | R$ 26,15 | ~87% |
| Pesado, preço padrão | R$ 7,70 | R$ 22,30 | ~74% |

Mesmo no pior cenário (uso pesado, sem desconto promocional), sobra ~74% de
margem — dá para descontar taxas de gateway de pagamento (~5% + taxa fixa,
se cobrar direto do aluno) e um custo fixo de hospedagem do backend sem
comprometer o resultado.

**Isso não é mais "custo + margem mínima"** — R$ 30/aluno/mês é um preço de
produto normal, bem acima do que cobriria só o custo de operação (que ficaria
na faixa de R$ 5,50–6,60/aluno/mês, com margem de 30–40%, se a prioridade
fosse só se pagar). Cobrança por instituição (faturamento agregado, não por
aluno individual) simplifica tanto a operação quanto a integração com a área
financeira da faculdade, e a instituição pode repassar R$ 30 ao aluno ou
absorver parte do custo, dependendo do modelo de negócio escolhido.

Esses números são estimativas de planejamento, não uma calculadora em tempo
real — o MVP não tem lógica de cobrança implementada (ver "Falta para
terminar").

## Falta para terminar

- Conectar a leitura de foto a uma chamada real da API da Claude (visão),
  atrás de um backend que protege a chave de API.
- Indexar conteúdo médico real (apostilas, resumos atualizados) em vez dos 5
  textos de exemplo, e gerar a síntese final com o modelo em vez de recorte
  de texto.
- Plugar o banco de dados real de provas antigas da instituição no lugar do
  `examBank` de exemplo.
- Vídeo ao vivo: avaliar viabilidade e custo de um modelo multimodal com
  suporte a vídeo antes de priorizar essa fase.
- Cobrança institucional: hoje é só a proposta de valor acima, em texto —
  ainda não há gateway de pagamento nem medição de uso real no código.
- Cadastro de alunos: migrar de `localStorage` para o banco de dados real
  (schema proposto acima), com autenticação e sincronização entre
  dispositivos — hoje é só uma demonstração local do fluxo.
