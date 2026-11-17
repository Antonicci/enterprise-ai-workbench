# ADR 0002 — OIDC e três perfis com autorização por ferramenta

Status: aceito na v0.2.

A v0.1 combinava escrita documental e operação no grupo operations. Isso impede demonstrar separação de responsabilidades e não oferece identidade corporativa.

Decisão: separar knowledge-manager, query-l1 e query-l2. Perfis concedem permissões; documentos são classificados por nível. Backend valida access token OIDC e aplica política. Worker MCP da mesma aplicação revalida o token e a permissão. Manter modo demo explícito, sem fallback no modo OIDC.

Keycloak fornece IdP reproduzível no Compose. oidc-client-ts usa Authorization Code + PKCE e permite configurar autoridade corporativa. Entra ID é alternativa documentada e exige registros próprios de SPA/API, escopos, app roles e validação no tenant.

Consequências: mais infraestrutura local e tokens com expiração; roles acumulam permissões. Não há logout/revogação imediata na API. Worker MCP não é um recurso OAuth remoto. Namespace acl-v2 separa dados antigos e exige reingestão explícita. Não implementar permissões baseadas em nomes de botões nem confiar no modelo para decidir acesso.
