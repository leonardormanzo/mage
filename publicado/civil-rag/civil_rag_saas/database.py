import os
import json
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

def inicializar_banco():
    """Cria as tabelas necessárias no Neon/PostgreSQL usando pgvector."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ativa a extensão de vetor do PostgreSQL
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 1. Tabela de Obras cadastradas no SaaS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            descricao TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Tabela de Chunks de Documentos com pgvector
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            obra_id TEXT NOT NULL,
            arquivo TEXT NOT NULL,
            pagina INTEGER NOT NULL,
            texto TEXT NOT NULL,
            vetor vector(768),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (obra_id) REFERENCES obras (id) ON DELETE CASCADE
        )
    """)
    
    # Cria o índice HNSW para busca em grande escala
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS chunks_vetor_idx ON chunks USING hnsw (vetor vector_cosine_ops);
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

def criar_obra(obra_id: str, nome: str, descricao: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO obras (id, nome, descricao) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (obra_id, nome, descricao)
    )
    conn.commit()
    cursor.close()
    conn.close()

def listar_obras():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, descricao FROM obras")
    obras = [{"id": l[0], "nome": l[1], "descricao": l[2]} for l in cursor.fetchall()]
    cursor.close()
    conn.close()
    return obras

def salvar_chunk(obra_id: str, arquivo: str, pagina: int, texto: str, vetor: list[float]):
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chunks (obra_id, arquivo, pagina, texto, vetor) VALUES (%s, %s, %s, %s, %s)",
        (obra_id, arquivo, pagina, texto, vetor)
    )
    conn.commit()
    cursor.close()
    conn.close()

def buscar_chunks_da_obra(obra_id: str):
    """
    Retorna os chunks brutos para o Python. (Substituído em RAG escalável por buscar_documentos_similares)
    """
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, arquivo, pagina, texto, vetor::text FROM chunks WHERE obra_id = %s",
        (obra_id,)
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    resultados = []
    for l in linhas:
        resultados.append({
            "id": l[0],
            "arquivo": l[1],
            "pagina": l[2],
            "texto": l[3],
            "vetor": json.loads(l[4])
        })
    return resultados

def buscar_documentos_similares(obra_id: str, vetor_pergunta: list[float], limite: int = 5):
    """Busca diretamente no PostgreSQL/pgvector usando distância de cosseno (<=>). Muito mais rápido!"""
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT arquivo, pagina, texto, 1 - (vetor <=> %s::vector) AS similaridade
        FROM chunks 
        WHERE obra_id = %s
        ORDER BY vetor <=> %s::vector
        LIMIT %s
    """, (vetor_pergunta, obra_id, vetor_pergunta, limite))
    
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    resultados = []
    for l in linhas:
        resultados.append({
            "arquivo": l[0],
            "pagina": l[1],
            "texto": l[2],
            "similaridade": l[3]
        })
    return resultados

def obter_estatisticas_obra(obra_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT COUNT(id) as total_chunks, COUNT(DISTINCT arquivo) as total_documentos FROM chunks WHERE obra_id = %s",
        (obra_id,)
    )
    res = cursor.fetchone()
    
    cursor.execute(
        "SELECT arquivo, COUNT(id) as chunks FROM chunks WHERE obra_id = %s GROUP BY arquivo",
        (obra_id,)
    )
    arquivos = [{"nome": row[0], "chunks": row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return {
        "total_chunks": res[0] if res else 0,
        "total_documentos": res[1] if res else 0,
        "arquivos": arquivos
    }
