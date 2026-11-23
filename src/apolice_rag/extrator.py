"""Extração da ficha da apólice com LLM local (Ollama) via LangChain.

Para cada campo:
1. busca híbrida recupera os trechos relevantes (RAG);
2. o LLM recebe só esses trechos e devolve JSON estruturado: valor, página e trecho literal;
3. o grounding confere se o trecho citado existe no PDF original.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from . import config
from .busca import buscar
from .grounding import verificar
from .indice import paginas_do_documento


class Resposta(BaseModel):
    valor: str | None = Field(None, description="Valor do campo, ou null se não estiver nos trechos")
    pagina: int | None = Field(None, description="Número da página de onde o valor saiu")
    trecho: str | None = Field(None, description="Cópia literal e curta (até 150 caracteres) do texto que comprova o valor")


# campo -> (pergunta usada na busca, instrução para o modelo)
CAMPOS = {
    "segurado": ("nome do segurado transportadora", "Nome da empresa segurada."),
    "seguradora": ("seguradora emissora da apólice", "Nome da seguradora."),
    "numero_apolice": ("número da apólice", "Número da apólice, exatamente como escrito."),
    "vigencia": ("vigência início e término do seguro", "Período de vigência (de ... até ...)."),
    "limite_maximo_garantia": ("limite máximo de garantia por veículo embarque valor R$",
                               "Limite máximo de garantia (LMG) por veículo, com o valor em R$."),
    "cobertura_roubo": ("cobertura de roubo de carga subtração da mercadoria",
                        "A apólice cobre roubo de carga? Responda 'sim' ou 'não' e cite a cláusula."),
    "mercadorias_excluidas": ("mercadorias não cobertas bens excluídos",
                              "Lista resumida das mercadorias excluídas da cobertura."),
    "restricao_horario": ("horário proibido de circulação rodagem noturna",
                          "Horário em que a circulação é proibida, se houver."),
    "gerenciamento_risco": ("exigências de gerenciamento de risco rastreador escolta isca",
                            "Exigências de gerenciamento de risco (rastreador, escolta, isca etc.)."),
}

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Você extrai dados de apólices de seguro de transporte de carga. "
     "Use SOMENTE os trechos fornecidos. Se a informação não estiver neles, devolva valor null. "
     "No campo 'trecho', copie literalmente um pedaço curto do texto que comprova o valor. "
     "Nunca invente valores, datas ou números."),
    ("human", "Campo: {instrucao}\n\nTrechos da apólice:\n{contexto}"),
])


def _modelo():
    llm = ChatOllama(model=config.modelo_llm(), base_url=config.ollama_url(), temperature=0)
    return PROMPT | llm.with_structured_output(Resposta)


def _contexto(resultados) -> str:
    return "\n\n".join(f"[PÁGINA {r.pagina}]\n{r.conteudo}" for r in resultados)


def extrair(conn, documento: str, k: int = 4) -> dict:
    paginas = paginas_do_documento(conn, documento)
    cadeia = _modelo()
    ficha = {}
    for campo, (pergunta, instrucao) in CAMPOS.items():
        resultados = buscar(conn, documento, pergunta, k=k)
        if not resultados:
            ficha[campo] = {"valor": None, "fonte": None}
            continue
        resposta: Resposta = cadeia.invoke({"instrucao": instrucao, "contexto": _contexto(resultados)})
        fonte = verificar(paginas, resposta.pagina, resposta.trecho) if resposta.valor else None
        ficha[campo] = {"valor": resposta.valor, "fonte": fonte}
    return ficha
