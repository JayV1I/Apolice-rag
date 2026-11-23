"""Gera 3 apólices de seguro de carga FICTÍCIAS em PDF, para testes e demonstração.

Seguradoras, transportadoras, CNPJs, números e valores são inventados.
Cada apólice escreve as mesmas ideias com palavras diferentes, de propósito, para
mostrar onde a busca por palavra-chave falha e a vetorial acerta (e vice-versa).

Uso: python scripts/gerar_apolices_ficticias.py
"""
from pathlib import Path

import pymupdf

SAIDA = Path(__file__).resolve().parent.parent / "dados" / "apolices"

CONDICOES_GERAIS = (
    "Estas condições gerais regem a relação entre a Seguradora e o Segurado e devem ser lidas "
    "em conjunto com as condições especiais e a especificação da apólice. Em caso de divergência, "
    "prevalecem as condições especiais. O Segurado obriga-se a comunicar à Seguradora qualquer "
    "alteração que possa agravar o risco coberto, sob pena de perda do direito à indenização. "
    "As comunicações devem ser feitas por escrito, no prazo estabelecido nesta apólice. "
    "A Seguradora poderá inspecionar os procedimentos de embarque a qualquer tempo, mediante aviso prévio."
)

APOLICES = {
    "apolice_horizonte": {
        "cabecalho": "SEGURADORA HORIZONTE S.A. | Apólice RCF-DC | Documento fictício para testes",
        "paginas": [
            ["ESPECIFICAÇÃO DA APÓLICE",
             "Seguradora: Seguradora Horizonte S.A.",
             "Segurado: Transportes Rota Sul Ltda.",
             "CNPJ do Segurado: 00.111.222/0001-00",
             "Número da Apólice: HZ-2026-000123",
             "Vigência: das 24h de 01/01/2026 às 24h de 01/01/2027.",
             "Ramo: Responsabilidade Civil Facultativa por Desaparecimento de Carga (RCF-DC)."],
            ["CLÁUSULA 3 - RISCOS COBERTOS",
             "3.1 Está coberto o roubo de carga ocorrido durante o transporte rodoviário, inclusive "
             "quando o veículo transportador estiver estacionado em local autorizado.",
             "3.2 Está coberto o furto qualificado da carga, desde que comprovado por boletim de ocorrência.",
             "CLÁUSULA 4 - LIMITES",
             "4.1 Limite Máximo de Garantia (LMG) por veículo: R$ 500.000,00 (quinhentos mil reais).",
             "4.2 Para cargas de eletrônicos, o LMG fica limitado a R$ 250.000,00 por veículo."],
            ["CLÁUSULA 5 - BENS NÃO COMPREENDIDOS NO SEGURO",
             "Não estão cobertos: dinheiro em espécie, joias, obras de arte, armas e munições, "
             "animais vivos e cargas de cigarros.",
             "CLÁUSULA 6 - GERENCIAMENTO DE RISCO",
             "6.1 Para embarques acima de R$ 150.000,00 é obrigatório rastreador com bloqueio remoto.",
             "6.2 Acima de R$ 350.000,00, além do rastreador, é obrigatória escolta armada.",
             "6.3 É proibida a circulação entre 22h00 e 05h00 em rodovias de pista simples."],
            ["CONDIÇÕES GERAIS", CONDICOES_GERAIS, CONDICOES_GERAIS],
        ],
    },
    "apolice_atlantica": {
        "cabecalho": "ATLÂNTICA SEGUROS S.A. | Seguro de Responsabilidade Civil | Documento fictício",
        "paginas": [
            ["QUADRO RESUMO",
             "Emitente: Atlântica Seguros S.A.",
             "Tomador e Segurado: Logística Serra Azul Ltda.",
             "CNPJ: 00.333.444/0001-00",
             "Apólice nº AT-55-0099881",
             "Período de cobertura: 15/03/2026 a 15/03/2027."],
            ["CONDIÇÕES ESPECIAIS - COBERTURA",
             "Item 2. Garante-se a indenização pela subtração da mercadoria mediante grave ameaça "
             "ou violência à pessoa do motorista, durante o percurso.",
             "Item 3. Importância segurada máxima por embarque: R$ 800.000,00 (oitocentos mil reais), "
             "considerada a soma das notas fiscais transportadas no mesmo veículo."],
            ["CONDIÇÕES ESPECIAIS - EXCLUSÕES E OBRIGAÇÕES",
             "Item 7. Ficam excluídos da cobertura: medicamentos controlados, celulares e componentes "
             "eletrônicos, bebidas destiladas e combustíveis.",
             "Item 8. O Segurado deverá manter o veículo monitorado por sistema de rastreamento via "
             "satélite durante toda a viagem e utilizar isca eletrônica na carga em embarques "
             "superiores a R$ 400.000,00.",
             "Item 9. Fica vedado o trânsito no período noturno, das 23h às 06h, salvo em postos de "
             "parada cadastrados."],
            ["CONDIÇÕES GERAIS", CONDICOES_GERAIS, CONDICOES_GERAIS],
            ["CONDIÇÕES GERAIS (continuação)", CONDICOES_GERAIS],
        ],
    },
    "apolice_vale_verde": {
        "cabecalho": "SEGUROS VALE VERDE S.A. | RC Transporte de Cargas | Documento fictício",
        "paginas": [
            ["DADOS DO CONTRATO",
             "Companhia seguradora: Seguros Vale Verde S.A.",
             "Contratante: TransMinas Cargas Ltda., CNPJ 00.555.666/0001-00",
             "Contrato de seguro número VV/2026/4471",
             "Início de vigência em 01/07/2026 e término em 30/06/2027."],
            ["COBERTURAS CONTRATADAS",
             "a) Assalto à mão armada contra o veículo transportador, com perda total ou parcial da carga.",
             "b) Desaparecimento do veículo com a carga durante o trajeto.",
             "Teto de indenização por veículo: R$ 1.200.000,00 (um milhão e duzentos mil reais)."],
            ["CARGAS SEM COBERTURA",
             "Não serão indenizados sinistros envolvendo defensivos agrícolas, pneus, "
             "minério de alto valor, cosméticos e produtos farmacêuticos.",
             "PROCEDIMENTOS OBRIGATÓRIOS",
             "Todo embarque deve ter consulta de motorista aprovada, rastreamento ativo e "
             "comunicação de início de viagem à central de monitoramento. "
             "Valores acima de R$ 600.000,00 exigem duas tecnologias de rastreamento distintas e escolta.",
             "Não é permitido rodar entre 21h e 05h nos estados com índice crítico de ocorrências."],
            ["CONDIÇÕES GERAIS", CONDICOES_GERAIS],
        ],
    },
}


def gerar(nome: str, dados: dict) -> Path:
    doc = pymupdf.open()
    total = len(dados["paginas"])
    for numero, blocos in enumerate(dados["paginas"], start=1):
        pagina = doc.new_page(width=595, height=842)  # A4
        pagina.insert_text((50, 40), dados["cabecalho"], fontsize=8, fontname="helv")
        texto = "\n\n".join(blocos)
        pagina.insert_textbox(pymupdf.Rect(50, 70, 545, 790), texto, fontsize=10, fontname="helv")
        pagina.insert_text((50, 815), f"Página {numero} de {total} | Documento fictício, sem valor contratual",
                           fontsize=8, fontname="helv")
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / f"{nome}.pdf"
    doc.save(caminho)
    doc.close()
    return caminho


if __name__ == "__main__":
    for nome, dados in APOLICES.items():
        print("gerado:", gerar(nome, dados))
