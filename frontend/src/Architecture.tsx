import {useState} from 'react';
type Props={authMode:string;provider:string;store:string};
const nodes=[
 {id:'ui',x:30,y:35,title:'Interface web',sub:'React + TypeScript',detail:'Conversa, fontes, edição, identidade e métricas. A interface não concede permissões.'},
 {id:'idp',x:370,y:35,title:'Identidade',sub:'Keycloak / Entra ID / demo',detail:'Login OIDC com Authorization Code + PKCE. O backend valida assinatura, issuer, audience e expiração do access token. No modo demo usa tokens locais.'},
 {id:'policy',x:710,y:35,title:'API e políticas',sub:'FastAPI · perfis e permissões',detail:'Resolve perfil no servidor e autoriza recurso e ação. Gestor edita; nível 1 consulta; nível 2 consulta fontes restritas e métricas.'},
 {id:'rag',x:30,y:230,title:'Recuperação RAG',sub:'Somente fontes autorizadas',detail:'Gera vetor da pergunta e busca apenas documentos permitidos antes de montar o contexto. Similaridade não é confiança.'},
 {id:'ingest',x:370,y:230,title:'Gestão de documentos',sub:'Incluir · editar · classificar',detail:'Apenas gestor. Persiste texto original, divide em trechos e reindexa conteúdo e classificação. O seed não sobrescreve edições na v0.2.'},
 {id:'mcp',x:710,y:230,title:'Gateway + MCP',sub:'Ferramentas em allowlist',detail:'Backend e worker stdio validam a permissão da ferramenta. Worker local pertence à mesma aplicação; não é um endpoint MCP remoto.'},
 {id:'embed',x:30,y:420,title:'Embeddings',sub:'Hash demo / LangChain',detail:'Demo usa hashing lexical. Ollama e API usam embeddings do provedor configurado. Troca de modelo exige reindexação.'},
 {id:'store',x:370,y:420,title:'Documentos e vetores',sub:'Memória / PostgreSQL + pgvector',detail:'Texto, nível de acesso e trechos. Namespace ACL v2 separa os dados do laboratório antigo. Memória é volátil.'},
 {id:'tools',x:710,y:420,title:'Ferramentas de leitura',sub:'Serviço / assistente',detail:'get_service_metrics retorna fixtures sintéticas. get_ai_quality_metrics retorna contadores reais do processo; qualidade, tokens e custo não medidos.'},
 {id:'answer',x:370,y:610,title:'Resposta com evidências',sub:'Extrativa / Ollama / API',detail:'Recebe somente contexto autorizado. Modelo não executa ferramentas. Resposta inclui fontes, trace e duração; exige revisão.'},
];
const edges=[['ui','idp'],['idp','policy'],['policy','rag'],['policy','ingest'],['policy','mcp'],['rag','embed'],['ingest','store'],['ingest','embed'],['embed','store'],['mcp','tools'],['store','answer'],['tools','answer']];
const flows:Record<string,string[]>={overview:nodes.map(n=>n.id),query:['ui','policy','rag','embed','store','answer'],ingest:['ui','policy','ingest','embed','store'],mcp:['ui','policy','mcp','tools','answer'],auth:['ui','idp','policy']};
export default function Architecture({authMode,provider,store}:Props){
 const [flow,setFlow]=useState('overview');const [selected,setSelected]=useState('policy');
 const active=flows[flow];const node=nodes.find(n=>n.id===selected)!;
 return <section className="panel"><div className="panel-title">MAPA DE COMPONENTES / EXPLORE OS CAMINHOS</div>
 <div className="flow-tabs" aria-label="Fluxo da arquitetura">{[['overview','Visão geral'],['auth','Login e acesso'],['query','Consulta RAG'],['ingest','Ingestão'],['mcp','Ferramentas MCP']].map(([id,title])=><button key={id} aria-pressed={flow===id} onClick={()=>setFlow(id)}>{title}</button>)}</div>
 <p>Configuração conectada: <strong>{authMode}</strong> · <strong>{provider}</strong> · <strong>{store}</strong>. Clique em um componente para ver sua responsabilidade. O mapa explica o fluxo; não é uma animação de execução real.</p>
 <div className="diagram-scroll"><svg viewBox="0 0 1000 745" className="component-map" aria-label="Diagrama de componentes da solução">
 <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#769f58"/></marker></defs>
 {edges.map(([a,b])=>{const from=nodes.find(n=>n.id===a)!;const to=nodes.find(n=>n.id===b)!;const horizontal=from.y===to.y;const x1=horizontal?from.x+250:from.x+125,y1=horizontal?from.y+48:from.y+96,x2=horizontal?to.x:to.x+125,y2=horizontal?to.y+48:to.y;return <path key={a+b} d={horizontal?`M${x1} ${y1} L${x2} ${y2}`:`M${x1} ${y1} C${x1} ${y1+45} ${x2} ${y2-45} ${x2} ${y2}`} fill="none" stroke={active.includes(a)&&active.includes(b)?'#769f58':'#dce2ea'} strokeWidth="2" markerEnd="url(#arrow)" opacity={active.includes(a)&&active.includes(b)?1:0.35}/>;})}
 {nodes.map(n=><g key={n.id} role="button" tabIndex={0} aria-label={n.title} aria-pressed={selected===n.id} onClick={()=>setSelected(n.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(n.id);}}} className="map-node" opacity={active.includes(n.id)?1:0.35}><rect x={n.x} y={n.y} width="250" height="96" rx="12" fill={selected===n.id?'#eaf5dd':'#f8fafc'} stroke={selected===n.id?'#679b3d':'#cbd6e4'} strokeWidth={selected===n.id?2:1}/><text x={n.x+16} y={n.y+37} fontSize="16" fontWeight="650" fill="#17243a">{n.title}</text><text x={n.x+16} y={n.y+65} fontSize="12" fill="#60718a">{n.sub}</text></g>)}
 </svg></div><article className="component-detail" aria-live="polite"><h3>{node.title}</h3><p>{node.detail}</p></article>
 <div className="architecture-cards"><article><h3>Gestor de conhecimento</h3><p>Consulta níveis 1 e 2, inclui, edita e classifica documentos. Sem métricas.</p></article><article><h3>Consulta nível 1</h3><p>Pesquisa e lê apenas documentos nível 1. Sem escrita e sem ferramentas de métricas.</p></article><article><h3>Consulta nível 2</h3><p>Pesquisa níveis 1 e 2 e acessa métricas da aplicação e do assistente. Sem escrita.</p></article></div>
 <p>Entra ID é uma alternativa de configuração OIDC com tenant, audiência e app roles próprios. O laboratório local fornece Keycloak. Nenhum provedor foi ativado apenas por aparecer no mapa.</p>
 </section>;
}
