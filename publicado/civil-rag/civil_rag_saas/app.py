import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from civil_rag_saas.database import (
    inicializar_banco,
    criar_obra,
    listar_obras,
    obter_estatisticas_obra
)
from civil_rag_saas.extractor import extrair_texto_arquivo
from civil_rag_saas.rag_engine import indexar_documento_na_obra, consultar_obra

app = FastAPI(
    title="ArcTech - RAG Intelligence para Construção Civil",
    description="Sistema de Inteligência Artificial para gestão e análise técnica de documentos de obras.",
    version="2.1.0"
)

# Inicializa o banco de dados
inicializar_banco()

PASTA_UPLOADS = "civil_rag_saas/uploads_temporarios"
os.makedirs(PASTA_UPLOADS, exist_ok=True)

class ObraCreate(BaseModel):
    id: str
    nome: str
    descricao: str = ""

class PerguntaRequest(BaseModel):
    pergunta: str

@app.post("/api/obras")
def api_criar_obra(dados: ObraCreate):
    criar_obra(dados.id, dados.nome, dados.descricao)
    return {"status": "sucesso", "mensagem": f"Obra '{dados.nome}' criada com sucesso!"}

@app.get("/api/obras")
def api_listar_obras():
    return listar_obras()

@app.get("/api/obras/{obra_id}/stats")
def api_estatisticas_obra(obra_id: str):
    return obter_estatisticas_obra(obra_id)

