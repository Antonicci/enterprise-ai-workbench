# Implementação corporativa passo a passo — v0.2

1. **Discovery:** definir tarefa, personas, fontes, classificação, resultado esperado, orçamento e risco da resposta errada. Usar a matriz de técnicas antes de assumir que LLM é necessário.
2. **Demo:** executar README, consultar como nível 1 e nível 2, editar como gestor. Testar negações por chamadas diretas, não apenas botões desabilitados.
3. **Identidade:** ativar overlay Keycloak para laboratório. No piloto corporativo registrar SPA/API no IdP, configurar emissor/audiência/JWKS e atribuir perfis. Executar a matriz de acesso com tokens válidos, inválidos, expirados e de outra audiência.
4. **Dados:** usar nível 1/2 explicitamente. O gestor inclui, abre, edita, classifica e reindexa. Para fontes corporativas, adicionar proveniência, atualização incremental, exclusão e mapeamento das permissões originais.
5. **Modelos:** escolher Ollama local ou endpoint compatível aprovado. Testar chat e embeddings com o corpus. Não há fallback silencioso. Modelo local não prova ausência de egress.
6. **Persistência:** iniciar banco antes do backend; namespace novo ao mudar embedding/política. Memória é só laboratório. Dados v0.1 devem ser reingeridos com classificação.
7. **Ferramentas:** conceder permissão por ação e recurso. Nesta versão, nível 2 acessa a allowlist global. Novos serviços/equipes exigem política de recurso; ferramenta de escrita exige aprovação e identidade de destino mínima.
8. **Avaliação:** medir fontes recuperadas, groundedness, abstinência, acesso, latência e custo instrumentado. Snapshot operacional não substitui avaliação de qualidade.
9. **Piloto:** grupo pequeno, quotas, auditoria durável, TLS, egress limitado, backups, exclusão e responsáveis. Não publicar o Compose de laboratório na internet.

## Configuração

| Variável | Propósito |
|---|---|
| AUTH_MODE | demo ou oidc; sem fallback entre os modos |
| AUTH_TOKENS | Mapa de tokens locais → roles, usado apenas no modo demo |
| OIDC_ISSUER | Emissor exato validado e autoridade pública usada pela SPA |
| OIDC_JWKS_URL | URL confiável das chaves, pode usar rede interna |
| OIDC_AUDIENCE | Audiência da API, distinta da SPA |
| OIDC_CLIENT_ID / OIDC_SCOPE | Registro da SPA e escopos pedidos |
| OIDC_ROLES_CLAIM | realm_access.roles no Keycloak; roles no exemplo Entra |
| PROVIDER / STORE | demo, ollama ou openai-compatible; memory ou postgres |
| CHAT_MODEL / EMBEDDING_MODEL | Identificadores dos modelos |
| API_BASE_URL / API_KEY | Provedor compatível aprovado |
| OLLAMA_BASE_URL / DATABASE_URL | Endereços acessíveis no ambiente de execução |
| TOP_K / REQUEST_TIMEOUT | Limites de recuperação e prazo do fluxo |

## Troubleshooting

- 401: token inválido/expirado, audiência/emissor incorretos ou JWKS inacessível. Token demo é recusado em OIDC.
- 403: perfil não atribuído ou permissão insuficiente. Gestor não consulta métricas; nível 2 não edita.
- 404 documental: documento inexistente ou fora do nível permitido.
- Callback rejeitado: usar localhost:8080 ou localhost:5173; registrar exatamente /auth/callback no IdP.
- Interface perdeu sessão após reload: tokens ficam em memória; clique Entrar com SSO novamente.
- Realm não mudou após atualizar JSON: volume já contém realm, importação não substitui; administrar ou recriar apenas o armazenamento de identidade após backup.
- 503: dependência indisponível; usar trace e logs locais sem publicar tokens. No startup, embeddings e banco precisam estar disponíveis no modo real.
- Documento antigo não aparece: namespace acl-v2; reingerir com classificação. Não mapear permissões antigas silenciosamente.
