# Enterprise AI Workbench

**Laboratório de arquitetura de IA corporativa: identidade, autorização, RAG, MCP e modelos locais ou APIs.**

[Rodrigo Antonicci](https://github.com/Antonicci) · [Chihuahuas Studios](https://chihuahuasstudios.com/architectures/)

## v0.2 — identidade e permissões visíveis

O usuário se autentica, o backend resolve seu perfil, filtra os documentos e autoriza cada ferramenta. A interface mostra identidade e permissões, permite editar documentos e oferece um mapa interativo dos componentes.

| Capacidade | Gestor de conhecimento | Consulta nível 1 | Consulta nível 2 |
|---|---|---|---|
| Consultar documentos nível 1 | Sim | Sim | Sim |
| Consultar documentos nível 2 | Sim | Não | Sim |
| Incluir, editar e classificar documentos | Sim | Não | Não |
| Consultar métricas da aplicação por MCP | Não | Não | Sim |
| Consultar métricas do assistente por MCP | Não | Não | Sim |

Perfis: `knowledge-manager`, `query-l1`, `query-l2`. Perfis concedem permissões; documentos têm classificação `level1` ou `level2`. A autorização acontece no servidor e também no worker MCP. Quem possui múltiplos perfis acumula permissões; os usuários iniciais têm um perfil cada.

> Laboratório com dados sintéticos. A resposta padrão é extrativa, **sem LLM**, e usa hashing lexical. Ollama/API habilitam geração e embeddings reais. Métricas da aplicação investigada são sintéticas. Métricas operacionais do assistente são medidas; custo, tokens e qualidade ainda não são medidos.

## Opção 1 — executar a demonstração sem provedor de identidade

Pré-requisitos: Git e Docker Compose.

```powershell
git clone https://github.com/Antonicci/enterprise-ai-workbench.git
cd enterprise-ai-workbench
Copy-Item .env.example .env
docker compose up --build
```

No Linux/macOS, use `cp .env.example .env`. Abra **http://localhost:8080**.

| Token público de laboratório | Perfil |
|---|---|
| demo-analyst | Consulta nível 1 |
| demo-ops | Consulta nível 2 |
| demo-manager | Gestor de conhecimento |

Digite o token e clique em **Conectar**. Eles existem somente no modo demo e não são aceitos no modo OIDC.

## Opção 2 — login real com Keycloak local

A partir da raiz, com `.env` criado:

```powershell
docker compose -f compose.yaml -f compose.oidc.yaml up --build
```

Aguarde o Keycloak terminar o startup. Abra **http://localhost:8080** e clique em **Entrar com SSO**. Use **localhost**, pois as URLs de callback e o emissor foram registrados para esse hostname.

| Usuário Keycloak | Perfil | Senha pública de laboratório |
|---|---|---|
| gestor | Gestor de conhecimento | Workbench-Lab-2026! |
| consulta1 | Consulta nível 1 | Workbench-Lab-2026! |
| consulta2 | Consulta nível 2 | Workbench-Lab-2026! |

Admin local: http://localhost:8180/admin — usuário `admin`, senha `Workbench-Admin-Lab-2026!`. Essas contas são públicas, para dados sintéticos e acesso loopback. O Keycloak usa `start-dev` e HTTP; isso não é configuração de produção.

Fluxo: Authorization Code + PKCE, access token destinado à API, validação RS256/JWKS, emissor, audiência e expiração. Tokens ficam em memória no navegador; estado temporário de login/PKCE usa sessionStorage. Recarregar a página exige entrar novamente; a sessão SSO pode evitar nova senha. Não há renovação automática de token.

O volume `keycloakdata` preserva usuários e configurações. A importação inicial não atualiza um realm já existente. Consulte [identidade e migração](docs/08-identity-and-profiles.md).

## Roteiro visual

1. Entre como consulta1 e investigue erros HTTP 500 na API de pedidos. Veja somente fontes nível 1.
2. Como consulta2, habilite métricas: a API chama `get_service_metrics` por MCP stdio.
3. Em **Observabilidade**, consulte `get_ai_quality_metrics`: contadores reais do backend, sem dados inventados de custo/qualidade.
4. Como gestor, abra **Conhecimento**, selecione um documento, edite e salve. A reindexação atualiza conteúdo e classificação.
5. Crie um documento nível 2. Ele não aparece nem na biblioteca, leitura direta ou contexto RAG de consulta1.
6. Abra **Arquitetura**, selecione um fluxo e clique nos componentes. O mapa é explicativo; não representa tracing ao vivo.

## Modelos e persistência

Backend FastAPI/Python, frontend React/TypeScript, adaptadores LangChain, MCP Python SDK **v1**, PostgreSQL + pgvector opcional.

Para Ollama no host:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

Configure `PROVIDER=ollama`, `STORE=postgres` em `.env`. Se usar AUTH_MODE=demo com um provedor real, substitua os tokens públicos por valores aleatórios. No modo OIDC não são usados tokens estáticos.

```bash
docker compose --profile vector up -d --wait db
docker compose --profile vector up --build backend frontend
```

Para combinar SSO, inclua `-f compose.yaml -f compose.oidc.yaml` nos dois comandos. `.env.example` aponta Ollama para `http://host.docker.internal:11434`. Em Linux, valide o acesso da rede Docker ao host sem expor Ollama à internet. Se executar o backend no host, use `http://localhost:11434`.

API corporativa: configure `PROVIDER=openai-compatible`, `API_BASE_URL`, `API_KEY`, `CHAT_MODEL`, `EMBEDDING_MODEL`. Exige contratos compatíveis de Chat Completions e Embeddings. Provedores com protocolos/autenticação diferentes precisam de adaptador. Ingestão e consultas podem enviar dados ao provedor: política de dados vem antes da conexão.

## Atualização de quem já usou v0.1

```powershell
git pull --ff-only
```

Preserve seu `.env`. Para os três tokens demo, atualize **somente** AUTH_TOKENS conforme `.env.example` e adicione AUTH_MODE=demo. Ou use o overlay Keycloak, que ativa OIDC sem depender de tokens demo. Os grupos antigos employees/operations são aceitos somente no modo demo como aliases para consulta1/consulta2; `demo-ops` agora não edita documentos.

A v0.2 usa namespace `acl-v2`: vetores antigos não são reaproveitados com novas permissões. Documentos próprios da v0.1 devem ser exportados e reingeridos com classificação explícita. O corpus sintético é criado no namespace novo. Edições da v0.2 não são sobrescritas pelo seed no startup. Memória continua volátil; use PostgreSQL para persistência.

## Desenvolvimento e verificação

Python 3.11+ e Node 22.12+. A partir da raiz:

```bash
python -m venv .venv
# Ative .venv para seu sistema operacional.
pip install -r backend/requirements.lock
pip install --no-deps -e ./backend
uvicorn workbench.main:app --host 127.0.0.1 --port 8000
```

Outro terminal: `cd frontend`, `npm ci`, `npm run dev` → http://localhost:5173. O Vite encaminha a API. Para desenvolvimento no host com OIDC, configure JWKS para localhost:8180, não o hostname interno keycloak.

```bash
python -m pytest backend/tests -q
cd frontend
npm run build
# Com o Compose em execução e Chromium Playwright instalado:
npm run test:e2e
# Para testes de login Keycloak, defina AUTH_TEST_MODE=oidc antes do comando.
```

[GitHub Actions](https://github.com/Antonicci/enterprise-ai-workbench/actions) executa testes, PostgreSQL, builds, Compose e testes de navegador com os três perfis em demo e OIDC. Consulte [evidências e limites](docs/07-validation.md); configurar uma verificação não equivale a obter aprovação.

## Documentação corporativa

- [Discovery e escopo](docs/01-discovery-and-scope.md)
- [Escolha de técnicas](docs/02-solution-selection.md)
- [Arquitetura](docs/03-architecture.md)
- [Segurança](docs/04-security.md)
- [Implantação passo a passo](docs/05-implementation-guide.md)
- [Avaliação e operação](docs/06-evaluation-and-operations.md)
- [Identidade, perfis e Entra ID](docs/08-identity-and-profiles.md)
- [Decisões](docs/adr/0002-identity-and-authorization.md) e [roadmap](ROADMAP.md)

## Limites

Sem multitenancy, RLS, exclusão documental, auditoria durável, ingestão assíncrona, quotas ou SLA. OIDC não transforma esse laboratório em ambiente de produção. PostgreSQL usa busca exata e credenciais LAB. O MCP é um worker local confiável, não um servidor remoto autenticado multiusuário. Custo/qualidade de modelo e MLOps preditivo não foram implementados. Timeout não garante cancelamento de trabalho síncrono em andamento. Nunca versionar segredos ou dados reais de clientes.
