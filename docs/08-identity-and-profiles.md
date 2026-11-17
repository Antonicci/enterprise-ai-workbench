# Identidade, perfis e permissões — v0.2

## Autenticar e autorizar são etapas distintas

Keycloak ou Entra ID autenticam o usuário. O backend valida o access token e deriva permissões dos perfis reconhecidos. Campos da pergunta, corpo HTTP e interface não concedem acesso. Em modo OIDC, token demo nunca é fallback.

| Perfil / role | Documentos permitidos | Permissões |
|---|---|---|
| knowledge-manager | level1 e level2 | documents:search, documents:write |
| query-l1 | level1 | documents:search |
| query-l2 | level1 e level2 | documents:search, metrics:read, ai-metrics:read |

Não há administração de identidades dentro do Workbench. O administrador do IdP atribui os perfis. Múltiplas roles acumulam permissões. Para a demonstração, atribua exatamente uma a cada usuário.

## Keycloak local

Overlay `compose.oidc.yaml`, realm `workbench`, SPA pública `workbench-web`, API `workbench-api`. Importa três usuários. Direct Access Grants e fluxo implícito estão desabilitados. PKCE S256 é obrigatório na SPA. Não existe client secret no frontend.

O navegador usa emissor público `http://localhost:8180/realms/workbench`. No contêiner, o backend busca JWKS no endereço interno `http://keycloak:8080/realms/workbench/protocol/openid-connect/certs` e continua validando o emissor público exato. URL de chaves vem da configuração, nunca do token recebido. Algoritmo aceito: RS256. Campos obrigatórios: exp, iat, sub, iss e aud. O client scope basic é obrigatório para fornecer sub no access token nas versões atuais do Keycloak. O client mapper adiciona a audiência da API somente ao access token.

O frontend utiliza oidc-client-ts com tokens em memória. Estado transitório/PKCE em sessionStorage, removido ao consumir o callback. Sem renovação automática nesta versão; tokens expiram em 5 minutos no realm de laboratório. Reentrar obtém nova sessão/token. Logout redireciona ao IdP. JWT já emitido pode permanecer válido até expirar; não há revogação imediata via introspecção.

A CSP do laboratório permite conexões HTTPS a IdPs configuráveis e localhost:8180. Na empresa, substitua a regra ampla por hosts específicos.

## Ferramentas

`search_documents` exige documents:search. `get_service_metrics` exige metrics:read e serviço na allowlist orders-api/payments-api. `get_ai_quality_metrics` exige ai-metrics:read. A política é aplicada na API e no worker MCP.

O worker stdio pertence ao mesmo backend e revalida a identidade para a mesma audiência. Recebe o access token por ambiente isolado do processo, não por argumento de ferramenta ou prompt. Não recebe chave do provedor de IA ou DSN do banco para consultas de métricas. Isso não implementa autenticação MCP remota: para outro serviço, usar credencial destinada àquele recurso ou delegação apropriada, nunca encaminhamento genérico de tokens.

Os três perfis atuais não restringem métricas por equipe/serviço além da allowlist global. Uma implantação com múltiplas equipes exige política de recurso e tenant.

## Microsoft Entra ID como alternativa

Integração OIDC configurável; não testada com um tenant real nesta etapa.

1. Registrar SPA e API separadas no tenant específico.
2. Registrar callback `/auth/callback` e logout para a origem escolhida.
3. Expor um escopo delegado da API e consentir a SPA; solicitar esse escopo em OIDC_SCOPE junto de openid/profile.
4. Criar app roles da API com os nomes knowledge-manager, query-l1 e query-l2 e atribuir usuários/grupos.
5. Configurar OIDC_ISSUER com o emissor exato do tenant/v2, OIDC_JWKS_URL com o jwks_uri oficial, OIDC_AUDIENCE conforme o access token destinado à API, OIDC_CLIENT_ID com o ID da SPA e OIDC_ROLES_CLAIM=roles.
6. Validar tokens emitidos para a API e rejeitar tokens de Graph, da SPA ou de outro tenant. Não usar common como limite de confiança.
7. Executar matriz positiva/negativa antes de dados reais. MFA, acesso condicional e política de sessão são controles do tenant, não recursos implementados pelo Workbench.

Não existe botão que converta automaticamente uma instalação Keycloak em Entra ID; são registros e configuração diferentes usando uma fronteira OIDC comum.

## Atualização e persistência

O volume Keycloak preserva o realm; --import-realm não substitui um realm existente. Alterações de roles/usuários podem ser feitas no console administrativo. Para recriar apenas o realm, faça backup, pare e remova apenas o volume Keycloak necessário; nunca apagar todos os volumes para atualizar identidades, pois o volume PostgreSQL pode conter documentos.

No banco de conhecimento, acl-v2 evita que os grupos antigos sejam interpretados com a política nova. Não há migração silenciosa de documentos particulares; reingerir com nível explícito. O seed da v0.2 apenas cria documentos ausentes e preserva edições.

## Camada pública e header de sessão

`/` é uma apresentação pública do projeto, com documentação pública e entrada. Não renderiza controles de investigação, biblioteca, métricas ou arquitetura interativa antes do login. `/workspace` requer `/api/config` validado antes de renderizar qualquer conteúdo; sem sessão OIDC, redireciona ao IdP. No modo demo, apresenta o formulário de credencial local.

O header protegido exibe usuário, perfil, permissões e Sair. Expiração do access token e respostas HTTP 401 limpam fontes, documentos, métricas e dados da sessão, antes de nova autenticação. Erros de autorização 403 mantêm a identidade e não são contornados. Falha na validação inicial permanece na camada pública com erro, evitando loops de redirecionamento. O frontend não substitui os controles da API.
