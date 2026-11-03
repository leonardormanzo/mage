import math

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.dialects import postgresql

from app.core.config import BASE_DIR
from app.database.models import DocumentChunk, Project
from app.services import ai
from app.services.ai.providers import EMBEDDING_DIMENSION, MockEmbeddingProvider
from app.services.documents import chunk_text
from app.services.rag.vector_store import (
    build_vector_statement,
    cosine_similarity,
    search_chunks,
)
from tests.conftest import login

MANUAL = (
    "O cimento deve ser armazenado sobre estrados de madeira, longe da umidade. "
    "A pilha não deve passar de dez sacos."
).encode()


def _upload(client, project_id: str, content: bytes = MANUAL, name: str = "manual.txt"):
    return client.post(
        f"/api/projects/{project_id}/documents",
        files={"file": (name, content, "text/plain")},
    )


def _project_id(db_session, code: str) -> str:
    return db_session.scalar(select(Project).where(Project.code == code)).id


def test_mock_embedder_is_deterministic_normalized_and_ranks_related_text():
    provider = MockEmbeddingProvider()
    document = provider.embed("Conferir formas e armaduras antes da concretagem")
    related = provider.embed("O que conferir antes da concretagem?", task="query")
    unrelated = provider.embed("Cronograma de entrega das esquadrias de alumínio", task="query")

    assert len(document) == EMBEDDING_DIMENSION
    assert math.isclose(math.sqrt(sum(v * v for v in document)), 1.0, rel_tol=1e-9)
    assert document == provider.embed("Conferir formas e armaduras antes da concretagem")
    assert cosine_similarity(document, related) > cosine_similarity(document, unrelated)


def test_chunking_overlaps_and_never_returns_blank_pieces():
    pieces = chunk_text("palavra " * 400, size=900, overlap=100)
    assert len(pieces) >= 3
    assert all(piece.strip() for piece in pieces)
    assert all(len(piece) <= 900 for piece in pieces)
    assert pieces[0][-50:].strip() in pieces[1]
    assert chunk_text("   \n  ") == []


def test_upload_embeds_chunks_and_query_finds_them_by_vector(client, db_session):
    me = login(client, "engenheiro@arc.local")
    project_id = me["projects"][0]["id"]
    uploaded = _upload(client, project_id)
    assert uploaded.status_code == 200
    body = uploaded.json()
    assert body["chunks"] >= 1
    assert body["embedded_chunks"] == body["chunks"]
    assert body["embedder"] == MockEmbeddingProvider().name

    answer = client.post(
        f"/api/projects/{project_id}/query", json={"question": "Como armazenar o cimento?"}
    ).json()
    assert answer["route"] == "documental"
    assert answer["retrieval"] == "vector"
    assert "estrados" in answer["answer"]
    assert answer["sources"][0]["label"] == "manual.txt"
    assert 0 < answer["confidence"] <= 1


