"""Servidor MCP (Model Context Protocol) expondo a busca e a extração como ferramentas.

Com isso, qualquer cliente MCP (Claude Desktop, Claude Code, outros agentes) pode
consultar as apólices indexadas. Rodar: `python -m apolice_rag.mcp_server`.
"""
from mcp.server.mcpserver import MCPServer

from .busca import buscar
from .extrator import extrair
from .indice import conectar

mcp = MCPServer("apolice-rag")


@mcp.tool()
def listar_apolices() -> list[str]:
    """Lista os documentos (apólices) já indexados."""
    with conectar() as conn:
        return [l[0] for l in conn.execute("SELECT nome FROM documentos ORDER BY nome").fetchall()]


@mcp.tool()
def buscar_trechos(documento: str, pergunta: str, k: int = 5) -> list[dict]:
    """Busca híbrida (palavra-chave + vetorial) nos trechos de uma apólice."""
    with conectar() as conn:
        return [{"pagina": r.pagina, "conteudo": r.conteudo, "nota": round(r.nota, 4), "origem": r.origem}
                for r in buscar(conn, documento, pergunta, k=k)]


@mcp.tool()
def extrair_ficha(documento: str) -> dict:
    """Extrai a ficha da apólice, com página e trecho de cada campo conferidos no PDF."""
    with conectar() as conn:
        return extrair(conn, documento)


if __name__ == "__main__":
    mcp.run()
