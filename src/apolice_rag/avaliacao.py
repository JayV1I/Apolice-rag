"""Avaliação da recuperação: o trecho certo aparece entre os k primeiros?

Mede recall@k para os três modos de busca, separado da geração. Se a busca não
traz o trecho certo, não adianta culpar o LLM.
"""
import json
from pathlib import Path

from .busca import buscar
from .pdf_texto import normalizar


def avaliar(conn, caminho_gabarito: str, k: int = 5) -> dict:
    casos = json.loads(Path(caminho_gabarito).read_text(encoding="utf-8"))
    resultado = {}
    for modo in ("lexical", "vetorial", "hibrido"):
        acertos = 0
        for caso in casos:
            achados = buscar(conn, caso["documento"], caso["pergunta"], k=k, modo=modo)
            esperado = normalizar(caso["deve_conter"])
            if any(esperado in normalizar(r.conteudo) for r in achados):
                acertos += 1
        resultado[modo] = {"recall_at_k": round(acertos / len(casos), 3), "acertos": acertos, "casos": len(casos)}
    return resultado
