"use strict";

const path = require("path");
const fs = require("fs");
const os = require("os");
const { spawn } = require("child_process");
const readline = require("readline");
const express = require("express");
const multer = require("multer");

// Carrega variáveis de ambiente de múltiplos pontos possíveis
require("dotenv").config({ path: path.join(__dirname, ".env") });
const BACKEND_DIR = path.resolve(__dirname, "..", "..", "vigia-obra-seguranca");
require("dotenv").config({ path: path.join(BACKEND_DIR, ".env") });

const PORT = process.env.PORT || 5731;
const PYTHON_BIN = process.env.PYTHON_BIN || (process.platform === "win32" ? "python" : "python3");
const FRONTEND_DIR = path.resolve(__dirname, "..");
const ALLOWED_MODELS = new Set([
  "gemini-flash-lite-latest",
  "gemini-3.1-flash-lite",
  "gemini-3.5-flash",
  "gemini-flash-latest",
  "gemini-3.6-flash",
  "gemini-3.8-flash",
  "gemini-2.0-flash",
  "claude-sonnet-5",
  "claude-opus-5",
]);
const ALLOWED_EFFORTS = new Set(["low", "medium", "high", "xhigh", "max"]);

function resolveGeminiKey(customKey) {
  if (customKey && !customKey.startsWith("sk-ant-")) {
    return customKey.trim();
  }
  if (process.env.GEMINI_API_KEY && !process.env.GEMINI_API_KEY.includes("sua-chave")) {
    return process.env.GEMINI_API_KEY.trim();
  }
  try {
    const envContent = fs.readFileSync(path.join(BACKEND_DIR, ".env"), "utf-8");
    const m = envContent.match(/^GEMINI_API_KEY=(.+)$/m);
    if (m && m[1].trim() && !m[1].includes("sua-chave")) {
      process.env.GEMINI_API_KEY = m[1].trim();
      return m[1].trim();
    }
  } catch (e) {}
  return "";
}

function resolveAnthropicKey(customKey) {
  if (customKey && customKey.startsWith("sk-ant-")) {
    return customKey.trim();
  }
  if (process.env.ANTHROPIC_API_KEY && !process.env.ANTHROPIC_API_KEY.includes("sua-chave")) {
    return process.env.ANTHROPIC_API_KEY.trim();
  }
  try {
    const envContent = fs.readFileSync(path.join(BACKEND_DIR, ".env"), "utf-8");
    const m = envContent.match(/^ANTHROPIC_API_KEY=(.+)$/m);
    if (m && m[1].trim() && !m[1].includes("sua-chave")) {
      process.env.ANTHROPIC_API_KEY = m[1].trim();
      return m[1].trim();
    }
  } catch (e) {}
  return "";
}

// Configuração do Multer preservando extensões de vídeo (webm, mp4, etc.)
const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    cb(null, os.tmpdir());
  },
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname) || ".webm";
    const uniqueName = `vigia-video-${Date.now()}-${Math.random().toString(36).slice(2, 8)}${ext}`;
    cb(null, uniqueName);
  },
});
const upload = multer({ storage });

const app = express();
app.use(express.json());
app.use(express.static(FRONTEND_DIR));

app.get("/api/health", (_req, res) => {
  const geminiKey = resolveGeminiKey("");
  const anthropicKey = resolveAnthropicKey("");

  res.json({
    ok: true,
    backendDir: BACKEND_DIR,
    backendFound: fs.existsSync(path.join(BACKEND_DIR, "vigia_obra", "main.py")),
    geminiConfigured: Boolean(geminiKey),
    anthropicConfigured: Boolean(anthropicKey),
    demoSupported: true,
    pythonBin: PYTHON_BIN,
  });
});

