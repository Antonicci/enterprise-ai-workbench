# Governança e operação — v0.4

Este laboratório usa os seis pilares do [AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html) como referência de revisão, sem alegar certificação, auditoria formal ou prontidão para produção. A tela Governança é autenticada e apresenta controles e lacunas. Operação e diagnóstico de modelos continuam restritos a query-l2; conhecer a política não concede permissão operacional.

## Controles implementados

| Controle | Aplicação e limite |
|---|---|
| Identidade e perfis | Validação JWT/OIDC, permissões documentais e ferramentas no servidor. Modo demo não ativa OIDC. |
| Admissão | REQUESTS_PER_MINUTE=30 por subject verificado em janela móvel de 60 s; MAX_CONCURRENT_REQUESTS=2 por processo. Excesso retorna 429 + Retry-After antes da recuperação. |
| Contexto de geração | MAX_PROMPT_CHARS=16000 considera sistema, pergunta e JSON de evidências após recuperação. Retorna 413 antes da geração se exceder. Não é contagem exata de tokens e não impede o embedding anterior. Não trunca evidências silenciosamente. |
| Saída e contexto local | MAX_OUTPUT_TOKENS=512 solicitado ao adaptador. OLLAMA_NUM_CTX=4096 limita contexto do Ollama. Não equivale a quota financeira nem à capacidade de contexto de qualquer API. |
| Timeout | REQUEST_TIMEOUT=60 s na consulta. Trabalho síncrono em thread ou no provedor pode continuar após timeout; a vaga de admissão local é liberada. |
| Comparação numérica | Decimal e proteção limitada documentada no guia específico. Não é validação geral de groundedness. |

São limites de **/api/chat**, por processo, sem contador compartilhado entre workers ou persistência após reinício. Ingestão e endpoints administrativos não recebem essa quota. As credenciais e o conteúdo da pergunta não definem o subject. Histórico de admissão é limitado a 1000 identidades ativas por janela; ao atingir capacidade, novas identidades recebem 429. Rejeições por concorrência não consomem quota por usuário.

Para produção: aplicar controles compartilhados também em ingressos, ingestão, requisições de embedding e tarefas assíncronas. Não usar esse mecanismo como proteção completa contra abuso ou negação de serviço.

## Métricas e denominadores

Operação consulta get_ai_quality_metrics via MCP, usando o snapshot do mesmo backend que processou as consultas. A ferramenta não recria contadores. O nome histórico de quality_metrics não significa que a qualidade da resposta seja avaliada.

- Execuções: consultas admitidas finalizadas com sucesso ou falha de dependência. Taxa de sucesso = concluídas / finalizadas; taxa de erro = falhas / finalizadas.
- Rejeições de política (429 e 413) são contadas separadamente. Falhas de autenticação, autorização e validação do payload não entram nas taxas. Não são taxas HTTP globais nem indicadores de qualidade semântica.
- Latências: média e p95 por nearest rank sobre até 500 execuções, incluindo falhas. Taxas usam o total desde o início do processo.
- Últimas 12 execuções: hora, resultado, duração, etapas concluídas e uso disponível, sem perguntas, respostas ou identificadores de usuário.
- Processo: identificador aleatório, início e coleta UTC. Reinício zera tudo; múltiplos workers podem produzir snapshots diferentes.
- Rascunhos retidos: resposta concluída com relatório determinístico; não é falha de execução.

Sem amostras, as taxas são nulas, não 100% ou 0%. Faça uma investigação e abra Operação; a tela consulta automaticamente ao entrar e oferece atualização manual. Se os contadores estiverem zerados, confira identificador e horário do processo, reinícios e distribuição entre workers antes de concluir falha de instrumentação.

## Tokens e estimativa de custo

O adaptador LangChain retorna uma string com metadados por resposta, sem estado global compartilhado entre consultas. Captura input_tokens/output_tokens de usage_metadata ou contadores Ollama equivalentes. Sem dados completos, retorna null: não estima tokens pelo tamanho do texto.

O painel soma apenas uso informado na geração de respostas concluídas. Inclui rascunho retido quando houve geração. Embeddings, falhas/timeouts e tentativas internas podem consumir recursos não contabilizados. Exibe a quantidade de respostas com uso informado para tornar a cobertura explícita.

Ollama: tokens/s = saída / eval_duration em segundos, quando disponível. Duração de avaliação vem do provedor; não equivale à latência ponta a ponta.

API compatível: para estimativa, configure explicitamente:

```dotenv
PRICE_MODEL=mesmo-valor-de-CHAT_MODEL
INPUT_PRICE_PER_MILLION=1.00
OUTPUT_PRICE_PER_MILLION=2.00
PRICE_CURRENCY=USD
```

