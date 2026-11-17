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

## v0.3 — Ollama real e evidências visuais

[Execução aprovada 44178793520](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44178793520), código c6c4478649c1fb7114999d8fbdac0ff54ab35388:

- **26 testes de backend** aprovados, incluindo PostgreSQL e distinção entre duração medida e etapa MCP não solicitada.
- Build frontend aprovado e **7 testes de navegador em cada modo**, demo e OIDC (14 no total), incluindo modo apresentação e fontes.
- **Ollama real em CPU aprovado**, com qwen2.5:0.5b e nomic-embed-text: geração, embeddings, recuperação e MCP executados. A ferramenta de serviço segue retornando dados sintéticos.

Esse smoke verifica o caminho executável; não avalia a qualidade das respostas. Não é benchmark do modelo 3B nem da RTX 4050 do autor. A configuração de GPU está preparada, mas precisa de validação no host. A tag da imagem Ollama é mutável; o job registra versão e inventário. Não foi verificada ausência total de egress, nem inicialização offline. O provisionador de modelos consulta o registro quando executa pull, mesmo se os pesos já estiverem em cache.

## Escopo e proveniência — regressão do caso HTTP 500

[Execução aprovada 44185276003](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44185276003), código 5b893191402800fca06c51d13a16ad77f0cbd54d:

- **31 testes de backend** aprovados, incluindo filtro de escopo/acesso antes do ranking e migração de dados editados no PostgreSQL.
- Build frontend e **8 testes de navegador em cada modo** (16 no total) aprovados.
- **Qwen2.5 3B real em CPU**: recuperação de duas fontes, sem runbook de pagamentos; geração e MCP concluídos. Na revisão manual dessa saída, o modelo distinguiu o limiar de 2%, citou a ferramenta e incluiu pool de conexões/timeouts.

A abertura da resposta ainda utilizou uma formulação genérica baseada nos documentos antes de mencionar a observação. Não tratamos uma execução como prova de atribuição perfeita: a interface mostra as medições diretamente com origem MCP, e o texto gerado continua exigindo revisão.

A primeira tentativa do job OIDC falhou no download de imagem Docker com connection reset by peer, antes de subir a aplicação. Apenas o job com falha foi repetido; a tentativa seguinte passou.
