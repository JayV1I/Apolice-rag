"""Quebra do documento em trechos para indexação.

Estratégia: respeitar parágrafos (uma cláusula costuma ser um parágrafo) e só cortar
um parágrafo grande quando ele passa do tamanho máximo, com sobreposição entre os
pedaços para não separar a regra da exceção.
"""
from dataclasses import dataclass


@dataclass
class Trecho:
    documento: str
    pagina: int  # começa em 1
    ordem: int  # posição do trecho dentro do documento
    conteudo: str


def _paragrafos(texto: str) -> list[str]:
    blocos, atual = [], []
    for linha in texto.splitlines():
        if linha.strip():
            atual.append(linha.strip())
        elif atual:
            blocos.append(" ".join(atual))
            atual = []
    if atual:
        blocos.append(" ".join(atual))
    return blocos


def _cortar(texto: str, tamanho: int, sobreposicao: int) -> list[str]:
    if len(texto) <= tamanho:
        return [texto]
    pedacos, inicio = [], 0
    while inicio < len(texto):
        fim = min(len(texto), inicio + tamanho)
        if fim < len(texto):
            espaco = texto.rfind(" ", inicio + tamanho // 2, fim)
            if espaco > 0:
                fim = espaco
        pedacos.append(texto[inicio:fim].strip())
        if fim >= len(texto):
            break
        inicio = max(fim - sobreposicao, inicio + 1)
    return pedacos


def dividir(documento: str, paginas: list[str], tamanho: int = 800,
            sobreposicao: int = 150) -> list[Trecho]:
    """Junta parágrafos de uma página até `tamanho` caracteres por trecho."""
    trechos, ordem = [], 0
    for num, texto in enumerate(paginas, start=1):
        buffer = ""
        for paragrafo in _paragrafos(texto):
            for parte in _cortar(paragrafo, tamanho, sobreposicao):
                if buffer and len(buffer) + len(parte) + 1 > tamanho:
                    trechos.append(Trecho(documento, num, ordem, buffer))
                    ordem += 1
                    buffer = ""
                buffer = f"{buffer} {parte}".strip()
        if buffer:
            trechos.append(Trecho(documento, num, ordem, buffer))
            ordem += 1
    return trechos
