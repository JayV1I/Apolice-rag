"""Testa o fluxo do grafo LangGraph com funções falsas, sem LLM e sem banco."""
from types import SimpleNamespace

from apolice_rag.agente import montar_grafo
from apolice_rag.extrator import VAZIA, Resposta

PAGINAS = ["Item 2. Garante-se a indenização pela subtração da mercadoria mediante grave ameaça."]
TRECHO = SimpleNamespace(pagina=1, conteudo=PAGINAS[0])


def _rodar(extrair_fn, max_tentativas=3):
    perguntas = []
    grafo = montar_grafo(
        buscar_fn=lambda p: perguntas.append(p) or [TRECHO],
        extrair_fn=extrair_fn,
        reformular_fn=lambda i, p, anteriores: f"nova consulta {len(anteriores)}",
        paginas=PAGINAS,
        max_tentativas=max_tentativas,
    )
    final = grafo.invoke({"campo": "cobertura_roubo", "instrucao": "cobre roubo?", "pergunta": "roubo de carga"})
    return final, perguntas


def test_para_na_primeira_quando_confere():
    final, perguntas = _rodar(lambda i, c: Resposta(valor="sim", pagina=1, trecho="subtração da mercadoria"))
    assert perguntas == ["roubo de carga"]
    assert final["historico"][-1]["confere"]


def test_reformula_quando_trecho_inventado():
    respostas = iter([
        Resposta(valor="sim", pagina=1, trecho="cobertura de roubo qualificado"),  # inventado
        Resposta(valor="sim", pagina=1, trecho="subtração da mercadoria mediante grave ameaça"),
    ])
    final, perguntas = _rodar(lambda i, c: next(respostas))
    assert perguntas == ["roubo de carga", "nova consulta 1"]
    assert [h["confere"] for h in final["historico"]] == [False, True]


def test_desiste_no_limite_de_tentativas():
    final, perguntas = _rodar(lambda i, c: VAZIA, max_tentativas=2)
    assert len(perguntas) == 2
    assert final["resposta"].valor == ""
