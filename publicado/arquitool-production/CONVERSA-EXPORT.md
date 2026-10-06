# Arquitool Production — Export da Conversa

Registro do brainstorm, PRD, arquitetura e prompt de mockup definidos para o
app de vistoria de obra por IA.

## 1. Brainstorm inicial

Ideia: um app que usa IA para identificar problemas em obra a partir de foto.
Opções levantadas:

1. Inspeção de segurança (EPI/EPC) — compliance NR-18/NR-35.
2. Diagnóstico de patologias construtivas — trinca, umidade, mofo, eflorescência.
3. Checklist de vistoria de obra — progresso comparado ao cronograma/projeto.
4. Controle de qualidade de acabamento — piso, pintura, reboco, esquadrias.
5. Auditoria de instalações elétricas/hidráulicas/impermeabilização.

Decisão: consolidar os módulos 2, 3, 4 e 5 em um único app — mobile (instalável)
+ acesso via web — em vez de produtos separados.

## 2. Contexto do repositório

O repo já tinha protótipos parciais relacionados:

- `vigia-obra-seguranca` + `vigia-obra-frontend`: pipeline em Python que analisa
  **vídeo** de canteiro via Claude vision, focado em EPI/segurança
  (NR-6/18/35). Frontend ainda mockado, sem conexão real.
- `checklist-de-obra`: checklist antes/depois por foto, sem IA, sem persistência.
- `diario-de-obra`: diário de obra com ocorrências por severidade, sem IA, sem
  persistência.

Nenhum cobria o escopo completo (múltiplos módulos, foto única, persistência
real, acesso mobile+web). Daí a decisão de criar um novo projeto:
**Arquitool Production**.

## 3. PRD — resumo

Documento completo em `PRD.md`. Pontos centrais:

**Problema**: gestores de obra registram vistorias de forma manual e dispersa
(WhatsApp, caderno, planilha), sem histórico estruturado nem apoio técnico
imediato para julgar urgência.

**Objetivo**: app único, instalável no celular (PWA) e acessível via navegador,
em que o gestor tira uma foto e recebe diagnóstico assistido por IA em um de
quatro módulos, com histórico por obra e exportação de relatório.

**Os 4 módulos do MVP:**

| Módulo | O que a IA analisa | Saída |
|---|---|---|
| Patologias construtivas | trinca, umidade, mofo, eflorescência | tipo provável, causa, urgência |
| Checklist de progresso | etapa da obra vs. esperado | conformidade, itens fora do padrão |
| Qualidade de acabamento | piso, pintura, reboco, esquadrias | defeitos, retrabalho, severidade |
| Instalações técnicas | elétrica, hidráulica, impermeabilização | não conformidades, referência NBR |

Toda análise retorna: severidade (baixa/média/crítica), diagnóstico,
recomendação e disclaimer obrigatório (ferramenta assistiva, não substitui
laudo técnico).

**Fora do MVP**: análise de vídeo, leitura automática de planta, multiusuário,
assinatura digital.

**Fluxo de uso**: selecionar obra → tirar foto → escolher módulo → laudo em
segundos → fica salvo no histórico → exportação de relatório em PDF quando
necessário.

## 4. Arquitetura — resumo

Documento completo em `ARCHITECTURE.md`. Pontos centrais:

**Stack**: Cloudflare Workers + D1 (banco SQL serverless) + R2 (fotos), como
Worker próprio e independente do `wrangler.toml` estático da raiz do repo.
Decisão tomada explicitamente porque o resto do repo já publica via Cloudflare
— evita manter um servidor Python separado, mesmo custando escrever o backend
em TypeScript em vez de Python.

**Modelo de dados**: `obra` → `vistoria` → `laudo` (schema SQL completo no
documento de arquitetura).

**API principal**: `POST /api/obras/:id/vistorias` recebe foto + módulo +
contexto, grava no R2, chama o analyzer do módulo (prompt especializado no
Claude), grava o laudo no D1 e retorna a resposta já pronta (síncrono, sem
fila no MVP).

**Analyzers**: um por módulo, mesmo contrato de entrada/saída, reaproveitando
o padrão de prompt já usado em `vigia_obra/vision_analyzer.py` (adaptado de
vídeo/múltiplos frames para foto única).

**PWA**: sem framework pesado, captura de foto via `<input capture>`, service
worker cacheando só o shell do app (nunca a resposta da API).

**Auth do MVP**: senha única, sem multiusuário.

**Pendência marcada**: rodar `wrangler deploy` de verdade exige confirmação
explícita do usuário antes de acontecer.

## 5. Prompt de mockup (para ferramenta de design)

> App PWA (mobile-first, mas também usável em navegador desktop) para gestores
> de obra fazerem vistorias por foto com apoio de IA. Usuário principal:
> mestre de obras/engenheiro em campo, no celular, precisa de fluxo rápido e
> sem fricção.
>
> **Estilo visual**: funcional, robusto, "ferramenta de campo" — não é app de
> consumo. Alto contraste (uso ao ar livre, sob sol), botões grandes (uso com
> luvas/mãos sujas), cores de severidade claras (verde/amarelo/vermelho).
> Tipografia legível, sem excesso de decoração.
>
> **Telas necessárias:**
>
> 1. **Login** — campo único de senha (sem cadastro de usuário no MVP).
> 2. **Lista de obras** — cards com nome, endereço, contagem de vistorias,
>    botão "+ Nova obra" em destaque.
> 3. **Nova obra** — formulário simples: nome, endereço.
> 4. **Detalhe da obra** — histórico de vistorias em lista/timeline (foto
>    miniatura + módulo + severidade + data), botão flutuante "+ Nova
>    vistoria" e botão "Exportar relatório".
> 5. **Nova vistoria — passo 1: escolher módulo** — 4 cards grandes e
>    tocáveis: "Patologias construtivas", "Checklist de progresso",
>    "Qualidade de acabamento", "Instalações técnicas". Ícone + descrição
>    curta em cada.
> 6. **Nova vistoria — passo 2: capturar foto** — botão grande central "Tirar
>    foto", preview da foto, campo opcional de contexto (ex: "etapa
>    esperada" só no módulo "progresso"), botão "Analisar".
> 7. **Loading da análise** — indicador simples, "Analisando com IA...".
> 8. **Resultado do laudo** — card de destaque com selo de severidade
>    (baixa=verde/média=amarelo/crítica=vermelho), diagnóstico, recomendação,
>    disclaimer em rodapé discreto mas visível, botões "Salvar" e "Nova
>    vistoria".
> 9. **Relatório/exportação** — seleção de período + preview do PDF, botão
>    "Compartilhar/Baixar".
>
> **Componentes reutilizáveis**: badge de severidade (3 cores), card de
> vistoria (foto + módulo + data + severidade), botão de câmera grande,
> disclaimer footer.

## 6. Próximos passos combinados

1. Prototipar o módulo de patologias construtivas primeiro (prompt + rota +
   PWA mínima com 1 tela: foto → laudo).
2. Criar `wrangler.toml` do projeto + `schema.sql` + migração no D1.
3. Rodar localmente (`wrangler dev`) e validar antes de cogitar deploy real.
