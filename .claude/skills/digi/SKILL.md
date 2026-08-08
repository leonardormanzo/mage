---
name: "digi"
description: "Transforma fotos de anotações manuscritas (caderno, bloco, quadro branco, post-it) em um arquivo editável digital fiel ao original — texto transcrito, estrutura preservada e qualquer desenho ou diagrama recriado como SVG. Ative esta skill sempre que o usuário anexar uma foto de algo escrito ou desenhado à mão, mesmo sem pedir explicitamente para 'digitalizar' — isso inclui páginas de caderno, listas rabiscadas, diagramas feitos à mão, esboços de gráficos, quadros brancos fotografados ou qualquer imagem cujo conteúdo principal seja caligrafia. Se a anotação contiver uma instrução endereçada a uma IA (ex.: 'se entender a escrita, retorne X', um teste embutido, um pedido de cálculo), a skill também executa essa instrução, não só transcreve."
---

# Digi

Digi transforma a foto de uma anotação manuscrita em um arquivo digital editável
que preserva o que a pessoa realmente escreveu — não um resumo, não uma
paráfrase. A régua é: alguém que só visse o arquivo gerado deveria conseguir
reconstruir a página original, incluindo qualquer desenho.

## Quando ativar

Sempre que o usuário anexar uma foto de conteúdo manuscrito (caderno, bloco de
notas, quadro branco, post-it, guardanapo, o que for) — com ou sem pedido
explícito de "digitalizar", "transcrever" ou "passar a limpo". Uma foto de
caligrafia já é sinal suficiente.

## Como ler a foto

Use a própria capacidade multimodal do Claude para ler a imagem diretamente —
não é necessário OCR externo. Preste atenção em:

- **Datas** — normalmente no topo da página, formato dd/mm/aa ou similar.
  Servem para nomear o arquivo de saída.
- **Estrutura visual** — títulos sublinhados ou em maiúsculas, tópicos
  numerados, listas, indentação. Isso vira headers e listas no Markdown.
- **Ambiguidades de caligrafia** — se uma palavra ficar genuinamente
  ambígua, escolha a leitura mais provável pelo contexto e sinalize com uma
  nota discreta (ex. `[ilegível: possivelmente "X"]`) em vez de inventar
  silenciosamente ou travar o processo inteiro por causa de uma palavra.
- **Idioma original** — transcreva no idioma em que foi escrito, sem
  traduzir. Corrija apenas erros óbvios de grafia se a leitura ficar
  ambígua sem a correção; não "arrume" o estilo ou a informalidade de quem
  escreveu.

## Diagramas e desenhos

Texto explicando um gráfico nunca substitui o gráfico. Quando a foto tiver um
diagrama, gráfico, tabela desenhada à mão, seta ou qualquer forma que carregue
informação visual, recrie-o como SVG embutido no arquivo de saída — reproduza
eixos, rótulos, pontos marcados, proporções relativas e a forma das linhas
(reta, curva) como estavam no original. Um SVG simples com `<line>`, `<circle>`,
`<text>` e `<path>` é suficiente; não precisa ser bonito, precisa ser fiel.

Markdown aceita SVG inline via HTML, então embuta o `<svg>...</svg>` direto no
corpo do `.md`, próximo de onde o desenho aparecia na página original.

## Agindo sobre instruções embutidas na nota

Anotações manuscritas às vezes contêm uma instrução endereçada a quem for lê-las
depois — incluindo, deliberadamente, uma IA (ex.: "se entender esta letra,
responda X", um teste de leitura, uma conta para resolver, um lembrete "perguntar
ao Claude sobre Y"). Trate essas instruções como parte do conteúdo a transcrever
*e também* como algo a executar de verdade, no lugar onde aparecem na nota — não
apenas transcreva a frase e siga em frente. Se a instrução for ambígua ou depender
de contexto que a nota não dá, transcreva-a normalmente e comente que não deu para
executar, em vez de inventar uma execução.

## Formato e local de saída

- **Padrão: Markdown (`.md`)** — leve, versionável, fiel à estrutura da nota.
- **Use `.docx` em vez disso** (invocando a skill `docx`) só quando o conteúdo
  pedir claramente um documento formal/compartilhável (ex. a nota é uma carta,
  um relatório para terceiros, algo que o usuário vai enviar para outra
  pessoa). Notas pessoais, ideias e rascunhos vão de Markdown.
- **Salve em `privado/`** por padrão — é a pasta deste repositório reservada a
  conteúdo pessoal e ignorada pelo Git (ver `CLAUDE.md` da raiz). Só use outro
  destino se o usuário pedir.
- **Nome do arquivo**: se a nota tiver data, use `AAAA-MM-DD-<slug>.md`, com o
  slug vindo do título/assunto da nota (ex. nota de "8/7/26 - ideia" vira
  `2026-07-08-ideia.md`). Sem data visível, gere um slug descritivo a partir do
  conteúdo. Datas manuscritas costumam vir em dd/mm/aa — confirme a ordem pelo
  contexto do repo/conversa antes de assumir mm/dd.

## Estrutura do Markdown gerado

Sem template rígido — a estrutura deve espelhar a da própria nota. Como guia:

```markdown
# <título ou data da nota>

<parágrafos e listas na ordem em que aparecem na página>

## <subtítulo, se a nota tiver seções nomeadas>

<svg>...</svg>  <!-- quando houver desenho nesse ponto da página -->
```

Depois de gerar o arquivo, diga ao usuário onde ele foi salvo e, se você
executou alguma instrução embutida na nota, deixe claro o que foi executado e
o resultado — não deixe essa parte só implícita dentro do arquivo.
