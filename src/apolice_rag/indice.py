"""Indexação no PostgreSQL: texto + vetor (pgvector) + índice full-text (tsvector).

Uma tabela só guarda as duas "visões" do trecho:
- `embedding`: para a busca por significado (vetorial);
- `tsv`: para a busca por palavra-chave (full-text do Postgres, em português).
"""
from pathlib import Path

import numpy as np
import psycopg
from psycopg.types.json import Jsonb
from langchain_ollama import OllamaEmbeddings
from pgvector.psycopg import register_vector

from . import config
from .chunking import Trecho, dividir
from .pdf_texto import ler_paginas, remover_repetidos


def conectar() -> psycopg.Connection:
    conn = psycopg.connect(config.database_url(), autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=config.modelo_embedding(), base_url=config.ollama_url())


def criar_schema(conn: psycopg.Connection) -> None:
    dim = config.dimensao_embedding()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS trechos (
            id         serial PRIMARY KEY,
            documento  text    NOT NULL,
            pagina     int     NOT NULL,
            ordem      int     NOT NULL,
            conteudo   text    NOT NULL,
            embedding  vector({dim}) NOT NULL,
            tsv        tsvector GENERATED ALWAYS AS (to_tsvector('portuguese', conteudo)) STORED,
            UNIQUE (documento, ordem)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS trechos_hnsw ON trechos "
                 "USING hnsw (embedding vector_cosine_ops)")
    conn.execute("CREATE INDEX IF NOT EXISTS trechos_tsv ON trechos USING gin (tsv)")
    conn.execute("CREATE TABLE IF NOT EXISTS documentos ("
                 "nome text PRIMARY KEY, arquivo text NOT NULL, paginas jsonb NOT NULL)")


def nome_documento(caminho_pdf: str) -> str:
    return Path(caminho_pdf).stem


def indexar(conn: psycopg.Connection, caminho_pdf: str) -> int:
    """Lê o PDF, quebra em trechos, gera os embeddings e grava. Reindexar substitui."""
    nome = nome_documento(caminho_pdf)
    paginas = remover_repetidos(ler_paginas(caminho_pdf))
    trechos: list[Trecho] = dividir(nome, paginas)
    vetores = embeddings().embed_documents([t.conteudo for t in trechos])

    with conn.transaction():
        conn.execute("DELETE FROM trechos WHERE documento = %s", (nome,))
        conn.execute(
            "INSERT INTO documentos (nome, arquivo, paginas) VALUES (%s, %s, %s) "
            "ON CONFLICT (nome) DO UPDATE SET arquivo = EXCLUDED.arquivo, paginas = EXCLUDED.paginas",
            (nome, str(caminho_pdf), Jsonb(paginas)),
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO trechos (documento, pagina, ordem, conteudo, embedding) "
                "VALUES (%s, %s, %s, %s, %s)",
                [(t.documento, t.pagina, t.ordem, t.conteudo, np.array(v, dtype=np.float32))
                 for t, v in zip(trechos, vetores)],
            )
    return len(trechos)


def paginas_do_documento(conn: psycopg.Connection, nome: str) -> list[str]:
    linha = conn.execute("SELECT paginas FROM documentos WHERE nome = %s", (nome,)).fetchone()
    if not linha:
        raise ValueError(f"Documento não indexado: {nome}")
    return linha[0]
