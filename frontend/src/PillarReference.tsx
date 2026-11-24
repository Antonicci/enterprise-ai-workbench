import type {Pillar} from './governance.types';
import {governanceReference} from './governanceReference';

export type ModelContext = {provider: string; model: string};

function ModelResiliencePlan({modelContext}: {modelContext: ModelContext}) {
  const local = modelContext.provider === 'ollama';
  const demo = modelContext.provider === 'demo';
  const primary = demo ? 'qwen2.5:3b — exemplo; demo sem LLM ativo' : modelContext.model;
  const light = local || demo
    ? modelContext.model === 'qwen2.5:1.5b'
      ? 'Escolher outro candidato leve e validar'
      : 'qwen2.5:1.5b — candidato a validar'
    : 'Modelo leve aprovado no mesmo perímetro contratual';

  return (
    <details className="reference-model-plan">
      <summary>Dois modelos e circuit breaker</summary>
      <p className="reference-warning">Desenho de referência. Fallback automático e circuit breaker não estão implementados.</p>
      <div className="reference-models">
        <div><small>P1 / PRINCIPAL</small><strong>{primary}</strong><p>Priorizar a maior capacidade validada para a tarefa, dentro de qualidade, memória, latência e orçamento.</p></div>
        <div><small>P2 / ROTA LEVE PROPOSTA</small><strong>{light}</strong><p>Não se presume instalado, disponível, mais rápido ou com qualidade suficiente. Exige benchmark e aprovação antes de habilitar.</p></div>
      </div>
      <ol className="reference-route">
        <li>Validar identidade, ACL, escopo e admissão.</li>
        <li>Executar P1 com deadline e orçamento de tentativa.</li>
        <li>Em falha transitória elegível, consultar circuito e capacidade da alternativa.</li>
        <li>Tentar P2 uma única vez se a política e o saldo de tempo/uso permitirem; informar modelo e motivo da degradação.</li>
        <li>Se não houver rota segura, abster-se ou retornar indisponibilidade. Relatório determinístico somente com evidência suficiente.</li>
      </ol>
      <p>Preservar as mesmas fontes autorizadas e controles numéricos nas duas rotas. Não trocar de provedor para contornar rejeição de segurança.</p>
      <p>Mesmo daemon/GPU é um domínio de falha compartilhado. Carregar P2 sob falta de memória pode piorar a saturação; cold start também consome o deadline.</p>
    </details>
  );
}

function ScalingPlan() {
  return (
    <details>
      <summary>Escalabilidade e elasticidade</summary>
      <p className="reference-warning">Referência de implantação. O Compose atual não cria ou remove réplicas automaticamente.</p>
      <dl className="reference-decisions">
        <div><dt>API</dt><dd>Réplicas sem estado local, autenticação preservada, quotas compartilhadas e telemetria agregada. Mais API não corrige uma GPU saturada.</dd></div>
        <div><dt>Inferência</dt><dd>Fila limitada, throughput por modelo, VRAM/CPU e cold start. Validar batching e concorrência em cada pool de execução.</dd></div>
        <div><dt>Scale-out proposto</dt><dd>Sinal de fila + latência + saturação por janela; respeitar máximo de réplicas, limite do provedor e reserva de orçamento.</dd></div>
        <div><dt>Scale-in proposto</dt><dd>Demanda baixa sustentada, cooldown e drenagem das requisições em andamento. Evitar descarregar modelo antes de terminar trabalho admitido.</dd></div>
      </dl>
      <p>Definir mínimo/máximo e tempo de aquecimento por ambiente. Uma quota de 30/min por processo vira potencialmente 120/min com quatro réplicas se não houver controle compartilhado.</p>
    </details>
  );
}

function CostEnvelope() {
  return (
    <details>
      <summary>Orçamento e elasticidade de custos</summary>
      <p className="reference-warning">Os tetos de orçamento e reservas abaixo são referência. Ainda não bloqueiam gasto no laboratório.</p>
      <ol>
        <li>Definir moeda, período, responsável e teto por produto/ambiente.</li>
        <li>Antes de admitir, estimar com tokenizador e preços válidos; reservar uso no ledger compartilhado.</li>
        <li>Contabilizar geração, embeddings, retries e fallback. Reconciliar reserva com uso real, incluindo chamadas que falharam.</li>
        <li>Limitar réplicas e concorrência global pelo orçamento e pela capacidade, além de alertar sobre tendência de consumo.</li>
        <li>Reduzir capacidade ociosa com cooldown e preservar a capacidade mínima necessária ao SLO.</li>
      </ol>
      <p>Exemplos de desenho: alertar em 80%; negar admissão que ultrapassaria 100% do teto reservado. Alertas tardios de faturamento não substituem um bloqueio antes da chamada.</p>
      <p>Rota leve só é elegível se couber no orçamento e preservar qualidade e política de dados. Sem saldo ou rota segura, rejeitar explicitamente; não declarar custo local zero.</p>
    </details>
  );
}

type Props = {
  id: string;
  pillar: Pillar;
  compact: boolean;
  modelContext: ModelContext;
};

export default function PillarReference({id, pillar, compact, modelContext}: Props) {
  const guide = governanceReference[id];

  return (
    <details className="pillar-reference">
      <summary>Referência e evolução</summary>
      {compact && <p>{pillar.evidence}</p>}
      <p><strong>Lacuna atual:</strong> {pillar.gap}</p>
      {guide && <>
        <p className="reference-warning">Guia de referência · gatilhos, automações e metas propostos não estão ativos. Números são exemplos; calibrar por SLO, carga, qualidade e risco.</p>
        <p><strong>Responsável sugerido:</strong> {guide.owner}.</p>

        <details>
          <summary>Métricas e gatilhos propostos</summary>
          <h4>Cobertura de medição atual</h4>
          <dl className="reference-metrics">
            {guide.metrics.map(metric => (
              <div key={metric.name}>
                <dt>{metric.name} <span className="reference-coverage">{metric.coverage}</span></dt>
                <dd>{metric.note}</dd>
              </div>
            ))}
          </dl>
          <h4>Condição → ação → recuperação</h4>
          {guide.triggers.map(trigger => (
            <section className="reference-trigger" key={trigger.condition}>
              <h5>{trigger.condition}</h5>
              <p><strong>Ação proposta:</strong> {trigger.action}</p>
              <p><strong>Retorno:</strong> {trigger.recovery}</p>
            </section>
          ))}
        </details>

        {id === 'reliability' && <ModelResiliencePlan modelContext={modelContext}/>}
        {id === 'performance' && <ScalingPlan/>}
        {id === 'cost' && <CostEnvelope/>}

        <details>
          <summary>Boas práticas e validação</summary>
          <ul>{guide.practices.map(practice => <li key={practice}>{practice}</li>)}</ul>
          <h4>Como verificar antes de promover</h4>
          <ul>{guide.validation.map(check => <li key={check}>{check}</li>)}</ul>
        </details>

        <details>
          <summary>Fontes de referência</summary>
          <ul>{guide.sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.label} ↗</a></li>)}</ul>
        </details>
      </>}
    </details>
  );
}