app.post("/api/save-key", (req, res) => {
  const key = (req.body.apiKey || "").trim();
  const provider = (req.body.provider || "").trim().toLowerCase();

  if (!key) {
    return res.status(400).json({ error: "Chave não informada." });
  }

  const isGemini = provider === "gemini" || !key.startsWith("sk-ant-");
  const envVarName = isGemini ? "GEMINI_API_KEY" : "ANTHROPIC_API_KEY";
  process.env[envVarName] = key;

  try {
    const envPath = path.join(BACKEND_DIR, ".env");
    let currentContent = "";
    if (fs.existsSync(envPath)) {
      currentContent = fs.readFileSync(envPath, "utf-8");
    }

    const regex = new RegExp(`^${envVarName}=.*$`, "m");
    let newContent = "";
    if (regex.test(currentContent)) {
      newContent = currentContent.replace(regex, `${envVarName}=${key}`);
    } else {
      newContent = currentContent.trim() ? `${currentContent.trim()}\n${envVarName}=${key}\n` : `${envVarName}=${key}\n`;
    }

    fs.writeFileSync(envPath, newContent, { encoding: "utf-8" });
    res.json({ ok: true, message: `Chave ${envVarName} salva com sucesso!` });
  } catch (err) {
    res.json({ ok: true, message: `Chave ${envVarName} salva em memória na sessão atual.` });
  }
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

  const customKey = (req.body.apiKey || req.headers["x-api-key"] || "").trim();
  const geminiKey = resolveGeminiKey(customKey);
  const anthropicKey = resolveAnthropicKey(customKey);

  const model = ALLOWED_MODELS.has(req.body.model) ? req.body.model : "gemini-flash-lite-latest";
  const isGeminiModel = !model.startsWith("claude");
  const hasKey = isGeminiModel ? Boolean(geminiKey) : Boolean(anthropicKey);
  const isDemo = req.body.demo === "true" || req.body.demo === true || !hasKey;

  const interval = Number(req.body.interval) || 2;
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

  if (isDemo) {
    args.push("--demo");
  } else {
    args.push("--provider", isGeminiModel ? "gemini" : "anthropic");
  }

  if (maxFrames) {
    args.push("--max-frames", String(maxFrames));
  }

  res.setHeader("Content-Type", "application/x-ndjson; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("X-Accel-Buffering", "no");
  if (res.flushHeaders) res.flushHeaders();

  const spawnEnv = {
    ...process.env,
    PYTHONIOENCODING: "utf-8",
    PYTHONUTF8: "1",
  };
  if (geminiKey) spawnEnv.GEMINI_API_KEY = geminiKey;
  if (anthropicKey) spawnEnv.ANTHROPIC_API_KEY = anthropicKey;

  let child;
  try {
    child = spawn(PYTHON_BIN, args, { cwd: BACKEND_DIR, env: spawnEnv });
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
    } catch (_err) {}
  });

  child.stderr.on("data", (chunk) => {
    stderrTail = (stderrTail + chunk.toString()).slice(-2000);
  });

  child.on("error", (err) => {
    sendEvent(res, {
      type: "error",
      message: `Não foi possível executar '${PYTHON_BIN}'. Detalhe: ${err.message}`,
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

app.post("/api/analyze-frame", upload.single("frame"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "Nenhum frame enviado (campo 'frame')." });
  }

  const framePath = req.file.path;
  const cleanup = () => {
    fs.unlink(framePath, () => {});
  };

  const customKey = (req.body.apiKey || req.headers["x-api-key"] || "").trim();
  const geminiKey = resolveGeminiKey(customKey);
  const anthropicKey = resolveAnthropicKey(customKey);

  const model = ALLOWED_MODELS.has(req.body.model) ? req.body.model : "gemini-flash-lite-latest";
  const isGeminiModel = !model.startsWith("claude");
  const hasKey = isGeminiModel ? Boolean(geminiKey) : Boolean(anthropicKey);
  const isDemo = req.body.demo === "true" || req.body.demo === true || !hasKey;

  const timestamp = req.body.timestamp || new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const frameIndex = Number(req.body.frameIndex) || 0;
  const effort = ALLOWED_EFFORTS.has(req.body.effort) ? req.body.effort : "medium";

  const args = [
    "-m",
    "vigia_obra.analyze_single_frame",
    framePath,
    "--timestamp",
    timestamp,
    "--frame-index",
    String(frameIndex),
    "--model",
    model,
    "--effort",
    effort,
  ];

  if (isDemo) {
    args.push("--demo");
  } else {
    args.push("--provider", isGeminiModel ? "gemini" : "anthropic");
  }

  const spawnEnv = {
    ...process.env,
    PYTHONIOENCODING: "utf-8",
    PYTHONUTF8: "1",
  };
  if (geminiKey) spawnEnv.GEMINI_API_KEY = geminiKey;
  if (anthropicKey) spawnEnv.ANTHROPIC_API_KEY = anthropicKey;

  let stdoutData = "";
  let stderrData = "";
  const child = spawn(PYTHON_BIN, args, { cwd: BACKEND_DIR, env: spawnEnv });

  child.stdout.on("data", (chunk) => {
    stdoutData += chunk.toString("utf-8");
  });
  child.stderr.on("data", (chunk) => {
    stderrData += chunk.toString("utf-8");
  });

  child.on("error", (err) => {
    cleanup();
    res.status(500).json({ error: `Erro ao executar Python: ${err.message}` });
  });

  child.on("close", (code) => {
    cleanup();
    if (code !== 0) {
      return res.status(500).json({
        error: `Erro ao analisar frame (código ${code}): ${stderrData || "Erro desconhecido"}`,
      });
    }
    try {
      const jsonMatch = stdoutData.match(/\{[\s\S]*\}/);
      if (!jsonMatch) throw new Error("JSON não encontrado no output");
      const data = JSON.parse(jsonMatch[0]);
      res.json(data);
    } catch (parseErr) {
      console.error("[analyze-frame] parse error:", parseErr.message, "stdout:", stdoutData);
      res.status(500).json({ error: `Resposta inválida do analisador: ${stdoutData}` });
    }
  });
});

app.listen(PORT, () => {
  console.log(`Vigia Obra rodando em http://localhost:${PORT}`);
  console.log(`Backend Python em: ${BACKEND_DIR}`);
});
