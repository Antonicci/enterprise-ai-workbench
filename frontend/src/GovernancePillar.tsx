import type {GovernanceReport, Pillar} from './governance.types';

type Presentation = {id: string; summary: string};

// A API define os estados. Cor e resumo pertencem à apresentação, não à autorização.
// Associação por nome evita trocar os cartões quando a ordem do backend mudar.
const presentation: Record<string, Presentation> = {
  'Excelência operacional': {
    id: 'operations',
    summary: 'Tempos por etapa, taxas e janela de coleta. Contadores locais ao processo.',
  },
  'Segurança': {
    id: 'security',
    summary: 'Identidade validada, perfis e documentos filtrados no servidor.',
  },
  'Confiabilidade': {
    id: 'reliability',
    summary: 'Timeout e limites de admissão. Sem HA ou SLA.',
  },
  'Eficiência de performance': {
    id: 'performance',
    summary: 'Contexto e saída limitados; tokens/s quando reportados.',
  },
  'Otimização de custos': {
    id: 'cost',
    summary: 'Uso informado; estimativa de API quando há preços. Custo local não medido.',
  },
  'Sustentabilidade': {
    id: 'sustainability',
    summary: 'Limites de processamento; energia e carbono ainda não medidos.',
  },
};

function BackendPolicies({limits}: {limits: GovernanceReport['limits']}) {
  const values = [
    ['Consultas por usuário', limits.requests_per_minute + ' / min'],
    ['Concorrência', String(limits.max_concurrent_requests)],
    ['Timeout', limits.request_timeout_seconds + ' s'],
    ['Contexto Ollama', limits.ollama_num_ctx === null ? 'Não aplicável' : limits.ollama_num_ctx + ' tokens'],
    ['Limite de saída', limits.max_output_tokens + ' tokens'],
    ['Limite do prompt', limits.max_prompt_chars + ' caracteres'],
  ];

  return (
    <section className="backend-policies" aria-label="Políticas aplicadas no backend">
      <h4>POLÍTICAS APLICADAS NO BACKEND</h4>
      <dl className="policy-values">
        {values.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <details>
        <summary>Escopo das políticas</summary>
        <p>{limits.scope} Limite por usuário em janela móvel de 60 s. Excesso retorna 429; contexto excessivo retorna 413 antes da geração.</p>
        <p>Caracteres não são quota de tokens. Timeout e admissão também apoiam confiabilidade; o agrupamento aqui é para consulta dos limites de processamento.</p>
      </details>
    </section>
  );
}

type Props = {
  pillar: Pillar;
  index: number;
  report: GovernanceReport;
  compact: boolean;
};

export default function GovernancePillar({pillar, index, report, compact}: Props) {
  const visual = presentation[pillar.name] ?? {id: 'other', summary: pillar.evidence};

  return (
    <article className={'governance-pillar pillar-' + visual.id} data-pillar={visual.id}>
      <div className="pillar-title">
        <span className="pillar-number">0{index + 1}</span>
        <span className={'control-state ' + pillar.status}>
          {pillar.status === 'parcial' ? 'Parcial' : 'Planejado'}
        </span>
      </div>
      <h3>{pillar.name}</h3>
      <p>{compact ? visual.summary : pillar.evidence}</p>

      {visual.id === 'performance' && <BackendPolicies limits={report.limits}/>}
      {visual.id === 'security' && (
        <details>
          <summary>Permissões desta sessão</summary>
          <ul>{report.identity.permissions.map(permission => <li key={permission}><code>{permission}</code></li>)}</ul>
        </details>
      )}
      {visual.id === 'cost' && (
        <details>
          <summary>Preços para estimativa</summary>
          <p>{report.pricing.enabled
            ? report.pricing.currency + ' · entrada ' + report.pricing.input_per_million + ' / milhão · saída ' + report.pricing.output_per_million + ' / milhão · modelo ' + report.pricing.model
            : 'Preços não habilitados para o modelo de API atual. Não há estimativa financeira bloqueante.'}
          </p>
          <small>{report.pricing.scope}</small>
        </details>
      )}

      <details>
        <summary>{compact ? 'Evidência e lacunas' : 'Próxima evolução'}</summary>
        {compact && <p>{pillar.evidence}</p>}
        <p>{pillar.gap}</p>
      </details>
    </article>
  );
}
