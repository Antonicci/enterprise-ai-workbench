# Segurança — v0.2

## Implementado

- OIDC Authorization Code + PKCE no navegador; access token validado por RS256/JWKS, emissor, audiência, expiração e campos obrigatórios no backend.
- Emissor/JWKS configurados pelo administrador; nenhum endereço de descoberta é aceito do token ou usuário.
- Modo demo separado. OIDC não aceita credenciais demo como fallback.
- Perfis server-side; permissão específica por ferramenta; política revalidada no worker stdio.
- Níveis documentais filtrados na listagem, leitura direta, recuperação e contexto. Documento restrito não é enviado ao modelo de usuário nível 1.
- Escrita/classificação apenas pelo gestor; métricas apenas por nível 2. UI não é fronteira de autorização.
- Chaves de IA e DSN não são enviados ao worker de métricas, frontend ou prompt.
- SQL parametrizado; documento/chunks atualizados em transação PostgreSQL; namespace acl-v2.
- UI renderiza texto com escape; sem HTML de respostas. Credenciais/tokens em memória; estado transitório de PKCE em sessionStorage.
- Perguntas e documentos com limites de tamanho; Nginx limita corpo a 256 KB. Portas Compose só em loopback, banco não publicado.
- Logs sem perguntas, conteúdo ou tokens. Sujeito, trace, contagens e duração são registrados; não há auditoria imutável.

## Ameaças e limites

| Ameaça | Controle | Risco residual |
|---|---|---|
| Token de outro sistema/tenant | Assinatura, emissor e audiência exatos | Revogação não é imediata; JWT válido até expirar |
| Escalada por parâmetros | Roles resolvidas no servidor e níveis enumerados | Admin do IdP ainda pode atribuir múltiplas roles |
| Documento restrito exposto | Filtros em todas as APIs e contexto | Banco sem RLS; operador de banco lê dados |
| Prompt injection | Modelo sem ferramentas e instruções explícitas | Pode gerar conteúdo incorreto; não há filtro infalível |
| Token passthrough remoto | Worker local de mesma aplicação, audiência igual | Transporte remoto exige projeto próprio de OAuth/delegação |
| Negação de serviço/custo | Limites textuais e timeout | Sem quotas/fila/concurrency budget; thread pode continuar |
| Exfiltração via provedor | Provedor configurado e contexto filtrado | Aprovação de dados, egress, retenção e contratos necessários |

Keycloak local usa HTTP/start-dev, contas públicas e armazenamento de laboratório. Não é configuração corporativa. A CSP permite HTTPS para IdPs configuráveis; produção deve restringir os hosts. A v0.2 não oferece multi-tenant, RLS, MFA próprio, auditoria durável, rotação ou alta disponibilidade.

## Antes de dados reais

Classificar fontes e finalidade, aprovar provedor/egress, configurar TLS/IdP corporativo, rotação e identidades de serviço mínimas. Aplicar tenant independente de perfil, RLS, quotas, exclusão/retencão de texto/vetores/backups e auditoria durável. Validar matriz de acessos e tentativas de injection. Qualquer ação de escrita em sistemas externos exige autorização, aprovação específica e idempotência.

[Configuração de identidade, perfis e Entra ID](08-identity-and-profiles.md).

## Dependências de build

Na instalação validada em 17/11/2026, npm audit reportou um ReDoS em picomatch (transitivo de ferramentas de build), sem versão corrigida publicada no registro consultado (latest 4.0.7). O contêiner entregue ao usuário serve arquivos estáticos por Nginx e não contém Vite/Node em runtime. Não expor o servidor de desenvolvimento nem aceitar padrões glob de usuários. Acompanhar a correção e atualizar o lock quando disponível; não tratar o build aprovado como ausência de vulnerabilidades.