def test_seeded_document_is_retrieved_by_vector(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    answer = client.post(
        f"/api/projects/{project_id}/query",
        json={"question": "O que conferir antes da concretagem?"},
    ).json()
    assert answer["retrieval"] == "vector"
    assert "armaduras" in answer["answer"]


def test_question_without_evidence_is_not_answered(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    answer = client.post(
        f"/api/projects/{project_id}/query",
        json={"question": "Qual foi a ocorrência com o guindaste amarelo?"},
    ).json()
    assert answer["confidence"] == 0.0
    assert answer["sources"] == []


def test_search_never_crosses_projects(client, db_session):
    me = login(client, "engenheiro@arc.local")
    restricted = _project_id(db_session, "OR-002")
    secret = b"O cofre secreto do container fica na sala azul do segundo andar."
    assert _upload(client, restricted, secret, "segredo.txt").status_code == 200

    login(client, "trabalhador@arc.local")
    visible = me["projects"][0]["id"]
    answer = client.post(
        f"/api/projects/{visible}/query", json={"question": "Onde fica o cofre secreto?"}
    ).json()
    assert answer["sources"] == []
    assert "segredo.txt" not in str(answer)


def test_search_ignores_vectors_from_another_embedder(db_session):
    project = db_session.scalar(select(Project))
    provider = MockEmbeddingProvider()
    vector = provider.embed("estrados de madeira para o cimento")
    db_session.add(
        DocumentChunk(
            company_id=project.company_id,
            project_id=project.id,
            document_id=db_session.scalar(select(DocumentChunk.document_id)),
            content="trecho gerado por outro modelo",
            embedding=vector,
            metadata_json={"embedder": "outro-modelo"},
        )
    )
    db_session.commit()
    hits = search_chunks(
        db_session,
        company_id=project.company_id,
        project_id=project.id,
        embedding=vector,
        embedder=provider.name,
        limit=5,
        min_score=0.0,
    )
    assert all(chunk.content != "trecho gerado por outro modelo" for _, chunk, _ in hits)


def test_search_respects_limit_threshold_and_order(client, db_session):
    me = login(client, "engenheiro@arc.local")
    project_id = me["projects"][0]["id"]
    _upload(client, project_id)
    project = db_session.get(Project, project_id)
    provider = MockEmbeddingProvider()
    query = provider.embed("armazenar cimento estrados", task="query")

    hits = search_chunks(
        db_session,
        company_id=project.company_id,
        project_id=project.id,
        embedding=query,
        embedder=provider.name,
        limit=1,
        min_score=0.1,
    )
    assert len(hits) == 1
    assert hits[0][1].content.startswith("O cimento deve ser armazenado")
    assert hits[0][0] > 0.1

    none = search_chunks(
        db_session,
        company_id=project.company_id,
        project_id=project.id,
        embedding=query,
        embedder=provider.name,
        limit=5,
        min_score=0.99,
    )
    assert none == []


def test_postgres_statement_uses_pgvector_cosine_operator():
    statement = build_vector_statement(
        company_id="c", project_id="p", embedding=[0.1] * EMBEDDING_DIMENSION, embedder="x", limit=3
    )
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "<=>" in sql
    assert "ORDER BY" in sql and "LIMIT" in sql
    assert "company_id" in sql and "project_id" in sql


class _BrokenEmbedder(MockEmbeddingProvider):
    def embed(self, text: str, task: str = "document") -> list[float]:
        raise RuntimeError("serviço de embeddings indisponível")


def test_embedding_failure_keeps_document_searchable_lexically(client, monkeypatch):
    monkeypatch.setattr(ai, "get_embedding_provider", lambda: _BrokenEmbedder())
    me = login(client, "engenheiro@arc.local")
    project_id = me["projects"][0]["id"]
    uploaded = _upload(client, project_id).json()
    assert uploaded["chunks"] >= 1
    assert uploaded["embedded_chunks"] == 0

    answer = client.post(
        f"/api/projects/{project_id}/query", json={"question": "Como armazenar o cimento?"}
    ).json()
    assert answer["retrieval"] == "lexical"
    assert answer["sources"][0]["label"] == "manual.txt"


def _alembic_config(connection) -> Config:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    config.attributes["connection"] = connection
    return config


def test_migrations_build_the_current_schema_from_scratch(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}")
    with engine.begin() as connection:
        command.upgrade(_alembic_config(connection), "head")
        columns = {c["name"] for c in inspect(connection).get_columns("document_chunks")}
    assert "embedding" in columns
    assert "embedding_json" not in columns


def test_migration_moves_legacy_embeddings_to_the_new_column(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE document_chunks (id VARCHAR(36) PRIMARY KEY, company_id VARCHAR(36), "
                "project_id VARCHAR(36), document_id VARCHAR(36), content TEXT, page INTEGER, "
                "metadata_json JSON, embedding_json JSON)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO document_chunks (id, company_id, project_id, document_id, content, "
                "metadata_json, embedding_json) VALUES ('1','c','p','d','texto','{}','[0.5, 0.25]')"
            )
        )
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
        )
        connection.execute(text("INSERT INTO alembic_version VALUES ('0002')"))
        command.upgrade(_alembic_config(connection), "head")
        columns = {c["name"] for c in inspect(connection).get_columns("document_chunks")}
        stored = connection.execute(text("SELECT embedding FROM document_chunks")).scalar_one()
    assert "embedding" in columns and "embedding_json" not in columns
    assert stored == "[0.5, 0.25]"
