"""Linha de comando.

    python -m apolice_rag.cli init
    python -m apolice_rag.cli indexar dados/apolices/*.pdf
    python -m apolice_rag.cli buscar apolice_horizonte "cobre roubo de carga?" --modo hibrido
    python -m apolice_rag.cli extrair apolice_horizonte
    python -m apolice_rag.cli extrair apolice_horizonte --agente
    python -m apolice_rag.cli avaliar avaliacao/gabarito_busca.json
"""
import argparse
import glob
import json

from .agente import extrair_com_agente
from .avaliacao import avaliar
from .busca import buscar
from .extrator import extrair
from .indice import conectar, criar_schema, indexar


def main() -> None:
    parser = argparse.ArgumentParser(prog="apolice_rag")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("init", help="cria extensão, tabelas e índices")

    p = sub.add_parser("indexar", help="indexa um ou mais PDFs")
    p.add_argument("pdfs", nargs="+")

    p = sub.add_parser("buscar", help="busca trechos numa apólice")
    p.add_argument("documento")
    p.add_argument("pergunta")
    p.add_argument("--modo", choices=["hibrido", "lexical", "vetorial"], default="hibrido")
    p.add_argument("-k", type=int, default=5)

    p = sub.add_parser("extrair", help="extrai a ficha da apólice")
    p.add_argument("documento")
    p.add_argument("--agente", action="store_true", help="usa o grafo LangGraph com reformulação da busca")
    p.add_argument("--campo", action="append", help="extrai só este campo (pode repetir)")

    p = sub.add_parser("avaliar", help="recall@k dos três modos de busca")
    p.add_argument("gabarito")
    p.add_argument("-k", type=int, default=5)

    args = parser.parse_args()
    with conectar() as conn:
        if args.comando == "init":
            criar_schema(conn)
            print("Schema criado.")
        elif args.comando == "indexar":
            criar_schema(conn)
            arquivos = [a for padrao in args.pdfs for a in (glob.glob(padrao) or [padrao])]
            for pdf in arquivos:
                print(f"{pdf}: {indexar(conn, pdf)} trechos")
        elif args.comando == "buscar":
            for r in buscar(conn, args.documento, args.pergunta, k=args.k, modo=args.modo):
                print(f"\n[p. {r.pagina}] nota {r.nota:.4f} via {', '.join(r.origem)}\n{r.conteudo}")
        elif args.comando == "extrair":
            funcao = extrair_com_agente if args.agente else extrair
            print(json.dumps(funcao(conn, args.documento, campos=args.campo), ensure_ascii=False, indent=2))
        elif args.comando == "avaliar":
            print(json.dumps(avaliar(conn, args.gabarito, k=args.k), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
