# Avaliação e operação — v0.2

## O que medir

| Dimensão | Método | Critério inicial proposto, ainda não validado |
|---|---|---|
| Recuperação | Recall@k sobre fonte esperada | ≥ 90% num conjunto curado relevante |
| Fundamentação | Revisão de afirmações versus evidências | ≥ 95% das afirmações verificáveis sustentadas |
| Abstinência | Perguntas sem fonte autorizada | Não inventar fonte ou causa |
| Segurança | Tentativas entre grupos, ferramentas e injeções | Zero vazamento de documento restrito no conjunto de testes |
| Desempenho | p50/p95, cold start e concorrência | Definir após benchmark do hardware/provedor |
| Custo | Tokens, embeddings, GPU/banco por consulta | Orçamento e teto definidos pelo piloto |
| Negócio | Tempo de investigação e utilidade revisada | Comparar com baseline humano sem assistente |

Números acima são metas de desenho, não resultados deste projeto. Similaridade vetorial não é confiança ou probabilidade de a resposta estar correta.

## Conjunto de avaliação

Começar com perguntas sobre pedidos, pagamentos, ações que exigem aprovação e perguntas sem resposta. Incluir sinônimos, português informal, documentos contraditórios, fontes desatualizadas e tentativas de obter OPS-RESTRICTED-7391 como analyst. Para geração real, rodar também instruções maliciosas em documentos e perguntas. Evitar que um único LLM seja o único juiz: combinar verificações determinísticas e revisão humana.

## Rastreabilidade atual

Resposta inclui trace_id, elapsed_ms, provider, citations e tool_calls. Logs de aplicação incluem sujeito pseudonimizado, contagens e duração. As métricas MCP incluem serviço, janela e observed_at; os valores são fixtures sintéticas, não uma leitura de infraestrutura.

A v0.2 adiciona dashboard e get_ai_quality_metrics com contadores reais por processo: consultas, falhas de execução, fontes, chamadas de ferramenta e média/p95 das últimas 500 latências. Tokens, custo, groundedness e recall são explicitamente não medidos. Ainda faltam OpenTelemetry, uso/custo de tokens, auditoria persistente e alertas. Um trace ID sozinho não comprova auditabilidade de ponta a ponta.

## Disponibilidade e falhas

Sem fonte, o assistente informa a lacuna. Falha de dependência gera 503; não há resposta de fallback inventada. Timeout do fluxo não garante cancelamento de operações síncronas. O piloto exige concorrência limitada, fila e budgets separados de chat/embedding. Não expor o laboratório publicamente sem esses controles.

## Retenção e lifecycle

O corpus empacotado é sintético e indexado apenas se ausente ao iniciar. Em memória, novas ingestões se perdem. PostgreSQL persiste em volume Compose; apagar o volume remove o corpus armazenado. A v0.1 não tem API de exclusão, revisão de versões ou política de retenção. Dados reais exigem esses mecanismos, inclusive remoção dos vetores derivados e tratamento de backups.

## Extensão de monitoramento com ML

Criar série sintética versionada e baseline de regra. Adicionar detector só quando melhorar precisão/recall ou tempo de detecção. O detector entrega score, versão e intervalo; MCP retorna esse resultado. RAG recupera o runbook; o LLM explica evidências. A ferramenta não transforma correlação em causa raiz.

Atribuição de fontes e escopo agora têm testes de regressão e contexto tipado: [detalhes](10-source-attribution-and-scope.md). Isso não equivale a uma avaliação semântica automática de todas as respostas do modelo.