@app.post("/api/obras/{obra_id}/upload")
async def api_upload_documento(obra_id: str, arquivo: UploadFile = File(...)):
    # basename impede que um nome como "../../x" grave fora da pasta de uploads
    nome_seguro = os.path.basename(arquivo.filename or "")
    if not nome_seguro:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
    caminho_salvo = os.path.join(PASTA_UPLOADS, nome_seguro)
    try:
        with open(caminho_salvo, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        # 1. Extrai o texto do PDF, DOCX ou TXT
        paginas_extraidas = extrair_texto_arquivo(caminho_salvo)
        if not paginas_extraidas:
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto do documento técnico.")

        # 2. Faz o chunking, gera embeddings no Gemini e salva no PostgreSQL
        total_chunks = indexar_documento_na_obra(obra_id, paginas_extraidas)

        return {
            "status": "sucesso",
            "arquivo": arquivo.filename,
            "paginas_processadas": len(paginas_extraidas),
            "chunks_vetorizados": total_chunks,
            "obra_id": obra_id
        }
    finally:
        if os.path.exists(caminho_salvo):
            os.remove(caminho_salvo)

@app.post("/api/obras/{obra_id}/perguntar")
def api_perguntar_obra(obra_id: str, dados: PerguntaRequest):
    try:
        resultado = consultar_obra(obra_id, dados.pergunta)
        return resultado
    except Exception as e:
        return {
            "resposta": f"Não foi possível processar a consulta neste momento: {str(e)}",
            "fontes": []
        }

# --- INTERFACE OFICIAL BASEADA NO ARCTECH DESIGN SYSTEM (OBSIDIAN DARK) ---
@app.get("/", response_class=HTMLResponse)
def interface_web():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Arc[tech_] // RAG Canteiro de Obras</title>
        
        <!-- ArcTech Design System Typography -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,700&family=Inter:wght@400;600;700;800&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
        
        <!-- Markdown Parser -->
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

        <style>
            :root {
                /* ArcTech Design Tokens - Theme: Dark (Obsidian) */
                --bg: #090B10;
                --bg-elevated: #11141E;
                --surface: rgba(18, 22, 33, 0.72);
                --surface-solid: #141824;
                --surface-hover: rgba(28, 34, 50, 0.85);
                
                --text: #F3F4F8;
                --text-secondary: #9FA4B6;
                --text-muted: #646A7E;
                
                --border: rgba(255, 255, 255, 0.10);
                --border-strong: rgba(255, 255, 255, 0.18);
                --border-specular: rgba(255, 255, 255, 0.28);
                
                --accent: #FF2E3B;
                --accent-hover: #E01E2B;
                --accent-soft: rgba(255, 46, 59, 0.14);
                --accent-glow: rgba(255, 46, 59, 0.25);
                --on-accent: #FFFFFF;
                
                --green: #059669;
                --green-soft: rgba(5, 150, 105, 0.12);
                --blue: #0284C7;
                --gold: #D97706;

                /* Shadows & Radii */
                --radius-sm: 8px;
                --radius-md: 14px;
                --radius-lg: 20px;
                --radius-pill: 9999px;
                --glass-shadow: 0 24px 60px -12px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.08) inset;
            }

            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
            }

            body {
                background: var(--bg);
                color: var(--text);
                font-family: 'DM Sans', sans-serif;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                background-image: 
                    radial-gradient(circle at 18% 12%, var(--accent-glow) 0%, transparent 40%),
                    radial-gradient(circle at 82% 88%, rgba(2, 132, 199, 0.12) 0%, transparent 45%);
                background-attachment: fixed;
            }

            /* Custom Scrollbar */
            ::-webkit-scrollbar { width: 5px; height: 5px; }
            ::-webkit-scrollbar-track { background: var(--bg); }
            ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: var(--radius-pill); }
            ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.25); }

            /* ArcTech Floating Pill Header */
            header {
                max-width: 1240px;
                width: calc(100% - 48px);
                margin: 18px auto 0;
                padding: 10px 24px;
                height: 64px;
                background: var(--surface);
                backdrop-filter: blur(24px) saturate(180%);
                border: 1px solid var(--border);
                border-top: 1px solid var(--border-specular);
                border-radius: var(--radius-pill);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
                display: flex;
                align-items: center;
                justify-content: space-between;
                position: sticky;
                top: 16px;
                z-index: 50;
            }

            /* ArcTech Official Logo Component */
            .logo-wrapper {
                display: flex;
                align-items: baseline;
                gap: 2px;
                text-decoration: none;
                user-select: none;
            }

            .logo-arc {
                font-family: 'Caveat', cursive;
                font-weight: 700;
                font-size: 28px;
                color: var(--text);
                transform: rotate(-1.5deg);
                display: inline-block;
                border-bottom: 2px solid var(--accent);
                line-height: 0.95;
                padding-bottom: 2px;
            }

            .logo-tech {
                font-family: 'Space Mono', monospace;
                font-weight: 700;
                font-size: 15px;
                color: var(--accent);
                margin-left: 3px;
                letter-spacing: -0.02em;
            }

            .logo-cursor {
                animation: blink 1.1s infinite;
                color: var(--accent);
                font-family: 'Space Mono', monospace;
                font-weight: 700;
            }

            @keyframes blink {
                0%, 49% { opacity: 1; }
                50%, 100% { opacity: 0; }
            }

            .nav-actions {
                display: flex;
                align-items: center;
                gap: 14px;
            }

            /* Hero Eyebrow Badge */
            .hero-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 5px 12px;
                background: var(--accent-soft);
                border: 1px solid rgba(255, 46, 59, 0.3);
                border-radius: var(--radius-pill);
                font-family: 'Space Mono', monospace;
                font-size: 11.5px;
                font-weight: 700;
                color: var(--accent);
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }

            .pulsing-dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: var(--accent);
                box-shadow: 0 0 10px var(--accent);
                animation: pulse 1.8s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.3; transform: scale(0.85); }
            }

            .portfolio-link {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 7px 15px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid var(--border);
                border-radius: var(--radius-pill);
                color: var(--text);
                font-size: 13.5px;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.2s ease;
            }

            .portfolio-link:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: var(--border-strong);
                color: var(--accent);
            }

            /* Main Container */
            main {
                max-width: 1240px;
                width: calc(100% - 48px);
                margin: 24px auto 32px;
                display: grid;
                grid-template-columns: 370px 1fr;
                gap: 24px;
                flex: 1;
            }

            /* Glass Panels */
            .glass-panel {
                background: var(--surface);
                backdrop-filter: blur(24px) saturate(180%);
                border: 1px solid var(--border);
                border-top: 1px solid var(--border-specular);
                border-radius: var(--radius-lg);
                box-shadow: var(--glass-shadow);
                padding: 24px;
                position: relative;
            }

            .inner-panel {
                background: var(--surface-solid);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 16px;
                margin-top: 14px;
            }

            /* Eyebrow Labels */
            .eyebrow {
                font-family: 'Space Mono', monospace;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--accent);
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
            }

            .eyebrow span {
                color: var(--text-muted);
            }

            /* Buttons ArcTech */
            .btn-accent {
                width: 100%;
                background: var(--accent);
                color: var(--on-accent);
                border: 1px solid var(--accent);
                border-radius: var(--radius-pill);
                padding: 12px 20px;
                font-family: 'Inter', sans-serif;
                font-size: 14.5px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 4px 18px var(--accent-glow);
            }

            .btn-accent:hover:not(:disabled) {
                background: var(--accent-hover);
                transform: translateY(-1px);
                box-shadow: 0 6px 24px rgba(255, 46, 59, 0.4);
            }

            .btn-accent:disabled {
                opacity: 0.4;
                cursor: not-allowed;
                transform: none;
            }

            .btn-glass {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border);
                border-radius: var(--radius-pill);
                color: var(--text);
                padding: 6px 14px;
                font-size: 12.5px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .btn-glass:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: var(--border-strong);
            }

            /* Inputs & Select */
            input, select {
                width: 100%;
                background: rgba(9, 11, 16, 0.85);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                color: var(--text);
                padding: 11px 13px;
                font-size: 14px;
                outline: none;
                transition: all 0.2s ease;
                margin-bottom: 12px;
            }

            input:focus, select:focus {
                border-color: var(--accent);
                box-shadow: 0 0 12px var(--accent-soft);
            }

            /* Authority Pill (ArcTech Component) */
            .authority-pill {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid var(--border);
                border-radius: var(--radius-pill);
                margin-bottom: 18px;
            }

            .authority-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: var(--accent);
                color: var(--on-accent);
                font-family: 'Space Mono', monospace;
                font-size: 12px;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }

            .authority-title {
                font-size: 12px;
                font-weight: 700;
                color: var(--text);
                line-height: 1.2;
            }

            .authority-sub {
                font-size: 11px;
                color: var(--text-muted);
                line-height: 1.2;
                margin-top: 2px;
            }

            /* Stats Metrics */
            .stats-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-top: 10px;
            }

            .stat-box {
                background: rgba(9, 11, 16, 0.6);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                padding: 12px;
                text-align: center;
            }

            .stat-value {
                font-family: 'Space Mono', monospace;
                font-size: 20px;
                font-weight: 700;
                color: var(--text);
            }

            .stat-label {
                font-family: 'Space Mono', monospace;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-muted);
                margin-top: 2px;
            }

            /* Technical Drop Zone */
            .drop-zone {
                border: 1.5px dashed var(--border-strong);
                border-radius: var(--radius-md);
                padding: 24px 16px;
                text-align: center;
                background: rgba(255, 255, 255, 0.015);
                cursor: pointer;
                transition: all 0.2s ease;
                margin-bottom: 12px;
            }

            .drop-zone:hover, .drop-zone.dragover {
                border-color: var(--accent);
                background: var(--accent-soft);
            }

            .drop-symbol {
                font-family: 'Space Mono', monospace;
                font-size: 22px;
                color: var(--accent);
                margin-bottom: 6px;
            }

            .drop-text {
                font-size: 13.5px;
                font-weight: 600;
                color: var(--text);
            }

            .drop-sub {
                font-family: 'Space Mono', monospace;
                font-size: 11px;
                color: var(--text-muted);
                margin-top: 4px;
            }

            /* File List */
            .file-list {
                display: flex;
                flex-direction: column;
                gap: 6px;
                margin-top: 10px;
                max-height: 140px;
                overflow-y: auto;
            }

            .file-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 7px 10px;
                background: rgba(9, 11, 16, 0.7);
                border: 1px solid var(--border);
                border-radius: 6px;
                font-size: 12px;
            }

            .file-name {
                color: var(--text-secondary);
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                max-width: 200px;
            }

            .file-chunks-badge {
                font-family: 'Space Mono', monospace;
                font-size: 10px;
                color: var(--accent);
                background: var(--accent-soft);
                padding: 2px 6px;
                border-radius: 4px;
            }

            /* Prompt Chips */
            .quick-prompts {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .prompt-btn {
                background: rgba(9, 11, 16, 0.7);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                padding: 9px 12px;
                color: var(--text-secondary);
                font-size: 12.5px;
                text-align: left;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .prompt-btn:hover {
                background: var(--surface-hover);
                border-color: var(--accent);
                color: var(--text);
                padding-left: 15px;
            }

            .prompt-arrow {
                font-family: 'Space Mono', monospace;
                color: var(--accent);
                font-size: 12px;
            }

            /* Workspace Area (Chat & Intelligence) */
            .workspace-area {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 124px);
                padding: 0;
                overflow: hidden;
            }

            .workspace-top {
                padding: 18px 24px;
                border-bottom: 1px solid var(--border);
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: rgba(14, 18, 27, 0.85);
            }

            .obra-header-title {
                font-family: 'Inter', sans-serif;
                font-size: 17px;
                font-weight: 700;
                letter-spacing: -0.02em;
            }

            .obra-header-desc {
                font-size: 12.5px;
                color: var(--text-secondary);
                margin-top: 2px;
            }

            .chat-thread {
                flex: 1;
                overflow-y: auto;
                padding: 26px;
                display: flex;
                flex-direction: column;
                gap: 20px;
                background: rgba(9, 11, 16, 0.65);
            }

            /* Welcome Screen */
            .empty-state {
                margin: auto;
                max-width: 520px;
                text-align: center;
                padding: 30px;
            }

            .empty-badge {
                margin-bottom: 14px;
            }

            .empty-title {
                font-family: 'Inter', sans-serif;
                font-size: 22px;
                font-weight: 700;
                letter-spacing: -0.02em;
                margin-bottom: 8px;
            }

            .empty-desc {
                font-size: 14px;
                color: var(--text-secondary);
                line-height: 1.6;
            }

            /* Message Bubbles */
            .chat-message {
                display: flex;
                gap: 12px;
                max-width: 88%;
                animation: fadeIn 0.25s ease;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(6px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .chat-message.user {
                align-self: flex-end;
                flex-direction: row-reverse;
            }

            .chat-message.ai {
                align-self: flex-start;
            }

            .chat-avatar {
                width: 32px;
                height: 32px;
                border-radius: var(--radius-sm);
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Space Mono', monospace;
                font-size: 11px;
                font-weight: 700;
                flex-shrink: 0;
            }

            .chat-message.user .chat-avatar {
                background: var(--surface-solid);
                border: 1px solid var(--border-strong);
                color: var(--text);
            }

            .chat-message.ai .chat-avatar {
                background: var(--accent);
                color: var(--on-accent);
                box-shadow: 0 0 12px var(--accent-glow);
            }

            .chat-bubble {
                padding: 16px 20px;
                border-radius: var(--radius-md);
                font-size: 14px;
                line-height: 1.65;
            }

            .chat-message.user .chat-bubble {
                background: var(--surface-solid);
                border: 1px solid var(--border-strong);
                color: var(--text);
                border-top-right-radius: 4px;
            }

            .chat-message.ai .chat-bubble {
                background: rgba(18, 22, 33, 0.9);
                border: 1px solid var(--border);
                border-top: 1px solid var(--border-specular);
                color: var(--text);
                border-top-left-radius: 4px;
                box-shadow: var(--glass-shadow);
            }

            .chat-bubble p { margin-bottom: 10px; }
            .chat-bubble p:last-child { margin-bottom: 0; }
            .chat-bubble ul, .chat-bubble ol { margin-left: 20px; margin-bottom: 10px; }
            .chat-bubble strong { color: var(--text); font-weight: 700; }
            .chat-bubble code {
                font-family: 'Space Mono', monospace;
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid var(--border);
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 0.85em;
                color: var(--accent);
            }

            /* Technical Citations Card */
            .audit-card {
                margin-top: 14px;
                padding: 12px 14px;
                background: rgba(9, 11, 16, 0.8);
                border: 1px solid var(--border);
                border-left: 3px solid var(--accent);
                border-radius: var(--radius-sm);
            }

            .audit-title {
                font-family: 'Space Mono', monospace;
                font-size: 10.5px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--accent);
                margin-bottom: 8px;
            }

            .audit-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }

            .audit-badge {
                font-family: 'Space Mono', monospace;
                font-size: 11px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid var(--border);
                padding: 3px 8px;
                border-radius: 4px;
                color: var(--text-secondary);
            }

            .audit-badge b {
                color: var(--text);
            }

            /* Bottom Input Dock */
            .input-dock {
                padding: 18px 24px;
                border-top: 1px solid var(--border);
                background: rgba(14, 18, 27, 0.9);
                display: flex;
                gap: 12px;
                align-items: center;
            }

            .input-dock input {
                margin-bottom: 0;
                height: 48px;
                border-radius: var(--radius-pill);
                background: var(--bg);
                padding: 0 20px;
                font-size: 14px;
            }

            .btn-send-pill {
                width: 140px;
                height: 48px;
                margin-bottom: 0;
                border-radius: var(--radius-pill);
                flex-shrink: 0;
            }

            /* Modal Nova Obra */
            .modal-backdrop {
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(10px);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 100;
            }

            .modal-box {
                background: var(--surface-solid);
                border: 1px solid var(--border-strong);
                border-top: 1px solid var(--border-specular);
                border-radius: var(--radius-lg);
                padding: 28px;
                max-width: 440px;
                width: 90%;
                box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8);
            }

            .modal-header {
                font-family: 'Inter', sans-serif;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 16px;
            }

            @media (max-width: 1024px) {
                main { grid-template-columns: 1fr; }
                .workspace-area { height: 600px; }
            }
        </style>
    </head>
    <body>
        <!-- ArcTech Floating Header -->
        <header>
            <div class="logo-wrapper">
                <span class="logo-arc">Arc</span><span class="logo-tech">[tech<span class="logo-cursor">_</span>]</span>
            </div>

            <div class="nav-actions">
                <div class="hero-badge">
                    <div class="pulsing-dot"></div>
                    <span>Canteiro // RAG Engine</span>
                </div>

                <a href="https://mage.leonardo-r-manzo.workers.dev/publicado/portfolio/" target="_blank" class="portfolio-link">
                    <span>Portfolio</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                </a>
            </div>
        </header>

        <!-- Main Workspace -->
        <main>
            <!-- Left Deck -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                
                <!-- 1. Obra Ativa Panel -->
                <div class="glass-panel">
                    <div class="eyebrow">
                        <span>01 // PROJETO ATIVO</span>
                        <button onclick="abrirModalNovaObra()" class="btn-glass">+ Nova Obra</button>
                    </div>

                    <!-- Authority Pill -->
                    <div class="authority-pill">
                        <div class="authority-avatar">LM</div>
                        <div>
                            <div class="authority-title">Desenhada por quem vive o canteiro</div>
                            <div class="authority-sub">Engenharia e IA • 12 anos de obra</div>
                        </div>
                    </div>

                    <select id="select-obras" onchange="trocarObra()">
                        <option value="">Carregando obras...</option>
                    </select>

                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-value" id="stat-docs">0</div>
                            <div class="stat-label">Documentos</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="stat-chunks">0</div>
                            <div class="stat-label">Chunks Vetorizados</div>
                        </div>
                    </div>
                </div>

                <!-- 2. Technical Ingestion Panel -->
                <div class="glass-panel">
                    <div class="eyebrow">
                        <span>02 // INGESTÃO TÉCNICA</span>
                        <span>PDF • DOCX • TXT</span>
                    </div>

                    <div class="drop-zone" id="drop-zone" onclick="document.getElementById('file-input').click()">
                        <div class="drop-symbol">[+]</div>
                        <div class="drop-text">Anexar Memorial ou Laudo</div>
                        <div class="drop-sub">Clique ou arraste o arquivo aqui</div>
                        <input type="file" id="file-input" style="display: none;" accept=".pdf,.docx,.txt" onchange="arquivoSelecionado(this)">
                    </div>

                    <div id="file-selected-name" style="font-family: 'Space Mono', monospace; font-size: 11px; color: var(--accent); margin-bottom: 10px; display: none;"></div>

                    <button class="btn-accent" id="btn-upload" onclick="executarUpload()" disabled>
                        <span>Fatiar e Vetorizar no Canteiro</span>
                    </button>

                    <div class="inner-panel">
                        <div class="eyebrow" style="margin-bottom: 8px;">
                            <span>BASE TÉCNICA DA OBRA</span>
                        </div>
                        <div class="file-list" id="doc-list">
                            <div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 6px;">Nenhum documento anexado.</div>
                        </div>
                    </div>
                </div>

                <!-- 3. Quick Engineering Queries -->
                <div class="glass-panel">
                    <div class="eyebrow">
                        <span>03 // CONSULTAS TÉCNICAS RÁPIDAS</span>
                    </div>
                    <div class="quick-prompts">
                        <div class="prompt-btn" onclick="usarPrompt('Qual é o fck do concreto especificado para a fundação e para a superestrutura?')">
                            <span>Resistência do Concreto (fck)</span>
                            <span class="prompt-arrow">→</span>
                        </div>
                        <div class="prompt-btn" onclick="usarPrompt('Quais as dimensões e especificações das esquadrias e portas?')">
                            <span>Esquadrias e Acabamentos</span>
                            <span class="prompt-arrow">→</span>
                        </div>
                        <div class="prompt-btn" onclick="usarPrompt('Quais as marcas de tubulação de água e esgoto homologadas?')">
                            <span>Instalações Hidráulicas</span>
                            <span class="prompt-arrow">→</span>
                        </div>
                        <div class="prompt-btn" onclick="usarPrompt('Existe previsão de piscina aquecida ou heliponto no projeto?')">
                            <span>Auditoria de Ausência</span>
                            <span class="prompt-arrow">→</span>
                        </div>
                    </div>
                </div>

            </div>

            <!-- Right Workspace (Chat) -->
            <div class="glass-panel workspace-area">
                <div class="workspace-top">
                    <div>
                        <div class="obra-header-title" id="display-obra-nome">Carregando Obra...</div>
                        <div class="obra-header-desc">Engenharia RAG • Gemini 3.8 Flash • Respostas com Citação de Página</div>
                    </div>

                    <button class="btn-glass" onclick="limparHistoricoChat()">Limpar Consulta</button>
                </div>

                <!-- Chat Thread -->
                <div class="chat-thread" id="chat-thread">
                    <div class="empty-state" id="empty-state">
                        <div class="hero-badge empty-badge">
                            <div class="pulsing-dot"></div>
                            <span>Pronto para Consulta</span>
                        </div>
                        <div class="empty-title">A próxima revolução é no canteiro de obras.</div>
                        <div class="empty-desc">Anexe os memoriais descritivos, cadernos de encargos ou laudos de sondagem da obra para iniciar a consulta técnica auditada com o Gemini 3.8 Flash.</div>
                    </div>
                </div>

                <!-- Bottom Input Dock -->
                <div class="input-dock">
                    <input type="text" id="input-pergunta" placeholder="Consulte o memorial da obra (ex: Qual o fck da fundação?)" onkeypress="if(event.key === 'Enter') enviarPergunta()">
                    <button class="btn-accent btn-send-pill" id="btn-enviar" onclick="enviarPergunta()">
                        <span>Consultar Obra</span>
                    </button>
                </div>
            </div>
        </main>

        <!-- Modal Nova Obra -->
        <div class="modal-backdrop" id="modal-nova-obra">
            <div class="modal-box">
                <div class="modal-header">Cadastrar Nova Obra</div>
                
                <div class="eyebrow" style="margin-bottom: 4px;">IDENTIFICADOR TÉCNICO (SLUG)</div>
                <input type="text" id="modal-id" placeholder="ex: residencial-horizonte">
                
                <div class="eyebrow" style="margin-bottom: 4px;">NOME DA OBRA</div>
                <input type="text" id="modal-nome" placeholder="ex: Edifício Horizonte Azul">
                
                <div class="eyebrow" style="margin-bottom: 4px;">LOCALIZAÇÃO / ESCOPO</div>
                <input type="text" id="modal-desc" placeholder="ex: Av. Atlântica, 1500 - Residencial Multifamiliar">
                
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button class="btn-glass" style="flex: 1;" onclick="fecharModalNovaObra()">Cancelar</button>
                    <button class="btn-accent" style="flex: 1;" onclick="confirmarNovaObra()">Cadastrar</button>
                </div>
            </div>
        </div>

        <script>
            let obraAtiva = "";

            window.addEventListener('DOMContentLoaded', async () => {
                await carregarListaObras();
                configurarDragAndDrop();
            });

            async function carregarListaObras() {
                try {
                    const res = await fetch('/api/obras');
                    const obras = await res.json();
                    const select = document.getElementById('select-obras');
                    select.innerHTML = '';

                    if (obras.length === 0) {
                        await fetch('/api/obras', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                id: 'edificio-horizonte',
                                nome: 'Edifício Horizonte Azul',
                                descricao: 'Residencial Multifamiliar • Av. Atlântica, 1500'
                            })
                        });
                        return carregarListaObras();
                    }

                    obras.forEach(o => {
                        select.innerHTML += `<option value="${o.id}">${o.nome}</option>`;
                    });

                    if (!obraAtiva && obras.length > 0) {
                        obraAtiva = obras[0].id;
                    }
                    select.value = obraAtiva;
                    await atualizarEstatisticas();
                } catch(e) {
                    console.error(e);
                }
            }

            async function trocarObra() {
                const select = document.getElementById('select-obras');
                obraAtiva = select.value;
                await atualizarEstatisticas();
                limparHistoricoChat();
            }

            async function atualizarEstatisticas() {
                if (!obraAtiva) return;
                const select = document.getElementById('select-obras');
                const nomeSelecionado = select.options[select.selectedIndex]?.text || obraAtiva;
                
                document.getElementById('display-obra-nome').innerText = nomeSelecionado;

                try {
                    const res = await fetch(`/api/obras/${obraAtiva}/stats`);
                    const stats = await res.json();

                    document.getElementById('stat-docs').innerText = stats.total_documentos || 0;
                    document.getElementById('stat-chunks').innerText = stats.total_chunks || 0;

                    const docList = document.getElementById('doc-list');
                    if (stats.arquivos && stats.arquivos.length > 0) {
                        docList.innerHTML = stats.arquivos.map(a => `
                            <div class="file-row">
                                <span class="file-name">${a.nome}</span>
                                <span class="file-chunks-badge">${a.chunks} chunks</span>
                            </div>
                        `).join('');
                    } else {
                        docList.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 6px;">Nenhum documento ativo.</div>`;
                    }
                } catch(e) {
                    console.error(e);
                }
            }

            function configurarDragAndDrop() {
                const zone = document.getElementById('drop-zone');
                ['dragenter', 'dragover'].forEach(eventName => {
                    zone.addEventListener(eventName, (e) => { e.preventDefault(); zone.classList.add('dragover'); }, false);
                });
                ['dragleave', 'drop'].forEach(eventName => {
                    zone.addEventListener(eventName, (e) => { e.preventDefault(); zone.classList.remove('dragover'); }, false);
                });
                zone.addEventListener('drop', (e) => {
                    const dt = e.dataTransfer;
                    const files = dt.files;
                    if (files.length) {
                        document.getElementById('file-input').files = files;
                        arquivoSelecionado(document.getElementById('file-input'));
                    }
                });
            }

            function arquivoSelecionado(input) {
                const label = document.getElementById('file-selected-name');
                const btn = document.getElementById('btn-upload');
                if (input.files[0]) {
                    label.innerText = `Arquivo pronto: ${input.files[0].name}`;
                    label.style.display = "block";
                    btn.disabled = false;
                } else {
                    label.style.display = "none";
                    btn.disabled = true;
                }
            }

            async function executarUpload() {
                const fileInput = document.getElementById('file-input');
                if (!fileInput.files[0] || !obraAtiva) return;

                const btn = document.getElementById('btn-upload');
                btn.disabled = true;
                btn.innerText = "Processando no Canteiro...";

                const formData = new FormData();
                formData.append('arquivo', fileInput.files[0]);

                try {
                    const res = await fetch(`/api/obras/${obraAtiva}/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();
                    if (res.ok) {
                        alert(`Sucesso! ${data.chunks_vetorizados} trechos técnicos indexados nesta obra.`);
                        fileInput.value = "";
                        document.getElementById('file-selected-name').style.display = "none";
                        await atualizarEstatisticas();
                    } else {
                        alert(`Erro: ${data.detail || 'Falha no processamento'}`);
                    }
                } catch(e) {
                    alert("Erro ao enviar arquivo.");
                } finally {
                    btn.disabled = false;
                    btn.innerText = "Fatiar e Vetorizar no Canteiro";
                }
            }

            function usarPrompt(texto) {
                document.getElementById('input-pergunta').value = texto;
                enviarPergunta();
            }

            async function enviarPergunta() {
                const input = document.getElementById('input-pergunta');
                const pergunta = input.value.trim();
                if (!pergunta || !obraAtiva) return;

                const emptyState = document.getElementById('empty-state');
                if (emptyState) emptyState.style.display = 'none';

                const thread = document.getElementById('chat-thread');
                
                thread.innerHTML += `
                    <div class="chat-message user">
                        <div class="chat-avatar">ENG</div>
                        <div class="chat-bubble">${pergunta}</div>
                    </div>
                `;
                input.value = "";
                thread.scrollTop = thread.scrollHeight;

                const loadingId = 'ai-loading-' + Date.now();
                thread.innerHTML += `
                    <div class="chat-message ai" id="${loadingId}">
                        <div class="chat-avatar">AI</div>
                        <div class="chat-bubble" style="display: flex; align-items: center; gap: 8px;">
                            <div class="pulsing-dot"></div>
                            <span style="font-family: 'Space Mono', monospace; font-size: 11.5px; color: var(--text-secondary);">Consultando base técnica e gerando parecer auditado...</span>
                        </div>
                    </div>
                `;
                thread.scrollTop = thread.scrollHeight;

                const btn = document.getElementById('btn-enviar');
                btn.disabled = true;

                try {
                    const res = await fetch(`/api/obras/${obraAtiva}/perguntar`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({pergunta})
                    });
                    const data = await res.json();
                    
                    const loadingEl = document.getElementById(loadingId);
                    if (loadingEl) loadingEl.remove();

                    let fontesCard = "";
                    if (data.fontes && data.fontes.length > 0) {
                        const tags = data.fontes.map(f => `
                            <div class="audit-badge">
                                <b>${f.arquivo}</b> (Pág ${f.pagina}) • <span>${Math.round(f.score * 100)}% relevância</span>
                            </div>
                        `).join('');

                        fontesCard = `
                            <div class="audit-card">
                                <div class="audit-title">AUDITORIA DOCUMENTAL (FONTES CITADAS)</div>
                                <div class="audit-tags">${tags}</div>
                            </div>
                        `;
                    }

                    const respostaHtml = marked.parse(data.resposta || "Sem resposta gerada.");

                    thread.innerHTML += `
                        <div class="chat-message ai">
                            <div class="chat-avatar">AI</div>
                            <div class="chat-bubble">
                                ${respostaHtml}
                                ${fontesCard}
                            </div>
                        </div>
                    `;
                } catch(e) {
                    const loadingEl = document.getElementById(loadingId);
                    if (loadingEl) loadingEl.remove();
                    thread.innerHTML += `
                        <div class="chat-message ai">
                            <div class="chat-avatar" style="background: #991b1b;">ERR</div>
                            <div class="chat-bubble" style="color: var(--text);">Falha de comunicação: ${e.message || "Erro inesperado"}</div>
                        </div>
                    `;
                } finally {
                    btn.disabled = false;
                    thread.scrollTop = thread.scrollHeight;
                }
            }

            function limparHistoricoChat() {
                const thread = document.getElementById('chat-thread');
                thread.innerHTML = `
                    <div class="empty-state" id="empty-state">
                        <div class="hero-badge empty-badge">
                            <div class="pulsing-dot"></div>
                            <span>Pronto para Consulta</span>
                        </div>
                        <div class="empty-title">A próxima revolução é no canteiro de obras.</div>
                        <div class="empty-desc">Anexe os memoriais descritivos, cadernos de encargos ou laudos de sondagem da obra para iniciar a consulta técnica auditada com o Gemini 3.8 Flash.</div>
                    </div>
                `;
            }

            function abrirModalNovaObra() {
                document.getElementById('modal-nova-obra').style.display = 'flex';
            }

            function fecharModalNovaObra() {
                document.getElementById('modal-nova-obra').style.display = 'none';
            }

            async function confirmarNovaObra() {
                const id = document.getElementById('modal-id').value.trim();
                const nome = document.getElementById('modal-nome').value.trim();
                const desc = document.getElementById('modal-desc').value.trim();

                if (!id || !nome) return alert("Preencha o identificador e o nome da obra!");

                await fetch('/api/obras', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id, nome, descricao: desc})
                });

                fecharModalNovaObra();
                document.getElementById('modal-id').value = '';
                document.getElementById('modal-nome').value = '';
                document.getElementById('modal-desc').value = '';

                obraAtiva = id;
                await carregarListaObras();
            }
        </script>
    </body>
    </html>
    """
