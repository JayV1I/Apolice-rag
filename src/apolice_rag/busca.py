"""Busca híbrida: palavra-chave (full-text) + vetorial (pgvector), unidas por RRF.

- A busca por palavra-chave acerta termo exato (número de cláusula, "LMG", valores).
- A busca vetorial acerta sinônimo ("roubo" x "subtração mediante grave ameaça").
- O RRF junta as duas sem precisar comparar as notas de escalas diferentes.
"""
import re
from dataclasses import dataclass

import numpy as np
import psycopg

from .fusao import rrf
from .indice import embeddings
from .pdf_texto import normalizar

# Palavras vazias que só atrapalham a consulta OR do full-text.
_VAZIAS = {"qual", "quais", "como", "onde", "quando", "para", "pela", "pelo", "sobre",
           "esta", "este", "essa", "esse", "sao", "tem", "existe", "apolice"}


@dataclass
class Resultado:
    id: int
    pagina: int
    conteudo: str
    nota: float
    origem: list[str]


def _consulta_ou(pergunta: str) -> str:
    """Transforma a pergunta numa tsquery com OR entre as palavras relevantes.

    `plainto_tsquery` usa AND, e uma pergunta em linguagem natural quase nunca tem
    todas as palavras no mesmo trecho. Com OR, o ts_rank decide quem tem mais.
    """
    palavras = [p for p in re.findall(r"[a-z0-9]+", normalizar(pergunta))
                if len(p) > 2 and p not in _VAZIAS]
    return " | ".join(palavras)


def busca_lexical(conn: psycopg.Connection, documento: str, pergunta: str, k: int = 10) -> list[int]:
    consulta = _consulta_ou(pergunta)
    if not consulta:
        return []
    linhas = conn.execute(
        """
        SELECT id FROM trechos, to_tsquery('portuguese', %s) q
        WHERE documento = %s AND tsv @@ q
        ORDER BY ts_rank_cd(tsv, q) DESC, id
        LIMIT %s
        """,
        (consulta, documento, k),
    ).fetchall()
    return [l[0] for l in linhas]


def busca_vetorial(conn: psycopg.Connection, documento: str, pergunta: str, k: int = 10) -> list[int]:
    vetor = np.array(embeddings().embed_query(pergunta), dtype=np.float32)
    linhas = conn.execute(
        "SELECT id FROM trechos WHERE documento = %s ORDER BY embedding <=> %s, id LIMIT %s",
        (documento, vetor, k),
    ).fetchall()
    return [l[0] for l in linhas]


def buscar(conn: psycopg.Connection, documento: str, pergunta: str, k: int = 5,
           modo: str = "hibrido") -> list[Resultado]:
    """`modo`: "hibrido", "lexical" ou "vetorial". Útil para comparar na avaliação."""
    rankings = {}
    if modo in ("hibrido", "lexical"):
        rankings["palavra-chave"] = busca_lexical(conn, documento, pergunta, k=k * 4)
    if modo in ("hibrido", "vetorial"):
        rankings["vetorial"] = busca_vetorial(conn, documento, pergunta, k=k * 4)

    fundidos = rrf(rankings)[:k]
    if not fundidos:
        return []
    ids = [f[0] for f in fundidos]
    linhas = {l[0]: l for l in conn.execute(
        "SELECT id, pagina, conteudo FROM trechos WHERE id = ANY(%s)", (ids,)).fetchall()}
    return [Resultado(id_, linhas[id_][1], linhas[id_][2], nota, origem)
            for id_, nota, origem in fundidos]
