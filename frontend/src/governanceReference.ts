export type ReferenceMetric = {
  name: string;
  coverage: 'Medido' | 'Parcial' | 'Planejado';
  note: string;
};

export type ReferenceTrigger = {
  condition: string;
  action: string;
  recovery: string;
};

export type PillarReferenceData = {
  owner: string;
  metrics: ReferenceMetric[];
  triggers: ReferenceTrigger[];
  practices: string[];
  validation: string[];
  sources: {label: string; url: string}[];
};

// Os limiares deste catálogo são exemplos de desenho, não configuração do backend.
// Não transformar o guia em um painel verde: uma recomendação não é um controle ativo.
export const governanceReference: Record<string, PillarReferenceData> = {
  operations: {
    owner: 'Operação da plataforma + responsável pelo produto',
    metrics: [
      {name: 'Sucesso, falhas e rejeições', coverage: 'Medido', note: 'Operação mede execuções por processo; 413/429 ficam separados. Não é taxa HTTP global nem acurácia.'},
      {name: 'p95 e tempos por etapa', coverage: 'Parcial', note: 'Até 500 amostras, sem janela temporal distribuída. Para alertar em 5 min, persistir série com timestamp e denominador.'},
      {name: 'Qualidade e utilidade', coverage: 'Planejado', note: 'Corpus versionado, revisão de groundedness/recall, abstinência e avaliação humana. Similaridade não é confiança.'},
    ],
    triggers: [
      {condition: 'Exemplo: falhas > 5% em 5 min, com pelo menos 20 execuções.', action: 'Abrir incidente, separar falha de recuperação, MCP e geração; acionar responsável.', recovery: 'Encerrar após janela estável e revisão das causas. Não zerar counters para esconder o incidente.'},
      {condition: 'Exemplo: p95 excede o SLO aprovado por duas janelas consecutivas.', action: 'Comparar etapas, modelo, cold start e saturação antes de escalar.', recovery: 'Confirmar p95 e taxa de sucesso recuperados com volume representativo.'},
    ],
    practices: [
      'Definir SLI, SLO, responsável e runbook por jornada. Sucesso técnico não substitui qualidade da resposta.',
      'Propagar trace entre API, recuperação, modelo e ferramenta. Registrar versão do modelo, política e corpus sem expor prompts, tokens de acesso ou documentos restritos.',
      'Centralizar métricas e logs com retenção, controle de acesso e alertas deduplicados; distinguir tráfego sintético de uso real.',
    ],
    validation: ['Injetar falha em cada dependência e conferir denominador, alerta e responsável.', 'Comparar mudança de modelo ou prompt em corpus curado antes de promover; registrar rollback.'],
    sources: [{label: 'AWS Well-Architected', url: 'https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html'}],
  },
  security: {
    owner: 'Segurança + identidade + responsáveis pelos dados',
    metrics: [
      {name: 'Perfis e permissões', coverage: 'Parcial', note: 'A sessão e os endpoints aplicam permissões; consulta1 não acessa fonte restrita nem métricas.'},
      {name: 'Rejeições 401/403 e auditoria', coverage: 'Planejado', note: 'As taxas operacionais atuais não contam autenticação/autorização. Instrumentar separadamente, sem registrar credenciais.'},
      {name: 'Isolamento e exfiltração', coverage: 'Parcial', note: 'Há testes de ACL; ainda faltam auditoria durável, revisão de egress, segregação de produção e validação ampla de ataques.'},
    ],
    triggers: [
      {condition: 'Qualquer evidência de documento ou ferramenta acessado fora do perfil.', action: 'Interromper o caminho afetado, preservar auditoria e acionar segurança; não tentar contornar via outro modelo.', recovery: 'Corrigir política e invalidar caches; repetir testes negativos antes de liberar.'},
      {condition: 'Exemplo: aumento anormal de 401/403 por identidade/origem em 5 min.', action: 'Investigar expiração, configuração do IdP ou abuso. Rate limit no ingresso, com regra aprovada.', recovery: 'Restaurar acesso válido sem liberar autorização por falha do IdP.'},
    ],
    practices: [
      'Validar assinatura, emissor, audiência e expiração. Usar Keycloak/OIDC com PKCE e TLS em produção; separar perfis de gestão documental e operação.',
      'Aplicar ACL antes do ranking/contexto e em cada ferramenta. Conteúdo recuperado e saída do modelo nunca concedem permissões.',
      'No fallback, preservar classificação, ACL, filtros, região e perímetro contratual. Nunca enviar dados restritos a outro provedor sem aprovação explícita.',
      'Cache deve considerar identidade/escopo, versão do documento e modelo; revogação de acesso e reclassificação exigem invalidação.',
    ],
    validation: ['Testar token expirado, audiência incorreta, rotação de chaves e cada combinação de perfil/ferramenta.', 'Executar testes de prompt injection e tentativa de exfiltração com corpus sintético e revisão humana.'],
    sources: [{label: 'OIDC Core', url: 'https://openid.net/specs/openid-connect-core-1_0.html'}],
  },
  reliability: {
    owner: 'Plataforma de IA + operação das dependências',
    metrics: [
      {name: 'Timeout, falha e admissão', coverage: 'Parcial', note: 'Timeout e 429/503 existem. Não há cancelamento garantido, fila durável ou estado distribuído de dependência.'},
      {name: 'Breaker e fallback por modelo', coverage: 'Planejado', note: 'Medir tentativas, motivo, estado do circuito, modelo efetivamente usado e resultado de cada rota.'},
      {name: 'Recuperação de desastre', coverage: 'Planejado', note: 'RTO/RPO, backup e restore precisam de metas e ensaio; memória local não é persistência resiliente.'},
    ],
    triggers: [
      {condition: 'Exemplo: 5 falhas transitórias consecutivas do provedor principal.', action: 'Abrir circuito por 30 s e avaliar modelo alternativo elegível, dentro do orçamento restante de tempo e uso.', recovery: 'Uma sonda em half-open; fechar após sucesso, reabrir se falhar. Limiares precisam de benchmark.'},
      {condition: 'Timeout/OOM ou 503; existe alternativa independente, pronta e validada.', action: 'No máximo uma tentativa de fallback no desenho proposto. Informar a rota degradada e o modelo utilizado.', recovery: 'Retorno ao principal somente após sonda estável e cooldown; não alternar a cada requisição.'},
      {condition: '401, 403, regra de segurança, contexto inválido ou ambas as rotas indisponíveis.', action: 'Não usar fallback para burlar rejeições. Abster-se ou retornar erro explícito; relatório determinístico apenas se houver evidência suficiente.', recovery: 'Corrigir autorização/configuração ou aguardar dependência. Sem inventar resposta bem-sucedida.'},
    ],
    practices: [
      'Separar timeout por etapa e deadline total. Retry e fallback compartilham o mesmo orçamento, incluindo custo de cold start e tentativas do SDK.',
      'Retries apenas para falhas transitórias e operações adequadas; respeitar Retry-After, backoff exponencial e jitter. Evitar retries em camadas multiplicando tentativas.',
      'Bulkhead por dependência, fila limitada e backpressure evitam que um provedor esgote a API inteira. Fila cheia deve ter rejeição explícita.',
      'Dois modelos no mesmo Ollama/GPU compartilham domínio de falha. Sob OOM, carregar mais pesos pode agravar o problema; validar descarregamento e isolamento.',
    ],
    validation: ['Desligar o provedor principal e verificar deadline, limite de tentativas, identidade preservada e identificação da rota.', 'Ensaiar recuperação half-open, falha dupla, restore e retorno ao principal sem tempestade de retries.'],
    sources: [
      {label: 'Circuit Breaker — Azure', url: 'https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker'},
      {label: 'Retry — Azure', url: 'https://learn.microsoft.com/en-us/azure/architecture/patterns/retry'},
    ],
  },
  performance: {
    owner: 'Arquitetura + plataforma + responsável pelo benchmark',
    metrics: [
      {name: 'Latência ponta a ponta e etapas', coverage: 'Medido', note: 'Separar recuperação/embedding, ferramenta e geração; cold start pode dominar a consulta.'},
      {name: 'Tokens/s e memória do modelo', coverage: 'Parcial', note: 'Ollama pode reportar duração e VRAM alocada ao modelo. Isso não informa RAM/VRAM total ou livre.'},
      {name: 'Fila, saturação e TTFT', coverage: 'Planejado', note: 'Medir espera em fila e tempo até primeiro token antes de definir política de autoscaling.'},
    ],
    triggers: [
      {condition: 'Exemplo: espera p95 na fila > 2 s por 3 min, com amostra mínima definida.', action: 'Avaliar capacidade adicional de inferência ou rota leve elegível; escalar API só se ela for o gargalo.', recovery: 'Reduzir capacidade após demanda baixa sustentada e drenagem, respeitando cold start.'},
      {condition: 'Memória insuficiente ou p95 acima do SLO após aumento de contexto/concorrência.', action: 'Reduzir contexto, saída ou concorrência; avaliar quantização e modelo menor com qualidade validada.', recovery: 'Promover configuração após benchmark de carga e memória. Não deduzir capacidade apenas do tamanho em disco.'},
    ],
    practices: [
      'Escalabilidade é capacidade de suportar crescimento; elasticidade é ajustar recursos à demanda. API e inferência precisam de políticas e métricas separadas.',
      'Horizontalizar API sem estado de sessão local, com quotas compartilhadas, corpus persistente e telemetria agregada. Controles por processo se multiplicam ao adicionar réplicas.',
      'Em inferência, validar GPU/VRAM, KV cache, batching, concorrência e tempo de aquecimento. Mais workers na mesma GPU não significam mais throughput.',
      'Configurar min/max de réplicas, readiness com modelo carregado, cooldown e drain no scale-in. O Docker Compose deste laboratório não faz autoscaling.',
    ],
    validation: ['Executar carga com rajada, demanda sustentada e cold start; registrar p95, throughput, rejeições e qualidade.', 'Simular scale-out/in sem perda de sessão, bypass de quotas ou interrupção indevida de trabalho em andamento.'],
    sources: [
      {label: 'Target tracking e cooldown — AWS', url: 'https://docs.aws.amazon.com/autoscaling/application/userguide/target-tracking-scaling-policy-overview.html'},
      {label: 'Modelos carregados — Ollama', url: 'https://docs.ollama.com/api/ps'},
    ],
  },
  cost: {
    owner: 'Produto + FinOps + plataforma',
    metrics: [
      {name: 'Tokens e estimativa por geração', coverage: 'Parcial', note: 'Somente respostas com uso reportado. Preços declarados não equivalem a cobrança conciliada.'},
      {name: 'Custo total por tarefa útil', coverage: 'Planejado', note: 'Incluir embeddings, retries, fallback, armazenamento, rede, infraestrutura local e revisão quando pertinente.'},
      {name: 'Orçamento e projeção de consumo', coverage: 'Planejado', note: 'Contadores atuais são voláteis; ainda não há ledger financeiro nem reserva de orçamento antes de admitir chamadas.'},
    ],
    triggers: [
      {condition: 'Exemplo: consumo ou projeção alcança 80% do orçamento diário aprovado.', action: 'Alertar responsável, revisar modelos e suspender tarefas adiáveis. Não confundir alerta de orçamento com bloqueio em tempo real.', recovery: 'Reavaliar forecast e demanda; elevar teto somente com decisão registrada.'},
      {condition: 'Exemplo: reserva de uso excederia 100% do teto no ledger compartilhado proposto.', action: 'Negar nova chamada faturável ou enfileirar segundo política. Só usar rota leve se ainda couber e tiver qualidade e acesso aprovados.', recovery: 'Liberar com nova janela de orçamento ou aprovação explícita; reconciliar reservas expiradas e uso real.'},
    ],
    practices: [
      'Estimar custo antes da admissão com tokenizador adequado e teto de saída; reservar, executar e reconciliar uso no ledger. Caracteres não garantem limite exato de tokens.',
      'Autoscaling deve ter máximo de capacidade e orçamento. Controlar tokens por minuto, limite do provedor, concorrência global e custo de réplicas ociosas.',
      'Modelo leve pode reduzir custo por chamada, mas maior taxa de erro/retrabalho pode aumentar custo por tarefa útil. Comparar qualidade e sucesso junto de preço.',
      'Local não é gratuito: declarar custo de energia/hardware separadamente. APIs podem ter preços e custos de transferência diferentes; usar contratos e preços atualizados.',
    ],
    validation: ['Simular concorrência no último saldo, falha do ledger e callbacks duplicados; evitar gasto por reserva dupla ou liberação incorreta.', 'Reconciliar relatórios do provedor e custos de infraestrutura com o período, moeda e escopo da estimativa.'],
    sources: [{label: 'Pilares Well-Architected — AWS', url: 'https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html'}],
  },
  sustainability: {
    owner: 'Plataforma + produto + responsável pela medição energética',
    metrics: [
      {name: 'Trabalho e recursos ociosos', coverage: 'Parcial', note: 'Há limites de contexto/saída. Tempo e tokens são proxies de trabalho, não medição de energia.'},
      {name: 'Energia por tarefa útil', coverage: 'Planejado', note: 'Medir kWh com instrumento adequado e carga definida; considerar CPU, GPU, memória e idle.'},
      {name: 'Qualidade por recurso consumido', coverage: 'Planejado', note: 'Comparar modelos com a mesma tarefa e critérios, incluindo retries e respostas inúteis.'},
    ],
    triggers: [
      {condition: 'Exemplo: capacidade de inferência ociosa por 15 min, sem demanda prevista.', action: 'Avaliar descarregar modelo ou reduzir réplicas, respeitando SLO de cold start e demanda mínima.', recovery: 'Aquecer de forma controlada antes da retomada; impedir alternância frequente entre carregar e descarregar.'},
      {condition: 'Modelo menor mantém qualidade mínima e SLO no corpus de avaliação.', action: 'Considerar rota padrão menor para tarefas elegíveis e reservar modelo maior para casos justificados.', recovery: 'Reverter se houver degradação de qualidade, retrabalho ou maior consumo por tarefa útil.'},
    ],
    practices: [
      'Recuperar apenas contexto necessário, limitar saídas e reutilizar embeddings versionados com autorização e invalidação corretas.',
      'Avaliar quantização, modelos menores e escalonamento de tarefas adiáveis com medições. Evitar manter dois modelos aquecidos sem benefício observado.',
      'Não converter tokens ou tempo em CO₂ sem método, fator energético, região, período e fronteira de medição declarados.',
    ],
    validation: ['Comparar carga útil, qualidade e energia antes/depois sob o mesmo cenário; incluir energia de idle e cold start.', 'Verificar se otimização de consumo mantém autorização, acessibilidade e qualidade mínima.'],
    sources: [{label: 'Sustentabilidade — AWS Well-Architected', url: 'https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html'}],
  },
};
