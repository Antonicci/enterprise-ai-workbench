# Validação — v0.2

## Testes previstos e executados

- API: perfis, leitura/listagem filtrada, edição e reclassificação, acesso negado antes das ferramentas, erros e limites.
- OIDC: JWKS local com assinatura RSA real; audiência, emissor, expiração, algoritmo e ausência de fallback demo. Mapeamento configurável de roles estilo Entra.
- MCP: handshake, descoberta e ferramentas em subprocesso; identidade OIDC revalidada no worker; métricas medidas separadas de fixtures.
- PostgreSQL: filtro e substituição de documentos/vetores.
- Frontend: TypeScript/Vite; Playwright com três perfis, edição, dois tipos de métricas, mapa interativo e viewport móvel.
- Compose: build, Nginx, API, RAG e MCP. Cenário adicional com Keycloak e login de navegador por Authorization Code + PKCE.

A suite de backend e build são executados localmente. Docker/navegador local continuam indisponíveis neste ambiente; os cenários de contêiner/SSO/navegador são executados por GitHub Actions. O resultado da execução associada ao commit precisa ser consultado antes de declarar aprovação.

## Não validado por esses testes

Qualidade de um LLM real, execução Ollama/GPU, custo, carga, segurança corporativa completa e integração com tenant Entra real. Contratos de provedores são simulados. Keycloak local usa dados sintéticos e contas públicas. Testes não garantem resistência universal a prompt injection.

## Histórico

v0.1: [workflow aprovado](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44102828104), 13 testes, PostgreSQL, frontend e Compose RAG/MCP. Esse resultado histórico não comprova aprovação automática da v0.2.
