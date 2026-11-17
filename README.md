# Enterprise AI Workbench

**Laboratório de arquitetura de IA corporativa: RAG com fontes, ferramentas MCP e modelos locais ou APIs.**

Criado por [Rodrigo Antonicci](https://github.com/Antonicci) · [Chihuahuas Studios](https://chihuahuasstudios.com/architectures/)

Este projeto demonstra como investigar um incidente com documentos autorizados e dados operacionais. A pergunta não define permissões: o backend valida a identidade, filtra o conhecimento, consulta ferramentas permitidas e fornece evidências para revisão humana.

> **Status: v0.1 / laboratório, dados sintéticos.** Não é uma plataforma pronta para produção. O modo padrão funciona sem GPU ou API e **não usa LLM**: retorna trechos recuperados por hashing lexical. O modo Ollama/API habilita embeddings semânticos e geração real. Métricas MCP são sintéticas em todos os modos.

## O que já existe

| Capacidade | Implementação |
|---|---|
| Interface web | React + TypeScript; investigação, fontes, métricas e ingestão textual |
| Backend | FastAPI, validação de entrada, credenciais e grupos definidos no servidor |
| RAG | Chunking com overlap, embeddings, busca por similaridade e contexto com fontes |
| Modelos | Demo extrativa, Ollama ou endpoint compatível com Chat Completions **e** Embeddings |
| LangChain | Integrações de modelos encapsuladas no adaptador de provedor |
| Persistência | Memória ou PostgreSQL + pgvector, seleção por configuração |
| MCP real | SDK Python v1, transporte stdio, handshake e chamada de ferramenta pelo cliente |
| Ferramentas | Métricas sintéticas restritas a operations; busca documental por MCP |
| Segurança do laboratório | Filtro de grupos antes do ranking; ingestão restrita; sem ferramentas de escrita |
| Rastreabilidade | Trace ID, duração, fontes e ferramentas; logs sem prompts, tokens ou documentos |

O fluxo web usa RAG diretamente e MCP para métricas. O servidor MCP também expõe busca documental para clientes externos locais. Em memória, essa busca vê somente o corpus empacotado; para compartilhar documentos ingeridos pela web entre processos, use PostgreSQL.

## Experimente em poucos minutos

Pré-requisitos: Git e Docker com Compose. Para desenvolvimento sem Docker: Python 3.11+ e Node 22.12+.

```bash
git clone https://github.com/Antonicci/enterprise-ai-workbench.git
cd enterprise-ai-workbench
cp .env.example .env
docker compose up --build
```

No PowerShell, use `Copy-Item .env.example .env` no lugar de `cp` se preferir.

Abra **http://localhost:8080**, clique em **Conectar** e pergunte:

> Como investigar erros HTTP 500 na API de pedidos?

1. Com `demo-analyst`, confira o runbook e as fontes.
2. Troque a credencial para `demo-ops` e conecte novamente.
3. Habilite **Consultar métricas via MCP** e repita a consulta.
4. Veja a execução `get_service_metrics`, o horário da coleta e os dados sintéticos.
5. Em **Conhecimento**, adicione um texto sintético e consulte-o.

As credenciais demo são públicas e só podem ser usadas com dados sintéticos em máquina local. A interface mantém a credencial em memória; não a persiste no navegador.

## Executar com Ollama e vetores persistentes

1. Instale o Ollama no host e baixe um modelo de chat e outro de embeddings:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

2. Em `.env`, configure `PROVIDER=ollama`, `STORE=postgres` e substitua `AUTH_TOKENS` por tokens aleatórios longos. Exemplo de formato (substitua os valores, não os use):

```dotenv
AUTH_TOKENS={"SUBSTITUA_ANALYST":["employees"],"SUBSTITUA_OPS":["employees","operations"]}
```

3. Inicie o banco e aguarde estar saudável antes do backend:

```bash
docker compose --profile vector up -d db
docker compose --profile vector ps
docker compose --profile vector up --build backend frontend
```

A URL do Ollama no exemplo é `http://host.docker.internal:11434`. No Linux, o daemon precisa aceitar conexões da rede Docker; restrinja esse acesso à rede necessária. Nunca exponha a porta do Ollama à internet. Alternativamente, execute o backend no host e use `http://localhost:11434`.

O modelo 3B quantizado é um ponto inicial para hardware limitado; consumo e latência dependem de contexto, quantização e concorrência. Valide antes de ampliar. Após baixar imagens, dependências e modelos, o modo local pode operar sem API externa; teste o egress antes de declará-lo offline.

## Usar uma API corporativa

Configure `PROVIDER=openai-compatible`, `API_BASE_URL`, `API_KEY`, `CHAT_MODEL` e `EMBEDDING_MODEL`. O endpoint precisa suportar os contratos de chat e embeddings usados pelos adaptadores. **Isso não garante compatibilidade automática com Azure, Bedrock ou qualquer gateway**; endpoints com autenticação/protocolo diferente precisam de adaptador próprio.

Nesse modo, trechos e perguntas são enviados ao provedor; textos completos também são enviados para embeddings durante a ingestão. Exija aprovação de dados e contrato do provedor. Não há fallback automático entre nuvem e local.

## Desenvolvimento local

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.lock
pip install --no-deps -e ./backend
# A partir da raiz, sem .env usa demo em memória.
uvicorn workbench.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Abra http://localhost:5173. O Vite encaminha `/api` para o backend, sem exigir CORS amplo.

Se copiar `.env.example` para executar no host, ajuste URLs: `OLLAMA_BASE_URL=http://localhost:11434`; o banco do Compose não publica porta no host. Use banco local ou um túnel/override explícito.

## Verificação

```bash
python -m pytest backend/tests -q
cd frontend
npm ci
npm run build
```

Os testes cobrem isolamento de documentos, autenticação, restrição das ferramentas, ingestão, substituição de documentos e chamadas MCP pelo protocolo real. Não substituem avaliação de qualidade de LLM nem teste de carga. Veja [validação](docs/07-validation.md).

## Trilha corporativa

1. [Discovery e escopo](docs/01-discovery-and-scope.md)
2. [Escolha entre regras, ML, LLM, RAG e MCP](docs/02-solution-selection.md)
3. [Arquitetura e limites](docs/03-architecture.md)
4. [Segurança e modelo de ameaças](docs/04-security.md)
5. [Implementação passo a passo](docs/05-implementation-guide.md)
6. [Avaliação e operação](docs/06-evaluation-and-operations.md)
7. [Evidências de validação](docs/07-validation.md)
8. [Decisões arquiteturais](docs/adr/0001-modular-monolith.md)
9. [Roadmap](ROADMAP.md)

## Limitações que fazem parte do desenho

- Credenciais estáticas de laboratório; OIDC/SSO, RLS, isolamento multitenant e auditoria durável ainda não implementados.
- Fontes retornadas são evidências recuperadas, não comprovação automática de cada frase gerada. O modelo pode alucinar ou ignorar instruções.
- Corpus empacotado é reindexado no startup. Ingestões em memória desaparecem ao reiniciar; documentos com IDs do corpus são restaurados no startup.
- Chunking por caracteres e busca exata; sem parsing de PDF, reranker, HNSW, ingestão assíncrona ou detecção de prompt injection dedicada.
- Timeout de requisição não interrompe necessariamente uma operação síncrona já iniciada em thread; não há controle global de concorrência/quotas.
- Logs de aplicação não são um sistema de auditoria imutável. Não há monitoramento contínuo, integração real de incidentes ou ações autônomas.
- O MCP está fixado no SDK **v1**; a migração para v2 exige revisão de protocolo e APIs.

Nenhum dado real de cliente, credencial ou documento empresarial deve ser incluído no repositório.
