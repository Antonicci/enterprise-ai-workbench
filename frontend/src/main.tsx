import React, {useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {accessToken,initializeAuth,login,logout,onSessionExpired,type AuthSettings} from './auth';
import Architecture from './Architecture';
import Operations from './Operations';
import Governance from './Governance';
import Investigation,{type InvestigationResult} from './Investigation';
import PublicHome from './PublicHome';
import SessionHeader from './SessionHeader';
import './style.css';
type Result=InvestigationResult;
type Config={provider:string;store:string;chat_model:string;embedding_model:string;groups:string[];metrics_allowed:boolean;name:string;roles:string[];role_labels:string[];permissions:string[];auth_mode:string};
type Doc={id:string;title:string;text:string;access_level:'level1'|'level2';services:string[]};
type DocSummary=Omit<Doc,'text'>;
const suggestions=['Como investigar erros HTTP 500 na API de pedidos?','Quais cuidados tomar com retentativas em pagamentos?','Qual o procedimento para propor uma mitigação?'];
const emptyDoc:Doc={id:'',title:'',text:'',access_level:'level1',services:[]};
function App(){
 const [presentation,setPresentation]=useState(false);
 const [compact,setCompact]=useState(false);
 const [documentScope,setDocumentScope]=useState('auto');
 const [sessionState,setSessionState]=useState<'loading'|'guest'|'authenticated'|'blocked'>('loading');
 const [workspaceRequested,setWorkspaceRequested]=useState(location.pathname.startsWith('/workspace'));
 const redirectStarted=useRef(false);
 const [token,setToken]=useState('demo-analyst');const [auth,setAuth]=useState<AuthSettings|null>(null);const [config,setConfig]=useState<Config|null>(null);
 const [question,setQuestion]=useState(suggestions[0]);const [metrics,setMetrics]=useState(false);const [service,setService]=useState('orders-api');
 const [result,setResult]=useState<Result|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const [tab,setTab]=useState<'investigate'|'ingest'|'architecture'|'observability'|'governance'>('investigate');
 const [doc,setDoc]=useState<Doc>(emptyDoc);const [editing,setEditing]=useState(false);const [documents,setDocuments]=useState<DocSummary[]>([]);
 const [notice,setNotice]=useState('');const epoch=useRef(0);
 const canWrite=!!config?.permissions.includes('documents:write');const canAI=!!config?.permissions.includes('ai-metrics:read');
 function clearSession(){epoch.current++;setCompact(false);setPresentation(false);setDocumentScope('auto');setSessionState('guest');setTab('investigate');setQuestion(suggestions[0]);setService('orders-api');setResult(null);setConfig(null);setMetrics(false);setError('');setNotice('');setDocuments([]);setDoc(emptyDoc);setEditing(false);}
 async function request(path:string,body?:unknown){
  const generation=epoch.current;
  const credential=await accessToken(token);
  const response=await fetch(path,{method:body?'POST':'GET',headers:{Authorization:`Bearer ${credential}`,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});
  if(generation!==epoch.current) throw new Error('Sessão alterada. Repita a operação.');
  if(!response.ok){if(response.status===401)clearSession();const data=await response.json().catch(()=>null);throw new Error(typeof data?.detail==='string'?data.detail:`Falha ${response.status}. Confira acesso e disponibilidade.`);}
  const data=await response.json();
  if(generation!==epoch.current) throw new Error('Sessão alterada. Repita a operação.');
  return data;
 }
 async function openWorkspace(){try{await accessToken(token);setWorkspaceRequested(true);history.replaceState({},'', '/workspace');}catch(e){clearSession();setError((e as Error).message);}}
 function openPublic(){setWorkspaceRequested(false);history.pushState({},'', '/');}
 useEffect(()=>{let active=true;initializeAuth().then(async state=>{if(!active)return;setAuth(state.settings);if(state.authenticated){try{const c=await request('/api/config');if(active){setConfig(c);setSessionState('authenticated');openWorkspace();}}catch(e){if(active){setSessionState('blocked');setError((e as Error).message);}}}else{setSessionState('guest');}}).catch(e=>{if(active){setSessionState('blocked');setError((e as Error).message);}});return()=>{active=false;};},[]);
 useEffect(()=>onSessionExpired(()=>clearSession()),[]);
 useEffect(()=>{function navigate(){setWorkspaceRequested(location.pathname.startsWith('/workspace'));}window.addEventListener('popstate',navigate);return()=>window.removeEventListener('popstate',navigate);},[]);
 async function startLogin(){setError('');redirectStarted.current=true;try{await login();}catch(e){setSessionState('blocked');setError((e as Error).message);}}
 useEffect(()=>{if(workspaceRequested&&sessionState==='guest'&&auth?.mode==='oidc'&&!redirectStarted.current)void startLogin();},[workspaceRequested,sessionState,auth]);
 async function connect(){clearSession();setSessionState('loading');try{setConfig(await request('/api/config'));setSessionState('authenticated');openWorkspace();}catch(e){setSessionState('blocked');setError((e as Error).message);}}
 async function signOut(){openPublic();clearSession();if(auth?.mode==='oidc'){try{await logout();}catch(e){setError((e as Error).message);}}}
 async function loadDocuments(){try{setDocuments(await request('/api/documents'));}catch(e){setError((e as Error).message);}}
 useEffect(()=>{if(tab==='ingest'&&config)void loadDocuments();},[tab,config]);
 async function investigate(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');setResult(null);try{setResult(await request('/api/chat',{question,include_metrics:metrics,service,document_scope:documentScope}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function ingest(e:React.FormEvent){e.preventDefault();setBusy(true);setNotice('');setError('');try{const r=await request('/api/documents',doc);setNotice(`${r.chunks} trechos indexados. Conteúdo e nível de acesso atualizados.`);setEditing(true);await loadDocuments();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function openDocument(id:string){setError('');setNotice('');try{setDoc(await request('/api/documents/'+encodeURIComponent(id)));setEditing(true);}catch(e){setError((e as Error).message);}}
 if(sessionState==='loading'&&!auth)return <div className="session-loading" role="status">Preparando seu acesso…</div>;
 if(!config||!workspaceRequested)return <PublicHome mode={auth?.mode??null} loading={sessionState==='loading'} error={error} token={token} onToken={value=>{clearSession();setToken(value);}} onEnter={()=>{if(auth?.mode==='oidc')void startLogin();else void connect();}} authenticated={!!config} onOpen={openWorkspace}/>;
 return <div className={`shell ${presentation&&tab==='investigate'?'presentation-mode':''} ${compact?'compact-mode':''}`}><aside><a className="brand" href="https://github.com/Antonicci/enterprise-ai-workbench"><span className="logo">W</span><span>Enterprise AI<small>WORKBENCH / LAB 04</small></span></a><p className="section-label">WORKSPACE</p><nav>{([['investigate','Investigar'],['ingest','Conhecimento'],['observability','Operação'],['governance','Governança'],['architecture','Arquitetura']] as const).filter(([id])=>id!=='observability'||canAI).map(([id,label])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id)}>{label}<span>↗</span></button>)}</nav><div className="aside-bottom"><span className="dot"/> Laboratório de arquitetura<p>Identidade · RAG · MCP</p><a href="https://chihuahuasstudios.com/architectures/">Chihuahuas Studios ↗</a></div></aside>
 <main><SessionHeader name={config.name} profiles={config.role_labels} permissions={config.permissions} mode={config.auth_mode} onLogout={()=>void signOut()} onPublic={openPublic}/>
 <div className="visual-toolbar"><strong>{compact?'Enterprise AI Workbench · LAB 04':''}</strong>{compact&&<nav aria-label="Seções da visão compacta">{([['investigate','Investigar'],['governance','Governança'],['architecture','Arquitetura']] as const).map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>{setTab(id);window.scrollTo(0,0);}}>{label}</button>)}</nav>}<button className="secondary" aria-pressed={compact} onClick={()=>{setCompact(value=>!value);setPresentation(false);window.scrollTo(0,0);}}>{compact?'Sair da visão compacta':'Visão compacta'}</button></div>
 <div className="heading"><div><p className="eyebrow">EVIDÊNCIAS ANTES DE AÇÕES</p><h1>{tab==='investigate'?(presentation?'Enterprise AI Workbench':'Investigue com contexto.'):tab==='ingest'?'Conhecimento autorizado.':tab==='observability'?'Operação com evidências.':tab==='governance'?'Governança que você pode conferir.':'Explore a arquitetura.'}</h1><p className="subtitle">Identidade, documentos e ferramentas com permissões explícitas.</p></div><span className="pill">v0.4 · laboratório</span></div>
 <div className="status-grid environment-strip"><div><small>MODELO ATIVO</small><strong>{config.chat_model}</strong></div><div><small>CONHECIMENTO</small><strong>{config.store==='memory'?'Memória · laboratório':'PostgreSQL + pgvector'}</strong></div><div><small>ACESSO DOCUMENTAL</small><strong>{config.groups.includes('level2')?'Níveis 1 e 2':'Nível 1'}</strong></div></div>
 {error&&<div role="alert" className="error">{error}</div>}
 {tab==='investigate'&&<Investigation compact={compact} question={question} onQuestion={setQuestion} documentScope={documentScope} onDocumentScope={setDocumentScope} metrics={metrics} onMetrics={setMetrics} service={service} onService={setService} busy={busy} result={result} config={config} onSubmit={investigate} presentation={presentation} onPresentation={()=>setPresentation(value=>!value)}/>}
 {tab==='ingest'&&<section className="panel"><div className="panel-title">BIBLIOTECA / CONSULTAR E EDITAR</div>{!config?<p>Conecte-se para ver os documentos autorizados.</p>:<><div className="document-toolbar"><label>Documento<select aria-label="Documento" value={editing?doc.id:''} onChange={e=>{if(e.target.value)void openDocument(e.target.value);else{setDoc(emptyDoc);setEditing(false);}}}><option value="">Selecione um documento</option>{documents.map(d=><option value={d.id} key={d.id}>{d.title} · {d.access_level==='level1'?'Nível 1':'Nível 2'}</option>)}</select></label>{canWrite&&<button className="secondary" onClick={()=>{setDoc(emptyDoc);setEditing(false);setNotice('');}}>Novo documento</button>}</div><p>{canWrite?'Você pode incluir, editar e classificar documentos.':'Seu perfil permite leitura dos documentos disponíveis abaixo.'} Utilize dados sintéticos neste laboratório.</p><form onSubmit={ingest}><label>ID<input required disabled={!canWrite||editing} pattern="[a-zA-Z0-9_-]{1,80}" value={doc.id} onChange={e=>setDoc({...doc,id:e.target.value})}/></label><label>Título<input required readOnly={!canWrite} maxLength={160} value={doc.title} onChange={e=>setDoc({...doc,title:e.target.value})}/></label><label>Acesso<select aria-label="Acesso" disabled={!canWrite} value={doc.access_level} onChange={e=>setDoc({...doc,access_level:e.target.value as Doc['access_level']})}><option value="level1">Consulta nível 1 e nível 2</option><option value="level2">Somente consulta nível 2 e gestor</option></select></label><label>Serviços do documento<select aria-label="Serviços do documento" disabled={!canWrite} value={doc.services.join(',')} onChange={e=>setDoc({...doc,services:e.target.value?e.target.value.split(','):[]})}><option value="">Geral / todos os serviços</option><option value="orders-api">Pedidos · orders-api</option><option value="payments-api">Pagamentos · payments-api</option><option value="orders-api,payments-api">Pedidos e pagamentos</option></select></label><label>Conteúdo<textarea required readOnly={!canWrite} minLength={20} maxLength={30000} value={doc.text} onChange={e=>setDoc({...doc,text:e.target.value})}/></label>{canWrite&&<button className="primary" disabled={busy}>{editing?'Salvar e reindexar →':'Incluir e indexar →'}</button>}</form>{notice&&<p role="status">{notice}</p>}</>}</section>}
 {tab==='observability'&&canAI&&<Operations request={request}/>}
 {tab==='governance'&&<Governance request={request} canOperate={canAI} compact={compact}/>}
 {tab==='architecture'&&<Architecture compact={compact} authMode={config?.auth_mode??auth?.mode??'não conectado'} provider={config?.provider??'consulte após conectar'} store={config?.store??'não conectado'}/>}
 <footer>Enterprise AI Workbench <span>Aprender, demonstrar e explicar decisões.</span></footer></main></div>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
