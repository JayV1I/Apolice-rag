"""Testes que não dependem de banco nem de Ollama."""
from pathlib import Path

from apolice_rag.chunking import dividir
from apolice_rag.fusao import rrf
from apolice_rag.grounding import verificar
from apolice_rag.pdf_texto import ler_paginas, normalizar, remover_repetidos

PDF = Path(__file__).resolve().parent.parent / "dados" / "apolices" / "apolice_horizonte.pdf"


def test_rrf_premia_quem_aparece_nas_duas_buscas():
    ranking = rrf({"palavra-chave": [1, 2, 3], "vetorial": [3, 4, 1]})
    ids = [r[0] for r in ranking]
    assert ids[:2] == [1, 3]  # 1 e 3 aparecem nas duas listas
    assert ranking[0][2] == ["palavra-chave", "vetorial"]


def test_rrf_listas_vazias():
    assert rrf({"palavra-chave": [], "vetorial": []}) == []


def test_normalizar_tira_acento_e_espaco():
    assert normalizar("  Subtração   da MERCADORIA ") == "subtracao da mercadoria"


def test_grounding_trecho_existente():
    paginas = ["capa", "O LMG por veículo é de R$ 500.000,00 conforme cláusula 4."]
    r = verificar(paginas, 2, "LMG por veículo é de R$ 500.000,00")
    assert r["confere"] and r["pagina"] == 2


def test_grounding_corrige_pagina_errada():
    paginas = ["capa", "O LMG por veículo é de R$ 500.000,00."]
    r = verificar(paginas, 1, "LMG por veículo é de R$ 500.000,00")
    assert r["confere"] and r["pagina"] == 2


def test_grounding_detecta_invencao():
    paginas = ["O LMG por veículo é de R$ 500.000,00."]
    r = verificar(paginas, 1, "cobertura de incêndio em armazém")
    assert not r["confere"]


def test_pdf_ficticio_remove_cabecalho_e_rodape():
    paginas = remover_repetidos(ler_paginas(str(PDF)))
    texto = "\n".join(paginas)
    assert "Documento fictício para testes" not in texto  # cabeçalho repetido
    assert "Página 2 de 4" not in texto  # rodapé com número variável
    assert "roubo de carga" in texto


def test_chunks_respeitam_tamanho():
    paginas = remover_repetidos(ler_paginas(str(PDF)))
    trechos = dividir("apolice_horizonte", paginas, tamanho=400, sobreposicao=50)
    assert trechos and all(len(t.conteudo) <= 450 for t in trechos)
    assert {t.pagina for t in trechos} == {1, 2, 3, 4}
