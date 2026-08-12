"use strict";

const path = require("path");
const fs = require("fs");
const os = require("os");
const { spawn } = require("child_process");
const readline = require("readline");
const express = require("express");
const multer = require("multer");

const PORT = process.env.PORT || 5731;
const PYTHON_BIN = process.env.PYTHON_BIN || (process.platform === "win32" ? "python" : "python3");
const BACKEND_DIR = path.resolve(__dirname, "..", "..", "vigia-obra-seguranca");
const FRONTEND_DIR = path.resolve(__dirname, "..");
const ALLOWED_MODELS = new Set(["claude-opus-5", "claude-sonnet-5"]);
const ALLOWED_EFFORTS = new Set(["low", "medium", "high", "xhigh", "max"]);

const upload = multer({ dest: os.tmpdir() });
const app = express();

app.use(express.static(FRONTEND_DIR));

app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    backendDir: BACKEND_DIR,
    backendFound: fs.existsSync(path.join(BACKEND_DIR, "vigia_obra", "main.py")),
    apiKeyConfigured: Boolean(process.env.ANTHROPIC_API_KEY),
  });
});

function sendEvent(res, event) {
  res.write(JSON.stringify(event) + "\n");
}

app.post("/api/analyze", upload.single("video"), (req, res) => {
  const cleanupPaths = [];
  const cleanup = () => {
    for (const p of cleanupPaths) {
      fs.unlink(p, () => {});
    }
  };

  if (!req.file) {
    res.status(400).json({ error: "Nenhum vídeo enviado (campo 'video')." });
    return;
  }
  cleanupPaths.push(req.file.path);

  if (!process.env.ANTHROPIC_API_KEY) {
    cleanup();
    res.status(500).json({
      error: "ANTHROPIC_API_KEY não configurada no ambiente do servidor. Defina a variável antes de iniciar o servidor (veja .env.example em vigia-obra-seguranca).",
    });
    return;
  }

  const interval = Number(req.body.interval) || 5;
  const model = ALLOWED_MODELS.has(req.body.model) ? req.body.model : "claude-opus-5";
  const effort = ALLOWED_EFFORTS.has(req.body.effort) ? req.body.effort : "medium";
  const maxFrames = req.body.maxFrames ? Number(req.body.maxFrames) : null;

  const outputPath = path.join(os.tmpdir(), `vigia-obra-ocorrencias-${Date.now()}.json`);
  cleanupPaths.push(outputPath);

  const args = [
    "-m",
    "vigia_obra.main",
    req.file.path,
    "--interval",
    String(interval),
    "--model",
    model,
    "--effort",
    effort,
    "--output",
    outputPath,
  ];
  if (maxFrames) {
    args.push("--max-frames", String(maxFrames));
  }

  res.setHeader("Content-Type", "application/x-ndjson");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("X-Accel-Buffering", "no");
  if (res.flushHeaders) res.flushHeaders();

  let child;
  try {
    child = spawn(PYTHON_BIN, args, { cwd: BACKEND_DIR });
  } catch (err) {
    sendEvent(res, { type: "error", message: `Falha ao iniciar o processo Python: ${err.message}` });
    res.end();
    cleanup();
    return;
  }

  let sawDone = false;
  let stderrTail = "";

  const rl = readline.createInterface({ input: child.stdout });
  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    try {
      const event = JSON.parse(trimmed);
      if (event.type === "done") sawDone = true;
      sendEvent(res, event);
    } catch (_err) {
      // linha não-JSON no stdout do pipeline (não deveria acontecer) — ignora silenciosamente
    }
  });

  child.stderr.on("data", (chunk) => {
    stderrTail = (stderrTail + chunk.toString()).slice(-2000);
  });

  child.on("error", (err) => {
    sendEvent(res, {
      type: "error",
      message: `Não foi possível executar '${PYTHON_BIN}'. Confirme que o Python e as dependências de vigia-obra-seguranca estão instalados. Detalhe: ${err.message}`,
    });
    res.end();
    cleanup();
  });

  child.on("close", (code) => {
    if (!sawDone) {
      sendEvent(res, {
        type: "error",
        message: `O pipeline encerrou (código ${code}) antes de concluir.${stderrTail ? " Detalhe: " + stderrTail.trim() : ""}`,
      });
    }
    res.end();
    cleanup();
  });

  req.on("close", () => {
    if (child && !child.killed) child.kill();
  });
});

app.listen(PORT, () => {
  console.log(`Vigia Obra rodando em http://localhost:${PORT}`);
  console.log(`Backend Python esperado em: ${BACKEND_DIR}`);
  if (!fs.existsSync(path.join(BACKEND_DIR, "vigia_obra", "main.py"))) {
    console.warn("Aviso: não encontrei vigia_obra/main.py no caminho esperado. Análises vão falhar.");
  }
  if (!process.env.ANTHROPIC_API_KEY) {
    console.warn("Aviso: ANTHROPIC_API_KEY não está definida neste ambiente.");
  }
});
