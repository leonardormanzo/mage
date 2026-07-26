# Vigia Obra Segurança

Pipeline de apoio ao SESMT: analisa vídeos de canteiro de obra, extrai frames em
intervalos regulares e usa o Claude (visão computacional) para sinalizar
não-conformidades de segurança do trabalho (NR-18, NR-6, NR-35).

**Esta ferramenta é assistiva e não substitui inspeção presencial.** Toda
ocorrência gerada deve ser revisada por um técnico de segurança do trabalho.

## Instalação

```sh
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
copy .env.example .env       # depois edite com sua ANTHROPIC_API_KEY
```

Não é necessário instalar `ffmpeg` — a extração de frames usa OpenCV
diretamente.

## Uso

```sh
python -m vigia_obra.main caminho\para\video.mp4 --interval 5 --output ocorrencias.json
```

Parâmetros:

- `--interval`: intervalo em segundos entre frames analisados (padrão: 5)
- `--max-frames`: limita quantos frames analisar (útil para testar rapidamente)
- `--model`: modelo Claude (padrão: `claude-opus-5`; para vídeos longos com muitos
  frames, `claude-sonnet-5` reduz custo mantendo boa qualidade)
- `--effort`: nível de esforço de raciocínio (`low`/`medium`/`high`/`xhigh`/`max`,
  padrão: `medium`)
- `--output`: caminho do arquivo JSON de saída

## Protocolo para integração com um frontend local

O `stdout` do processo emite **NDJSON** (uma linha JSON por evento) — pensado
para um frontend local (Electron/Tauri/backend Node) rodar isto via
`child_process`/subprocess e ler a saída linha a linha em tempo real:

```json
{"type": "start", "total_frames_estimate": 12, "interval": 5.0, "model": "claude-opus-5"}
{"type": "progress", "frame_index": 0, "timestamp": "00:00", "ocorrencias": []}
{"type": "progress", "frame_index": 1, "timestamp": "00:05", "ocorrencias": [{"timestamp": "00:05", "risco": "...", "norma": "...", "confianca": "alto", "severidade": "media"}]}
{"type": "error", "frame_index": 3, "timestamp": "00:15", "message": "Erro na API (529): ..."}
{"type": "done", "total_ocorrencias": 4, "output_file": "ocorrencias.json", "disclaimer": "Esta análise é assistiva..."}
```

- `total_frames_estimate` pode ser `null` (vídeo sem metadados confiáveis de
  duração/fps) — trate como progresso indeterminado.
- O evento `done.disclaimer` traz o texto que o frontend **deve exibir** na
  tela — a obrigação de deixar claro que a análise é assistiva não está no
  JSON de ocorrências, está neste evento.
- O arquivo `--output` também é gravado em disco, para persistência sem
  depender de capturar o stdout inteiro.

## Formato de saída

Uma lista JSON, um item por ocorrência:

```json
[
  {
    "timestamp": "00:35",
    "risco": "Trabalhador sem capacete próximo a estrutura de andaime",
    "norma": "NR-6, uso de EPI",
    "confianca": "alto",
    "severidade": "media"
  }
]
```

Frames sem pessoas ou elementos de risco relevantes são ignorados
automaticamente pelo modelo (lista vazia).

## Custos

Cada frame analisado é uma chamada à API com uma imagem — o custo escala
linearmente com o número de frames. Para vídeos longos, aumente `--interval`
(ex: 10–15s) ou use `--model claude-sonnet-5` para reduzir custo.
