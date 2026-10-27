import os
import pypdf
import docx

def extrair_texto_arquivo(caminho_arquivo: str) -> list[dict]:
    """
    Extrai o texto de um arquivo (PDF, DOCX ou TXT).
    Retorna uma lista de blocos com metadados:
    [
        {"conteudo": "texto da pagina/secao...", "pagina": 1, "arquivo": "memorial.pdf"},
        ...
    ]
    """
    nome_arquivo = os.path.basename(caminho_arquivo)
    extensao = nome_arquivo.split(".")[-1].lower()
    documentos = []

    if extensao == "pdf":
        leitor = pypdf.PdfReader(caminho_arquivo)
        for num_pagina, pagina in enumerate(leitor.pages, start=1):
            texto = pagina.extract_text() or ""
            if texto.strip():
                documentos.append({
                    "conteudo": texto.strip(),
                    "pagina": num_pagina,
                    "arquivo": nome_arquivo
                })

    elif extensao == "docx":
        doc = docx.Document(caminho_arquivo)
        texto_completo = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if texto_completo.strip():
            documentos.append({
                "conteudo": texto_completo.strip(),
                "pagina": 1,
                "arquivo": nome_arquivo
            })

    elif extensao in ["txt", "md"]:
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
            texto = f.read()
            if texto.strip():
                documentos.append({
                    "conteudo": texto.strip(),
                    "pagina": 1,
                    "arquivo": nome_arquivo
                })
    else:
        raise ValueError(f"Formato .{extensao} não suportado. Use PDF, DOCX ou TXT.")

    return documentos
