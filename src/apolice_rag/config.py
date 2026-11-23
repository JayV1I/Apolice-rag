"""Configuração lida do ambiente.

As variáveis são lidas dentro das funções, e não no topo do módulo, para que um
`.env` carregado depois do import (ou um teste que muda o ambiente) seja respeitado.
"""
import os


def database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag")


def ollama_url() -> str:
    return os.getenv("OLLAMA_URL", "http://localhost:11434")


def modelo_llm() -> str:
    return os.getenv("LLM_MODEL", "qwen2.5:7b")


def modelo_embedding() -> str:
    return os.getenv("EMBED_MODEL", "nomic-embed-text")


def dimensao_embedding() -> int:
    return int(os.getenv("EMBED_DIM", "768"))
