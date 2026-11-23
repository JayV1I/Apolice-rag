"""Verificação de grounding: o trecho que a IA citou existe mesmo no PDF?

Regra de ouro do projeto: a IA propõe, o código confere. Um valor cuja citação não
é encontrada no documento original fica marcado como `confere=False` e precisa de
conferência humana.
"""
from .pdf_texto import normalizar


def _palavras_longas(texto: str) -> list[str]:
    return [p for p in normalizar(texto).split() if len(p) >= 5]


def verificar(paginas: list[str], pagina: int | None, trecho: str | None,
              tolerancia: float = 0.8) -> dict:
    """Procura o trecho na página indicada, depois em qualquer página.

    Se a IA "costurou" o trecho (juntou pedaços), aceita quando `tolerancia` das
    palavras longas estão na mesma página, e marca como aproximado.
    """
    if not trecho:
        return {"pagina": pagina, "trecho": trecho, "confere": False}
    alvo = normalizar(trecho)
    normais = [normalizar(p) for p in paginas]

    ordem = list(range(len(normais)))
    if pagina and 1 <= pagina <= len(normais):
        ordem.remove(pagina - 1)
        ordem.insert(0, pagina - 1)

    for i in ordem:
        if alvo in normais[i]:
            return {"pagina": i + 1, "trecho": trecho, "confere": True}

    palavras = _palavras_longas(trecho)
    if palavras:
        for i in ordem:
            achadas = sum(1 for p in palavras if p in normais[i])
            if achadas / len(palavras) >= tolerancia:
                return {"pagina": i + 1, "trecho": trecho, "confere": True, "aproximado": True}

    return {"pagina": pagina, "trecho": trecho, "confere": False}
