# Demonstração visual — Enterprise AI Workbench LAB 03

## Objetivo

Mostrar, em cerca de 90 segundos, como identidade, autorização, recuperação documental, MCP e geração local se conectam. Público: arquitetos, líderes técnicos e equipes que avaliam IA corporativa. Use somente o corpus e os usuários sintéticos do laboratório.

Mensagem central: **uma resposta de IA precisa de contexto autorizado, origem visível e limites explícitos.**

## Preparação da gravação

- Abra a apresentação pública e o workspace em janelas separadas. Prepare sessões isoladas de consulta1 e consulta2 em perfis de navegador distintos para não misturar identidades.
- Use 1920 × 1080, zoom que mantenha os textos legíveis e o modo apresentação da aplicação. Recolha os trechos longos; abra apenas o que estiver narrando.
- Faça uma consulta de preparação para carregar o modelo. Na consulta gravada, preserve os tempos reais mostrados na interface.
- Confirme que consulta1 só recebe fontes nível 1 e não acessa métricas. Se a classificação do corpus foi alterada, restaure um cenário sintético conhecido antes de gravar.
- Em consulta2, use a pergunta “Como investigar erros HTTP 500 na API de pedidos?”, escopo automático e MCP para orders-api.
- A implementação atual usa memória no cenário mostrado pelo autor: não apresente esse cenário como PostgreSQL persistente. Se mudar a configuração, confira o indicador antes de narrar.
- Não grave campos de senha, tokens ou o callback OIDC. Mostre o usuário já autenticado; um corte entre as sessões é suficiente.

## Roteiro de 90 segundos

| Tempo | Tela e ação | Narração sugerida | Texto curto sobreposto |
|---|---|---|---|
| 0–8 s | Apresentação pública ou mapa de arquitetura. | “Construí um laboratório de IA corporativa para explorar identidade, documentos autorizados e ferramentas com origem visível.” | Enterprise AI Workbench · LAB |
| 8–20 s | Workspace consulta1; destaque perfil e permissões. Mostre resultado previamente concluído e fontes nível 1. | “O acesso usa SSO com Keycloak. Este perfil consulta apenas documentos nível 1 e não pode acessar as métricas.” | Identidade + autorização |
| 20–32 s | Corte para consulta2. Mostre o perfil, a pergunta e a opção MCP. Clique Investigar. | “Com consulta nível 2, posso recuperar fontes restritas autorizadas e consultar métricas do serviço via MCP.” | RAG com filtro de acesso |
| 32–40 s | Mostre alguns segundos de processamento; corte para o resultado. | “A geração roda localmente com Ollama. Cortei a espera neste vídeo; o tempo medido permanece na tela.” | Corte de espera · duração real na interface |
| 40–57 s | Destaque o bloco FONTE MCP e depois a comparação determinística. | “As métricas são sintéticas. O MCP retorna 4,8% de erros em cinco minutos. O runbook define 2%. O backend compara os valores e mostra que o critério de investigação foi atingido.” | Documento + medição → cálculo do backend |
| 57–70 s | Resposta e trecho do runbook aberto. | “O modelo organiza a orientação. As fontes permitem conferir as afirmações, mas não garantem que toda a resposta esteja correta.” | Fontes para revisão humana |
| 70–82 s | Etapas medidas e mapa de componentes. | “A aplicação separa os tempos de recuperação, ferramenta e geração. O mapa explica os componentes; não é um tracing ao vivo.” | RAG · MCP · LLM · tempos medidos |
| 82–90 s | Mapa ou apresentação pública; nome do projeto e endereço do repositório na edição. | “Código e decisões estão públicos. É um laboratório para estudar implementação e trade-offs, com limites documentados.” | Código + arquitetura no GitHub |

Os intervalos são de edição, não tempos de resposta esperados. Se não cortar a espera, amplie a duração do vídeo. Não acelere a interface de forma que pareça haver resposta instantânea.

## Três capturas para um post sem vídeo

1. **Identidade e acesso:** header de consulta1, permissões e fontes nível 1. Legenda: “O perfil delimita o contexto antes da geração.”
2. **Investigação com evidências:** consulta2, origem MCP e comparação 4,8% > 2%. Legenda: “Documento, medição e cálculo têm responsabilidades distintas.”
3. **Arquitetura explicável:** mapa de componentes com o caminho da consulta. Legenda: “As decisões e os limites fazem parte da entrega.”

Não monte uma imagem com toda a página em tamanho reduzido. Prefira três capturas legíveis. Use apenas resultados de execuções reais do laboratório.

## Texto sugerido para LinkedIn

Tenho desenvolvido o **Enterprise AI Workbench**, um laboratório público de arquitetura de IA corporativa.

No exemplo do vídeo, uma investigação de erros HTTP 500 combina:

- SSO com Keycloak e três perfis de acesso.
- Recuperação de documentos com filtro de autorização antes de fornecer contexto ao modelo.
- Consulta de métricas sintéticas via MCP.
- Geração local com Ollama.
- Comparação numérica no backend, com a regra documental e a medição identificadas.

O caso também trouxe um aprendizado prático: o modelo chegou a interpretar 4,8% como estando dentro de um limiar de 2%. Transformei essa comparação em cálculo determinístico e adicionei regressões e uma proteção limitada para contradições conhecidas.

O modelo continua exigindo revisão. Fontes visíveis ajudam a conferir uma resposta; não comprovam automaticamente todas as suas afirmações.

O projeto é um laboratório, com decisões, testes e limitações documentados.

Código: https://github.com/Antonicci/enterprise-ai-workbench
Arquiteturas: https://chihuahuasstudios.com/architectures/

Como vocês separam geração por modelo, autorização e validações determinísticas nas suas soluções?

#ArquiteturaDeSoluções #InteligenciaArtificial #RAG #MCP #Ollama

## Descrição curta para o portfólio

**Enterprise AI Workbench — IA corporativa com identidade e evidências.** Laboratório que integra SSO, três perfis de autorização, recuperação documental, ferramentas MCP e geração local com Ollama. Inclui comparação numérica determinística e tempos medidos por etapa. Dados operacionais sintéticos; limitações e decisões disponíveis no repositório.

## Afirmações que a demonstração sustenta

| Pode demonstrar | Limite a manter explícito |
|---|---|
| Autenticação OIDC e autorização por perfil | Keycloak local em configuração de laboratório; não equivale a produção |
| Fontes filtradas no backend | Não comprova resistência a todos os ataques ou isolamento multitenant |
| Chamada MCP de métricas | Medições de serviço sintéticas; não é integração com produção |
| Comparação Decimal entre regra reconhecida e medição | Não é um motor universal de políticas nem validação semântica completa |
| Retenção de contradições numéricas reconhecidas | Não elimina todas as alucinações |
| Tempos de etapas medidos | Não são estimativa de custo, confiança ou avaliação completa de qualidade |
| Execução local com Ollama | Não comprova ausência de tráfego externo nem uso de GPU no host |
| Mapa de arquitetura navegável | Diagrama explicativo; não representa execução ao vivo |

## Referências

- [Identidade e perfis](08-identity-and-profiles.md)
- [Escopo e proveniência](10-source-attribution-and-scope.md)
- [Comparação determinística e limites](11-deterministic-numeric-checks.md)
- [Evidências de validação](07-validation.md)
