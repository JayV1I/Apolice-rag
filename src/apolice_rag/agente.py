"""Extração com autocorreção, orquestrada com LangGraph.

Para cada campo, o grafo roda:

    buscar -> extrair -> verificar --(confere)--> fim
                ^                  |
                |            (não confere ou vazio, e ainda há tentativas)
                +--- reformular <--+

Se o trecho citado pelo LLM não existe no PDF (ou o campo veio vazio), o agente pede
ao LLM uma nova pergunta de busca, com outros termos, e tenta de novo. O histórico de
tentativas volta junto com a ficha, para dar para auditar o que aconteceu.
"""
from typing import Callable, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from .extrator import CAMPOS, Resposta, _contexto, _modelo
from .grounding import verificar

MAX_TENTATIVAS = 3


class Estado(TypedDict, total=False):
    campo: str
    instrucao: str
    pergunta: str
    tentativa: int
    resultados: list
    resposta: Resposta
    fonte: dict | None
    historico: list[dict]


def montar_grafo(
    buscar_fn: Callable[[str], list],
    extrair_fn: Callable[[str, str], Resposta],
    reformular_fn: Callable[[str, str, list[str]], str],
    paginas: list[str],
    max_tentativas: int = MAX_TENTATIVAS,
):
    """Monta o grafo. As funções entram por parâmetro para dar para testar sem LLM nem banco."""

    def no_buscar(e: Estado) -> Estado:
        return {"resultados": buscar_fn(e["pergunta"]), "tentativa": e.get("tentativa", 0) + 1}

    def no_extrair(e: Estado) -> Estado:
        if not e["resultados"]:
            return {"resposta": Resposta()}
        return {"resposta": extrair_fn(e["instrucao"], _contexto(e["resultados"]))}

    def no_verificar(e: Estado) -> Estado:
        r = e["resposta"]
        fonte = verificar(paginas, r.pagina, r.trecho) if r.valor and r.trecho else None
        registro = {"tentativa": e["tentativa"], "pergunta": e["pergunta"], "valor": r.valor,
                    "confere": bool(fonte and fonte["confere"])}
        return {"fonte": fonte, "historico": e.get("historico", []) + [registro]}

    def no_reformular(e: Estado) -> Estado:
        anteriores = [h["pergunta"] for h in e["historico"]]
        return {"pergunta": reformular_fn(e["instrucao"], e["pergunta"], anteriores)}

    def decidir(e: Estado) -> str:
        if e["historico"][-1]["confere"] or e["tentativa"] >= max_tentativas:
            return "fim"
        return "reformular"

    g = StateGraph(Estado)
    g.add_node("buscar", no_buscar)
    g.add_node("extrair", no_extrair)
    g.add_node("verificar", no_verificar)
    g.add_node("reformular", no_reformular)
    g.set_entry_point("buscar")
    g.add_edge("buscar", "extrair")
    g.add_edge("extrair", "verificar")
    g.add_conditional_edges("verificar", decidir, {"fim": END, "reformular": "reformular"})
    g.add_edge("reformular", "buscar")
    return g.compile()


PROMPT_REFORMULAR = ChatPromptTemplate.from_messages([
    ("system",
     "Você reescreve consultas de busca para apólices de seguro de carga. "
     "A busca anterior não encontrou a informação. Gere UMA nova consulta curta (até 12 palavras), "
     "com sinônimos e termos técnicos de seguro diferentes dos já usados. Responda só a consulta."),
    ("human", "Informação procurada: {instrucao}\nConsultas já tentadas: {anteriores}"),
])


def extrair_com_agente(conn, documento: str, k: int = 4, campos: list[str] | None = None) -> dict:
    from langchain_ollama import ChatOllama

    from . import config
    from .busca import buscar
    from .indice import paginas_do_documento

    llm = ChatOllama(model=config.modelo_llm(), base_url=config.ollama_url(), temperature=0, num_ctx=4096)
    cadeia_extrair = _modelo()
    cadeia_reformular = PROMPT_REFORMULAR | llm

    grafo = montar_grafo(
        buscar_fn=lambda pergunta: buscar(conn, documento, pergunta, k=k),
        extrair_fn=lambda instrucao, contexto: cadeia_extrair.invoke({"instrucao": instrucao, "contexto": contexto}),
        reformular_fn=lambda instrucao, _p, anteriores: cadeia_reformular.invoke(
            {"instrucao": instrucao, "anteriores": "; ".join(anteriores)}).content.strip().strip('"'),
        paginas=paginas_do_documento(conn, documento),
    )

    ficha = {}
    for campo, (pergunta, instrucao) in CAMPOS.items():
        if campos and campo not in campos:
            continue
        final = grafo.invoke({"campo": campo, "instrucao": instrucao, "pergunta": pergunta})
        ficha[campo] = {
            "valor": final["resposta"].valor,
            "fonte": final["fonte"],
            "tentativas": final["historico"],
        }
    return ficha
