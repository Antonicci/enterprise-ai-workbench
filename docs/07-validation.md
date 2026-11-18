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

## Comparação determinística e retenção de contradições conhecidas

[Execução aprovada 44209285279](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44209285279), código 6cb03166b1697c5cddacfa314eb7cd23971ff2db:

- **52 testes de backend** aprovados, incluindo PostgreSQL, limites decimais, janela incompatível, regras conflitantes, ausência de fonte autorizada e retenção do rascunho incorreto observado no laboratório.
- Build frontend e **9 testes de navegador por modo** (18 no total), demo e OIDC, aprovados. A regressão de UI usa resposta interceptada para verificar o aviso de retenção; a regressão do backend injeta o rascunho contraditório para exercitar a proteção real.
- **Qwen2.5 3B real em CPU** aprovado: comparação retornou `4.8 > 2`, diferença de `2.8` pontos percentuais e condição de investigação atendida. O rascunho desta execução reconheceu corretamente que a medição está acima do limiar; a proteção retornou `no_known_conflict`.

A revisão manual ainda identificou atribuição genérica do cálculo à “ferramenta” no texto do modelo. A comparação é executada pelo backend, não pelo servidor MCP. O bloco independente da interface informa essa origem. Não tratamos esse resultado como validação semântica completa nem benchmark da GPU do autor. Os valores operacionais continuam sintéticos. Veja [escopo e limites do cálculo](11-deterministic-numeric-checks.md).


## Apresentação da resposta e instruções de fidelidade

[Execução aprovada 44327394589](https://github.com/Antonicci/enterprise-ai-workbench/actions/runs/44327394589), código 90712ecc9fabcc842277176d8936187f98d02b7b:

- **61 testes backend**, build frontend e **18 testes de navegador** (9 demo, 9 OIDC) aprovados.
- Novas regressões verificam remoção de cerca externa de Markdown, preservação de código e cercas incompletas e normalização no adaptador real com modelo simulado.
- Smoke com Qwen2.5 3B real em CPU aprovado. Na saída revisada, o modelo usou texto Markdown direto, citou a medição de 4,8% e distinguiu o limiar de 2%. Não repetiu as alegações de remoção de senhas nem de proibição geral de intervenções.

O smoke é evidência de uma execução, não prova de fidelidade geral. As instruções de conteúdo não são um novo bloqueio semântico. A resposta ainda pode omitir verificações úteis ou produzir afirmações sem apoio; compare com as fontes. A duração em CPU deste job não representa benchmark do host do autor.
