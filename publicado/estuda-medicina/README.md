# Estuda Medicina

Assistente de estudos para alunos de medicina: lê questões por foto e explica a
resposta, ajuda a estudar buscando em conteúdo indexado (RAG) e permite buscar
provas antigas de um banco de questões. Página única, sem backend — pensado
mobile-first para funcionar bem no navegador do celular.

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

## Proposta de precificação institucional

A ideia é que o valor cobrado da instituição cubra o custo real de tokens da
API mais uma margem pequena — não é um produto para gerar lucro alto, e sim
para se pagar e permitir manutenção. Estimativa com preços atuais da
Anthropic (Claude Sonnet 5: US$ 3 / 1M tokens de entrada, US$ 15 / 1M tokens
de saída):

| Interação | Entrada estimada | Saída estimada | Custo por interação |
|---|---|---|---|
| Foto de questão (imagem + explicação) | ~1.800 tokens | ~600 tokens | ≈ US$ 0,014 |
| Pergunta de estudo (RAG, poucos trechos) | ~2.500 tokens | ~400 tokens | ≈ US$ 0,014 |
| Busca de prova antiga (sem IA) | — | — | US$ 0,00 |

Considerando um uso médio de ~50 interações com IA por aluno/mês (fotos +
perguntas de estudo), o custo de token fica em torno de **US$ 0,70/aluno/mês**.
Com uma margem mínima de 30–40% para cobrir infraestrutura e manutenção, o
valor institucional sugerido fica na faixa de **US$ 1,00 a US$ 1,20 por aluno
ativo/mês** (equivalente a ~R$ 5,50–6,60 no câmbio atual, ajustável conforme
volume real e negociação por número de alunos). Cobrança por instituição
(faturamento agregado, não por aluno individual) simplifica tanto a operação
quanto a integração com a área financeira da faculdade.

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
