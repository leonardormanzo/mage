import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from civil_rag_saas.chunking import fatiar_texto
from civil_rag_saas.database import salvar_chunk, buscar_documentos_similares

load_dotenv()

EMBEDDING_MODEL = "models/gemini-embedding-001"
# A coluna `vetor` do banco é vector(768). O gemini-embedding-001 devolve 3072
# dimensões por padrão, então a dimensão precisa ser pedida explicitamente.
EMBEDDING_DIM = 768
CHAT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.8-flash"
]

_client = None


def get_client() -> genai.Client:
    """Cria o cliente só quando é usado, para os testes rodarem sem chave."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GEMINI_API_KEY não está configurada.")
        _client = genai.Client(api_key=api_key)
    return _client


def gerar_embedding(texto: str, tarefa: str) -> list[float]:
    """Gera o vetor de um texto. `tarefa` é RETRIEVAL_DOCUMENT ou RETRIEVAL_QUERY."""
    resp = get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texto,
        config=types.EmbedContentConfig(task_type=tarefa, output_dimensionality=EMBEDDING_DIM),
    )
    return list(resp.embeddings[0].values)


def indexar_documento_na_obra(obra_id: str, paginas_documento: list[dict]):
    """
    Recebe os blocos extraídos do arquivo, fatia em chunks,
    gera os embeddings no Gemini e persiste no banco PostgreSQL (Neon) com pgvector.
    """
    total_chunks = 0
    for doc in paginas_documento:
        arquivo = doc["arquivo"]
        pagina = doc["pagina"]
        texto_pagina = doc["conteudo"]

        pedacos = fatiar_texto(texto_pagina)
        for pedaco in pedacos:
            # Gera o vetor no Gemini
            vetor = gerar_embedding(pedaco, "RETRIEVAL_DOCUMENT")
            
            # Salva no banco com o vínculo da obra
            salvar_chunk(obra_id, arquivo, pagina, pedaco, vetor)
            total_chunks += 1

    return total_chunks

def consultar_obra(obra_id: str, pergunta: str, top_k: int = 3) -> dict:
    """
    Busca os trechos mais parecidos daquela obra usando a busca vetorial nativa do PostgreSQL
    e gera a resposta técnica com Gemini.
    """
    # 1. Vetoriza a pergunta do usuário
    try:
        vetor_pergunta = gerar_embedding(pergunta, "RETRIEVAL_QUERY")
    except Exception as e:
        return {
            "resposta": f"Falha ao gerar embedding da pergunta: {e}",
            "fontes": []
        }

    # 2. Faz a busca de similaridade diretamente no PostgreSQL/Neon
    mais_relevantes = buscar_documentos_similares(obra_id, vetor_pergunta, limite=top_k)

    if not mais_relevantes:
        return {
            "resposta": "Esta obra ainda não possui documentos indexados ou não há contexto suficiente.",
            "fontes": []
        }

    # 3. Constrói o contexto com citações técnicas
    contexto_blocos = []
    fontes = []
    for item in mais_relevantes:
        # Pega as chaves retornadas pelo PostgreSQL
        arquivo = item["arquivo"]
        pagina = item["pagina"]
        score = item["similaridade"]
        texto = item["texto"]

        citacao = f"[Arquivo: {arquivo} | Pág: {pagina} | Relevância: {score:.2f}]"
        contexto_blocos.append(f"{citacao}\n{texto}")
        fontes.append({
            "arquivo": arquivo,
            "pagina": pagina,
            "score": round(score, 3)
        })

    contexto_str = "\n\n---\n\n".join(contexto_blocos)

    # 4. Prompt de Engenharia Civil para o Gemini
    prompt = f"""Você é o Engenheiro Especialista Responsável Técnico da Obra.
Sua missão é responder à dúvida com precisão cirúrgica, estritamente baseado nos documentos técnicos anexados abaixo.

DIRETRIZES:
1. Sempre cite o documento e a página de onde a informação foi extraída.
2. Use linguagem técnica de Engenharia Civil e Arquitetura.
3. Se a informação NÃO estiver contida nos documentos fornecidos, afirme claramente: "Esta informação não consta nas especificações técnicas disponibilizadas para esta obra." Nunca invente ou suponha.

DOCUMENTAÇÃO TÉCNICA RELEVANTE DA OBRA:
{contexto_str}

PERGUNTA DO CLIENTE/ENGENHEIRO:
{pergunta}
"""

    # 5. Execução com Fallback automático entre modelos disponíveis
    ultima_excecao = None
    for model_name in CHAT_MODELS:
        try:
            resposta = get_client().models.generate_content(
                model=model_name,
                contents=prompt
            )
            if resposta and resposta.text:
                return {
                    "resposta": resposta.text,
                    "fontes": fontes,
                    "modelo": model_name
                }
        except Exception as err:
            ultima_excecao = err
            print(f"[ArcTech IA Fallback] Modelo {model_name} falhou: {err}. Tentando próximo...")
            continue

    return {
        "resposta": f"Erro de comunicação temporário com o provedor de IA: {ultima_excecao}. Por favor, tente novamente em instantes.",
        "fontes": fontes
    }
