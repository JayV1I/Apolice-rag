# apolice-rag

Extração de dados de apólices de seguro de carga em PDF com **RAG híbrido** (busca por palavra-chave + busca vetorial, fundidas com RRF) e **LLM local** via Ollama.

> Todas as apólices, seguradoras, transportadoras, CNPJs e valores deste repositório são **fictícios**, gerados por `scripts/gerar_apolices_ficticias.py`.

## O problema

Apólices de seguradoras diferentes dizem a mesma coisa com palavras diferentes. Uma escreve "roubo de carga", outra "subtração da mercadoria mediante grave ameaça", outra "assalto à mão armada". Uma busca só por palavra-chave perde as duas últimas. Uma busca só vetorial às vezes perde valores exatos, como "R$ 800.000,00" ou "das 23h às 06h". Este projeto usa as duas e junta os resultados.

## Arquitetura

```
PDF ──> leitura (pymupdf) ──> remove cabeçalho/rodapé repetido ──> chunks por parágrafo (800 chars, sobreposição 150)
                                                                        │
                                                    ┌───────────────────┴───────────────────┐
                                            embeddings (nomic-embed-text)          tsvector 'portuguese'
                                                    │                                       │
                                            pgvector (HNSW, cosseno)               índice GIN (full-text)
                                                    └───────────────┬───────────────────────┘
                                                                    │
pergunta ──> busca vetorial + busca lexical ──> RRF (k=60) ──> top-k trechos ──> LLM (qwen2.5:7b, saída estruturada)
                                                                                         │
                                                                    grounding: o trecho citado existe na página?
```

| Módulo | O que faz |
|---|---|
| `pdf_texto.py` | Lê o PDF por página, remove linhas repetidas em 60%+ das páginas (números de página viram molde), normaliza texto |
| `chunking.py` | Divide por parágrafo, respeitando tamanho máximo e sobreposição |
| `indice.py` | Schema no Postgres (pgvector + tsvector gerado), indexação idempotente por documento |
| `busca.py` | Busca lexical (`ts_rank_cd`), vetorial (`<=>`) e híbrida |
| `fusao.py` | Reciprocal Rank Fusion |
| `extrator.py` | LangChain + `ChatOllama.with_structured_output` (Pydantic) campo a campo |
| `grounding.py` | Confere se o trecho citado pelo modelo está mesmo no PDF; corrige a página se o modelo errou |
| `avaliacao.py` | recall@k de cada modo de busca contra um gabarito |
| `mcp_server.py` | Expõe as ferramentas via MCP para qualquer cliente compatível |

### Por que o grounding

O modelo pode inventar um valor plausível. Cada campo extraído volta com `fonte.confere`: `true` só se o trecho literal (ou 80% das palavras relevantes) aparece na página. Campo sem fonte que confere não deve ser usado sem revisão humana.

## Como rodar

Pré-requisitos: Docker, Python 3.11+ e [Ollama](https://ollama.com) rodando na máquina.

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### Opção 1: tudo no Docker

```bash
docker compose up -d db
docker compose run --rm app init
docker compose run --rm app indexar "dados/apolices/*.pdf"
docker compose run --rm app buscar apolice_atlantica "a apólice cobre roubo de carga?" --modo hibrido
docker compose run --rm app extrair apolice_atlantica
docker compose run --rm app avaliar avaliacao/gabarito_busca.json
```

### Opção 2: Python local, banco no Docker

```bash
docker compose up -d db
python -m venv .venv && source .venv/bin/activate   # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd src
python -m apolice_rag.cli init
python -m apolice_rag.cli indexar "../dados/apolices/*.pdf"
python -m apolice_rag.cli extrair apolice_horizonte
```

Para regerar os PDFs fictícios: `python scripts/gerar_apolices_ficticias.py`.

### Testes

Os testes unitários não precisam de banco nem de Ollama:

```bash
pytest
```

### Servidor MCP

```json
{
  "mcpServers": {
    "apolice-rag": {
      "command": "python",
      "args": ["-m", "apolice_rag.mcp_server"],
      "cwd": "src"
    }
  }
}
```

Ferramentas: `listar_apolices`, `buscar_trechos`, `extrair_ficha`.

## Comparando os modos de busca

`avaliar` mede, para cada pergunta do gabarito, se o trecho esperado aparece entre os k primeiros resultados, nos três modos. O gabarito foi montado para que cada apólice use vocabulário diferente para o mesmo conceito, então o modo lexical tende a errar os sinônimos e o vetorial tende a errar valores e horários exatos. O híbrido deve ficar igual ou acima dos dois.

Resultado com as 3 apólices fictícias, 15 perguntas, k=5 (`qwen2.5:7b` + `nomic-embed-text`):

| Modo | recall@5 |
|---|---|
| Palavra-chave (full-text) | 66,7% (10/15) |
| Vetorial (pgvector) | 86,7% (13/15) |
| **Híbrido (RRF)** | **93,3% (14/15)** |

A busca por palavra-chave perde os sinônimos ("subtração da mercadoria", "assalto à mão armada"); a vetorial perde valores e horários exatos. Juntas, cobrem o ponto fraco uma da outra.

## Próximos passos

- Reranker (cross-encoder) depois da fusão
- Fluxo com LangGraph: buscar, extrair, verificar e, se o grounding falhar, reformular a pergunta e buscar de novo
- Avaliação da extração (não só da busca) contra uma ficha esperada por apólice
- API HTTP (FastAPI) para upload de PDF

## Licença

MIT
