"""Reciprocal Rank Fusion (RRF): junta rankings de buscas diferentes.

Cada item ganha 1 / (k + posição) em cada lista em que aparece, e as notas são
somadas. Um trecho que vai bem nas duas buscas (palavra-chave e vetorial) sobe para
o topo, sem precisar normalizar escalas de nota diferentes.
"""


def rrf(rankings: dict[str, list[int]], k: int = 60) -> list[tuple[int, float, list[str]]]:
    """`rankings` mapeia o nome da busca para a lista de ids em ordem de relevância.

    Devolve (id, nota, buscas_que_acharam) do mais relevante para o menos.
    """
    notas: dict[int, float] = {}
    origem: dict[int, list[str]] = {}
    for nome, ids in rankings.items():
        for posicao, id_ in enumerate(ids, start=1):
            notas[id_] = notas.get(id_, 0.0) + 1.0 / (k + posicao)
            origem.setdefault(id_, []).append(nome)
    ordenado = sorted(notas.items(), key=lambda x: (-x[1], x[0]))
    return [(id_, nota, origem[id_]) for id_, nota in ordenado]
