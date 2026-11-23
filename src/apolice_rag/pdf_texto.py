"""Leitura do PDF página a página e limpeza do texto."""
import re
import unicodedata
from collections import Counter

import pymupdf


def ler_paginas(caminho_pdf: str) -> list[str]:
    """Texto de cada página, na ordem. A página 1 é o índice 0."""
    with pymupdf.open(caminho_pdf) as doc:
        return [pagina.get_text("text") for pagina in doc]


def remover_repetidos(paginas: list[str], fracao_minima: float = 0.6) -> list[str]:
    """Remove linhas que se repetem na maioria das páginas (cabeçalho e rodapé da seguradora).

    Isso diminui o texto que vai para o modelo e evita que o cabeçalho "polua" a busca.
    """
    if len(paginas) < 3:
        return paginas

    def molde(linha: str) -> str:
        # "Página 2 de 5" e "Página 3 de 5" viram o mesmo molde
        return re.sub(r"\d+", "#", linha.strip())

    contagem = Counter()
    for pagina in paginas:
        contagem.update({molde(l) for l in pagina.splitlines() if l.strip()})
    minimo = fracao_minima * len(paginas)
    repetidas = {m for m, n in contagem.items() if n >= minimo}
    return [
        "\n".join(l for l in pagina.splitlines() if molde(l) not in repetidas)
        for pagina in paginas
    ]


def normalizar(texto: str) -> str:
    """Minúsculo, sem acento e com espaços colapsados. Usado só para comparar."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()
