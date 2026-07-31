# PRD — Arquitool Production

## 1. Problema

Gestores de obra fazem vistorias constantes (patologias, progresso, acabamento,
instalações técnicas) e hoje registram tudo de forma manual e dispersa — foto no
WhatsApp, anotação em caderno ou planilha, sem histórico estruturado por obra e sem
apoio técnico imediato para decidir se um problema é urgente ou cosmético.

Este repositório já tem três protótipos que cobrem pedaços do problema, mas nenhum
resolve o todo:

- `vigia-obra-seguranca` + `vigia-obra-frontend`: analisa **vídeo** de canteiro via
  Claude vision, focado só em EPI/segurança (NR-6/18/35). CLI + frontend mockado,
  sem persistência real.
- `checklist-de-obra`: checklist antes/depois por foto, mas sem IA e sem
  persistência (estado some ao recarregar).
- `diario-de-obra`: diário de obra com ocorrências por severidade, mas também sem
  IA e sem persistência.

## 2. Objetivo

Um único app — instalável no celular (PWA) e acessível via navegador — em que o
gestor de obra tira uma **foto** e recebe um **diagnóstico assistido por IA** em
um de quatro módulos, com histórico persistente por obra e exportação de relatório.

## 3. Usuário-alvo

Gestor de obra / mestre de obras / engenheiro responsável que faz vistorias em
campo, geralmente sozinho, com o celular na mão, sem tempo para preencher
formulários longos.

## 4. Escopo — os 4 módulos

| Módulo | O que a IA analisa na foto | Saída |
|---|---|---|
| **Patologias construtivas** | trinca, umidade, mofo/bolor, eflorescência, descolamento | tipo provável, causa mais provável, urgência, se precisa de laudo de engenheiro |
| **Checklist de progresso** | etapa da obra na foto vs. etapa esperada (informada pelo gestor) | conformidade, itens fora do padrão observados |
| **Qualidade de acabamento** | piso, pintura, reboco, esquadrias | defeitos visíveis, se gera retrabalho, severidade |
| **Instalações técnicas** | elétrica, hidráulica, impermeabilização | não conformidades aparentes, referência normativa (NBR) quando aplicável |

Cada análise gera um **laudo estruturado**: severidade (baixa/média/crítica),
diagnóstico em texto, recomendação de próximo passo, e o **disclaimer obrigatório**
de que é uma ferramenta assistiva (mesmo padrão de `vigia-obra-seguranca`).

### Fora do MVP (v2+)

- Análise de vídeo (só foto única no MVP — o vídeo já existe separado em
  `vigia-obra-seguranca` e pode ser integrado depois).
- Comparação automática com projeto/planta (módulo 3 no MVP depende do gestor
  informar a etapa esperada manualmente, não de leitura de planta).
- Multiusuário/equipe (MVP é uso individual por obra, sem convite de outros
  usuários).
- Assinatura digital de relatório (fica só exportação em PDF/imagem no MVP).

## 5. Fluxo de uso

1. Gestor abre o app (PWA instalado ou navegador) → seleciona a obra (ou cria uma
   nova, campo simples: nome + endereço).
2. Tira foto direto pela câmera do celular (`<input capture="environment">` / PWA).
3. Escolhe o módulo (ou o app sugere pelo contexto, mas seleção manual sempre
   disponível — não confiar 100% em auto-detecção no MVP).
4. IA retorna o laudo em poucos segundos: severidade, diagnóstico, recomendação.
5. Laudo fica salvo no histórico da obra, com foto, data, geolocalização opcional.
6. A qualquer momento, gestor exporta um relatório (PDF) da obra ou de um período,
   para enviar ao cliente/engenheiro responsável.

## 6. Arquitetura proposta

Nenhum dos 3 padrões documentados em `.claude/skills/odin/knowledge.md` cobre esse
caso (precisa de backend real + persistência multi-dispositivo + acesso
mobile/web simultâneo). Proponho um **4º padrão**: PWA + API própria.

- **Frontend**: PWA (manifest + service worker), HTML/CSS/JS sem framework pesado
  (consistente com o resto do repo), instalável no celular, com acesso à câmera via
  `getUserMedia`/`<input capture>`. Funciona também direto no navegador desktop.
- **Backend**: API HTTP simples (Python, FastAPI — mesma linguagem dos outros
  projetos de IA do repo) que:
  - recebe foto + módulo + contexto (obra, etapa esperada) → chama Claude vision
    com prompt especializado por módulo (reaproveitando o padrão de
    `vigia_obra/vision_analyzer.py`);
  - persiste obra / vistoria / laudo / foto.
- **Storage**: fotos em disco (ou bucket, se hospedado) + banco relacional
  (SQLite para começar — mesmo padrão do `agenda-retratil` — com caminho de
  migração para Postgres se crescer).
- **Modelo de IA**: Claude, modelo e nível de esforço configuráveis (não
  hardcoded), seguindo o padrão já usado em `vigia-obra-seguranca`.
- **Autenticação**: MVP com login simples (usuário único ou por obra), sem SSO —
  suficiente porque é uso individual do gestor.

## 7. Modelo de dados (rascunho)

```
Obra:        id, nome, endereço, criada_em
Vistoria:    id, obra_id, modulo, foto_path, criado_em, geolocalizacao (opcional)
Laudo:       id, vistoria_id, severidade, diagnostico, recomendacao, disclaimer,
             modelo_ia, criado_em
```

## 8. Reaproveitamento do que já existe

- Prompt engineering e padrão de saída estruturada de
  `vigia_obra/vision_analyzer.py` → adaptar de vídeo (múltiplos frames) para foto
  única, um prompt por módulo.
- UX de cards de ocorrência por severidade de `vigia-obra-frontend`.
- Fluxo antes/depois de `checklist-de-obra` → pode virar o modo de registro do
  módulo de acabamento (foto do defeito + foto do reparo).
- Estrutura de diário/ocorrências de `diario-de-obra` → inspira a tela de
  histórico por obra.

## 9. Riscos e limites conhecidos

- IA não substitui laudo técnico — todo output leva o disclaimer, igual aos
  demais projetos do repo.
- Falsos positivos/negativos em foto única (sem contexto de vídeo/múltiplos
  ângulos) — mitigar deixando claro que é triagem, não veredito.
- Custo de API escala com número de fotos analisadas — expor modelo mais barato
  como opção, mesmo padrão do `vigia-obra-seguranca`.

## 10. Próximos passos

1. Validar este PRD com o usuário (nome do projeto, prioridade entre os 4 módulos
   para o MVP — todos de uma vez ou começar por 1?).
2. Desenhar telas (via `ui-ux-pro-max`) antes de codar.
3. Prototipar módulo de patologias construtivas primeiro (maior valor percebido
   + já validado como prioridade no brainstorm).
4. Expandir para os outros 3 módulos reaproveitando a mesma infraestrutura.
