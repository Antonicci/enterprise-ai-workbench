# Validação — v0.2

## Testes previstos e executados

- API: perfis, leitura/listagem filtrada, edição e reclassificação, acesso negado antes das ferramentas, erros e limites.
- OIDC: JWKS local com assinatura RSA real; audiência, emissor, expiração, algoritmo e ausência de fallback demo. Mapeamento configurável de roles estilo Entra.
- MCP: handshake, descoberta e ferramentas em subprocesso; identidade OIDC revalidada no worker; métricas medidas separadas de fixtures.
- PostgreSQL: filtro e substituição de documentos/vetores.
- Frontend: TypeScript/Vite; Playwright com três perfis, edição, dois tipos de métricas, mapa interativo e viewport móvel.
- Compose: build, Nginx, API, RAG e MCP. Cenário adicional com Keycloak e login de navegador por Authorization Code + PKCE.

Resultado local: **20 testes passando e 1 integração PostgreSQL ignorada**, além do build TypeScript/Vite aprovado. A suite de backend e build são executados localmente. Docker/navegador local continuam indisponíveis neste ambiente; os cenários de contêiner/SSO/navegador são executados por GitHub Actions. O resultado da execução associada ao commit precisa ser consultado antes de declarar aprovação.

## Não validado por esses testes

Qualidade de um LLM real, execução Ollama/GPU, custo, carga, segurança corporativa completa e integração com tenant Entra real. Contratos de provedores são simulados. Keycloak local usa dados sintéticos e contas públicas. Testes não garantem resistência universal a prompt injection.

## Histórico

v0.1: [workflow aprovado](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44102828104), 13 testes, PostgreSQL, frontend e Compose RAG/MCP. Esse resultado histórico não comprova aprovação automática da v0.2.

## Resultado v0.2 no GitHub Actions

[Execução aprovada 44146912525](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44146912525), código do commit 6724b99d99d54cb8dad1f3aa31523f97f8fdc95e:

- Backend com PostgreSQL/pgvector: **21 testes aprovados**.
- Frontend: instalação e build aprovados.
- Compose demo: build, consulta RAG/MCP e **3 testes de navegador aprovados**.
- Compose OIDC: Keycloak real, Authorization Code + PKCE e **3 testes de navegador aprovados**, usando gestor, consulta1 e consulta2.

Os cenários de navegador incluem consulta com fontes, bloqueio de ferramentas por perfil, inclusão/edição/reclassificação, contadores medidos por MCP e mapa de arquitetura em viewport móvel. O primeiro teste SSO identificou a ausência de sub no token; o cliente Keycloak foi corrigido com o escopo basic, preservando a validação obrigatória no backend. Logs Nginx omitem query strings para não registrar códigos do callback.

## Camada pública e sessão protegida

[Execução aprovada 44153576669](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44153576669), código a90d6d463f3771bceaf27665763810a9832dfbda:

- **25 testes de backend** aprovados, incluindo os endpoints de leitura de negócio sem login.
- Build frontend aprovado.
- **6 testes de navegador em demo e 6 com Keycloak** aprovados.
- Cenários novos: camada pública sem controles do workspace, /workspace redirecionando ao IdP, header com usuário/perfil/permissões, logout e limpeza da interface após HTTP 401. O acesso direto às APIs sem token continua retornando 401.

A UI não implementa revogação imediata de JWT no servidor. Sessões em memória e validade dos tokens seguem as limitações descritas no guia de identidade.
