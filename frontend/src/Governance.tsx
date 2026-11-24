import {useEffect, useState} from 'react';
import GovernancePillar from './GovernancePillar';
import type {ApiRequest, GovernanceReport, RuntimeReport} from './governance.types';

type Props = {
  request: ApiRequest;
  canOperate: boolean;
  compact?: boolean;
};

const gib = (bytes: number | null) =>
  bytes === null ? 'Não informado' : (bytes / 1024 ** 3).toFixed(2) + ' GiB';

export default function Governance({request, canOperate, compact = false}: Props) {
  const [report, setReport] = useState<GovernanceReport | null>(null);
  const [runtime, setRuntime] = useState<RuntimeReport | null>(null);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    request('/api/governance')
      .then(data => { if (active) setReport(data as GovernanceReport); })
      .catch(reason => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, []);

  async function diagnose() {
    setBusy(true);
    setError('');
    try {
      const data = await request('/api/runtime') as RuntimeReport;
      setRuntime(data);
      setSelected(
        data.models.find(model => model.name === data.configured_model)?.name
        ?? data.models[0]?.name
        ?? ''
      );
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const model = runtime?.models.find(item => item.name === selected);
  const cards = (compactCards: boolean) => report?.pillars.map((pillar, index) => (
    <GovernancePillar key={pillar.name} pillar={pillar} index={index} report={report} compact={compactCards}/>
  ));

  return (
    <div className="governance-view">
      {error && <p className="error" role="alert">{error}</p>}
      {report && <>
        {compact && (
          <section className="panel governance-overview" aria-label="Visão compacta da governança">
            <div className="panel-title">
              <span>SEIS PILARES / CONTROLES E LIMITES</span>
              <span className="pill">{report.identity.mode === 'oidc' ? 'OIDC + PKCE' : 'DEMO · SINTÉTICO'}</span>
            </div>
            <div className="pillar-grid">{cards(true)}</div>
            <p className="compact-boundary">
              Referência Well-Architected · laboratório, sem certificação. Limites de chat por processo;
              caracteres não são quota de tokens. Custo tem cobertura parcial; sem orçamento bloqueante.
            </p>
          </section>
        )}

        <details className="governance-full" key={compact ? 'compact' : 'full'} open={!compact}>
          <summary>Políticas completas e diagnóstico de modelos</summary>
          <section className="panel">
            <div className="panel-title">
              <span>GOVERNANÇA / CONTROLES E EVIDÊNCIAS</span>
              <span className="pill">REFERÊNCIA WELL-ARCHITECTED</span>
            </div>
            <p>{report.scope}</p>
            <div className="governance-summary">
              <article>
                <small>IDENTIDADE ATIVA</small>
                <strong>{report.identity.mode === 'oidc' ? 'OIDC + PKCE' : 'Demo · sintético'}</strong>
                <p>{report.identity.roles.join(' · ')}</p>
              </article>
              <article>
                <small>SAÍDA MÁXIMA</small>
                <strong>{report.limits.max_output_tokens} tokens</strong>
                <p>Solicitado ao provedor de geração.</p>
              </article>
              <article>
                <small>CONTEXTO ENVIADO</small>
                <strong>{report.limits.max_prompt_chars.toLocaleString('pt-BR')} caracteres</strong>
                <p>Limite de texto; não é quota de tokens.</p>
              </article>
            </div>
            <div className="pillar-grid">{cards(false)}</div>
            <small>{report.framework} · estados representam o laboratório, não pontuação ou certificação.</small>
          </section>

          <section className="panel">
            <div className="panel-title">MODELO E CAPACIDADE / DIAGNÓSTICO OLLAMA</div>
            <p>Seleção explícita conforme tarefa, quantização, contexto, memória e benchmark. Este painel não altera o modelo ativo.</p>
            {canOperate ? (
              <button className="secondary" disabled={busy} onClick={diagnose}>
                {busy ? 'Consultando Ollama…' : 'Consultar capacidade e modelos'}
              </button>
            ) : <p>Diagnóstico operacional restrito ao perfil Consulta nível 2.</p>}

            {runtime && <>
              <p>
                Modelo configurado: <strong>{runtime.configured_model}</strong>.
                Host declarado pelo operador: RAM {runtime.declared_host.ram_gb ?? 'não informada'} GB
                · VRAM {runtime.declared_host.vram_gb ?? 'não informada'} GB.
              </p>
              {!runtime.available && <p>{runtime.reason}</p>}
              {runtime.models.length > 0 && <>
                <label>
                  Modelo para análise
                  <select value={selected} onChange={event => setSelected(event.target.value)}>
                    {runtime.models.map(item => <option key={item.name}>{item.name}</option>)}
                  </select>
                </label>
                {model && (
                  <div className="architecture-cards">
                    <article>
                      <h3>Artefato instalado</h3>
                      <strong>{model.name}</strong>
                      <p>{model.parameters ?? 'Parâmetros não informados'} · {model.quantization ?? 'Quantização não informada'}</p>
                      <small>Download: {gib(model.download_bytes)}. Tamanho em disco não é requisito de VRAM.</small>
                    </article>
                    <article>
                      <h3>Execução observada</h3>
                      <strong>{model.loaded ? 'Carregado no Ollama' : 'Não carregado'}</strong>
                      <p>Memória informada: {gib(model.loaded_bytes)} · em VRAM: {gib(model.loaded_vram_bytes)}.</p>
                      <small>
                        Contexto reportado: {model.context_length ?? 'não informado'}.
                        Zero em VRAM indica ausência de alocação GPU reportada.
                      </small>
                    </article>
                    <article>
                      <h3>Decisão de capacidade</h3>
                      <p>Execute uma consulta representativa e confira tokens/s e p95 em Operação. Se houver pressão de memória, avalie modelo menor ou menor contexto.</p>
                      <small>Para trocar: configure CHAT_MODEL e reinicie. Valide qualidade antes de promover.</small>
                    </article>
                  </div>
                )}
              </>}
              {/* /api/ps não informa RAM/VRAM total. Valor ausente deve continuar desconhecido. */}
              <ul>{runtime.limitations.map(limitation => <li key={limitation}>{limitation}</li>)}</ul>
            </>}
            <p className="hint">
              Sem inventário automático de RAM/VRAM total, escolha automática ou medição de energia.
              Credenciais e endereços internos não são exibidos.
            </p>
          </section>
        </details>
      </>}
    </div>
  );
}