Valores acima são **exemplo aritmético, não preços de mercado**. Sem ambos os preços ou se PRICE_MODEL divergir de CHAT_MODEL, não calcula. Fórmula decimal: (entrada × preço de entrada + saída × preço de saída) / 1000000. Não considera descontos, cache, tiers, impostos, câmbio ou cobrança real. Preços dependem de declaração do operador e podem ficar desatualizados. Alteração exige reinício.

Ollama não apresenta custo monetário zero: energia, depreciação e infraestrutura não são medidas. Não há orçamento financeiro bloqueante nem quota acumulada exata de tokens.

## Hardware e escolha do modelo

/api/runtime consulta apenas /api/tags e /api/ps no endpoint Ollama configurado, sem executar comandos no host, baixar pesos ou alterar o modelo.

Exibe modelo, quantização, parâmetros, tamanho em disco, presença em memória, bytes carregados e bytes em VRAM informados. Valores ausentes permanecem desconhecidos. Bytes em VRAM do modelo **não são a VRAM total ou livre da GPU**. RAM/VRAM total podem ser declaradas via HOST_RAM_GB e HOST_VRAM_GB; a UI rotula essas declarações e não as usa como detecção automática.

O usuário seleciona um modelo instalado para analisar, sem mudar o ativo. Escolha operacional:

1. Comece pelo modelo menor que atenda à tarefa e à qualidade avaliada.
2. Faça consulta representativa, verifique alocação no Ollama e tempos/tokens/s em Operação.
3. Sob pressão de memória, avalie menor modelo, menor contexto ou concorrência. Tamanho em disco sozinho não comprova que cabe em VRAM.
4. Para promover outro modelo, configure CHAT_MODEL e reinicie; valide qualidade, latência e memória novamente. Memória depende de pesos, quantização, KV cache e outras cargas.
5. Não trate a presença de GPU ou um valor de capacidade declarado como benchmark.

Não há roteamento automático por VRAM. Provedores de API não revelam hardware local por esse diagnóstico. Falha do diagnóstico apresenta estado indisponível, sem expor endereço interno ou credenciais.

## Pilares e lacunas

| Pilar | Evidência atual | Próxima evolução |
|---|---|---|
| Excelência operacional | Contadores, janelas, etapas e regressões | Histórico durável, alertas e telemetria agregada |
| Segurança | OIDC, perfis e ACL | TLS, gestão de segredos, threat model e auditoria durável |
| Confiabilidade | Timeout e admissão | HA, testes de carga, circuit breaker e cancelamento no provedor |
| Performance | Contexto limitado, diagnóstico e tempos | Benchmark de hardware e corpus de avaliação |
| Custos | Uso reportado e estimativa configurada | Contabilização de embeddings, orçamento e conciliação |
| Sustentabilidade | Limites de processamento | Energia medida e avaliação de eficiência por tarefa |

## Referências técnicas

- [LangChain UsageMetadata](https://reference.langchain.com/python/langchain-core/messages/ai/UsageMetadata)
- [Ollama uso e durações](https://docs.ollama.com/api/usage)
- [Ollama modelos carregados](https://docs.ollama.com/api/ps)
- [Identidade e perfis](08-identity-and-profiles.md)
- [Comparação numérica](11-deterministic-numeric-checks.md)


## Organização dos pilares na interface

Os pilares usam identidades visuais distintas: azul (operação), roxo (segurança), verde-azulado (confiabilidade), âmbar (performance), coral (custos) e verde (sustentabilidade). Cor identifica o tema, não o nível de conformidade. Nome, número e estado textual continuam visíveis.

Os seis limites de processamento aparecem em **Políticas aplicadas no backend**, dentro de Performance. O agrupamento organiza a consulta, mas timeout e admissão também apoiam Confiabilidade e Segurança. A seção expansível de escopo preserva essa distinção e os limites de aplicação por processo.

Permissões da sessão estão em Segurança; preços para estimativa, em Custos. O diagnóstico de modelos permanece em bloco próprio. Tanto a visão usual quanto a compacta usam o mesmo componente de pilar e os valores retornados pela API.

A apresentação está dividida em Governance.tsx (coleta e composição), GovernancePillar.tsx (cartões e políticas) e governance.types.ts (contratos TypeScript). Resumos e cores são associados pelo nome do pilar, evitando dependência da ordem do array. A API continua sendo a origem dos estados e valores efetivos; a interface não concede permissões.


## Guias de referência expansíveis

Cada pilar inclui **Referência e evolução**: lacunas atuais, responsável sugerido, cobertura das métricas, condições de acionamento propostas, práticas e validação. A interface associa a configuração atual do modelo ao desenho P1/P2, sem ativar uma segunda rota.

O catálogo também cobre circuit breaker, retries limitados, backpressure, quotas compartilhadas, autoscaling, reserva de orçamento, segurança de cache e energia por tarefa útil. Números são exemplos, não configuração efetiva. [Escopo, fluxo e referências primárias](13-governance-reference-playbooks.md).
