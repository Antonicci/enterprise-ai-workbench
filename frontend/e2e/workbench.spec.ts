import {test,expect,type Page} from '@playwright/test';
const oidc=process.env.AUTH_TEST_MODE==='oidc';
async function connect(page:Page,role:'manager'|'l1'|'l2'){
 await page.goto('/');
 if(oidc){
  await page.getByRole('button',{name:'Entrar com SSO'}).click();
  await page.locator('#username').fill({manager:'gestor',l1:'consulta1',l2:'consulta2'}[role]);
  await page.locator('#password').fill('Workbench-Lab-2026!');
  await page.locator('#kc-login').click();
 }else{
  await page.locator('input[type=password]').fill({manager:'demo-manager',l1:'demo-analyst',l2:'demo-ops'}[role]);
  await page.getByRole('button',{name:'Conectar',exact:true}).click();
 }
 await expect(page.getByRole('banner',{name:'Sessão ativa'})).toBeVisible();
}
test('level 1 can investigate but cannot use metrics or edit',async({page})=>{
 await connect(page,'l1');
 await expect(page.getByRole('checkbox')).toBeDisabled();
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.locator('.response')).toContainText('Demonstração extrativa');
 await page.getByRole('button',{name:'Conhecimento',exact:false}).click();
 await expect(page.getByRole('button',{name:'Novo documento'})).toHaveCount(0);
 await expect(page.getByRole('combobox').first()).not.toContainText('Procedimento restrito');
});
test('manager can create, reopen and change document access',async({page})=>{
 await connect(page,'manager');
 await expect(page.getByRole('checkbox')).toBeDisabled();
 await page.getByRole('button',{name:'Conhecimento',exact:false}).click();
 await page.getByRole('button',{name:'Novo documento'}).click();
 const id='e2e-'+Date.now();
 await page.getByLabel('ID',{exact:true}).fill(id);
 await page.getByLabel('Título',{exact:true}).fill('Procedimento Zephyr E2E');
 await page.getByLabel('Conteúdo',{exact:true}).fill('Zephyr utiliza uma fila sintética de faturamento para o teste de edição.');
 await page.getByRole('button',{name:'Incluir e indexar →'}).click();
 await expect(page.getByRole('status')).toContainText('trechos indexados');
 await page.getByLabel('Acesso',{exact:true}).selectOption('level2');
 await page.getByRole('button',{name:'Salvar e reindexar →'}).click();
 await expect(page.getByRole('status')).toContainText('trechos indexados');
 await page.getByRole('button',{name:'Novo documento'}).click();
 await page.getByLabel('Documento',{exact:true}).selectOption(id);
 await expect(page.getByLabel('Acesso',{exact:true})).toHaveValue('level2');
});
test('level 2 can use both MCP metrics tools and inspect component map',async({page})=>{
 await connect(page,'l2');
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.getByText('✓ get_service_metrics · MCP stdio')).toBeVisible();
 await page.getByRole('button',{name:'Operação',exact:false}).click();
 await page.getByRole('button',{name:'Consultar métricas do assistente'}).click();
 await expect(page.getByText('✓ get_ai_quality_metrics', {exact:false})).toBeVisible();
 await page.getByRole('button',{name:'Arquitetura',exact:false}).click();
 await page.getByRole('button',{name:'Login e acesso',exact:true}).click();
 await page.getByRole('button',{name:'API e políticas',exact:true}).click();
 await expect(page.locator('.component-detail')).toContainText('Resolve perfil no servidor');
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('public layer has no workspace controls and private APIs reject guests',async({page})=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Entre para explorar.'})).toBeVisible();
 await expect(page.locator('.shell')).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Investigar →',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Conhecimento',exact:false})).toHaveCount(0);
 const response=await page.request.get('/api/documents');
 expect(response.status()).toBe(401);
 if(oidc){
  await page.goto('/workspace');
  await expect(page).toHaveURL(/localhost:8180/);
  await expect(page.locator('#username')).toBeVisible();
 }else{
  await page.goto('/workspace');
  await expect(page.getByRole('button',{name:'Conectar',exact:true})).toBeVisible();
  await expect(page.locator('.shell')).toHaveCount(0);
 }
});
test('header shows current profile, permissions and logout removes private interface',async({page})=>{
 await connect(page,'l2');
 const header=page.getByRole('banner',{name:'Sessão ativa'});
 await expect(header).toContainText('Consulta nível 2');
 if(oidc)await expect(header).toContainText('consulta2');
 await header.getByText('Permissões',{exact:true}).click();
 await expect(page.getByLabel('Permissões atuais')).toContainText('metrics:read');
 const signout=oidc?page.waitForResponse(response=>response.url().includes('/protocol/openid-connect/logout')):Promise.resolve();
 await header.getByRole('button',{name:'Sair',exact:true}).click();
 await signout;
 if(oidc)await page.waitForURL('http://localhost:8080/');
 await expect(page.getByRole('heading',{name:'Entre para explorar.'})).toBeVisible();
 await expect(page.locator('.shell')).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
test('a rejected session clears protected content instead of leaving the app visible',async({page})=>{
 await connect(page,'l1');
 // Reject the next operation and any automatic SSO revalidation: no protected UI may survive a 401.
 await page.route('**/api/chat',route=>route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:'Sessão expirada no teste'})}));
 await page.route('**/api/config',route=>route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:'Sessão expirada no teste'})}));
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.locator('.shell')).toHaveCount(0);
 await expect(page.getByRole('heading',{name:'Entre para explorar.'})).toBeVisible();
});
test('presentation mode keeps identity, measured stages and source evidence',async({page})=>{
 await connect(page,'l1');
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.getByLabel('Etapas medidas da consulta')).toContainText('Resposta extrativa');
 await expect(page.getByLabel('Etapas medidas da consulta')).toContainText('Não usada');
 await page.getByRole('button',{name:'Modo apresentação',exact:true}).click();
 await expect(page.locator('.presentation-mode')).toBeVisible();
 await expect(page.getByRole('banner',{name:'Sessão ativa'})).toContainText('Consulta nível 1');
 await expect(page.getByRole('button',{name:'Conhecimento',exact:false})).toBeHidden();
 await page.getByText('Ver trecho recuperado',{exact:true}).first().click();
 await expect(page.locator('.source-panel')).toContainText('Documento SINTÉTICO');
 await page.getByRole('button',{name:'Sair da apresentação',exact:true}).click();
 await expect(page.getByRole('button',{name:'Conhecimento',exact:false})).toBeVisible();
});
test('retrieval shows document scope and distinguishes direct MCP evidence',async({page})=>{
 await connect(page,'l2');
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.getByLabel('Evidência direta da ferramenta')).toContainText('get_service_metrics');
 await expect(page.getByLabel('Evidência direta da ferramenta')).toContainText('não do runbook');
 await expect(page.locator('.source-panel')).not.toContainText('Runbook — latência em pagamentos');
 await expect(page.locator('.source-panel')).toContainText('DOCUMENTO');
 await page.getByLabel('Escopo dos documentos').selectOption('payments-api');
 await page.getByLabel('Serviço',{exact:true}).selectOption('payments-api');
 await page.locator('#question').fill('Como investigar latência na API de pagamentos?');
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.locator('.source-panel')).toContainText('Runbook — latência em pagamentos');
 await expect(page.locator('.source-panel')).not.toContainText('Runbook — erros na API de pedidos');
});
test('numeric verdict is computed independently and a contradictory model draft is withheld',async({page})=>{
 await connect(page,'l2');
 await page.route('**/api/chat',async route=>{
  const response=await route.fetch();const result=await response.json();
  // Exercise UI treatment of a server-blocked draft without executing an LLM in this browser suite.
  result.answer_validation={status:'blocked',reasons:['Contradição de teste'],scope:'Guard limitado'};
  result.answer='Resultado determinístico para revisão humana.';
  await route.fulfill({response,json:result});
 });
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.getByLabel('Comparação calculada pelo backend')).toContainText('4,8% > 2%');
 await expect(page.getByLabel('Comparação calculada pelo backend')).toContainText('Condição de investigação atendida');
 await expect(page.getByRole('alert')).toContainText('Rascunho do modelo retido');
});

test('governance shows six pillars and the active limits without granting operational access',async({page})=>{
 await connect(page,'l1');
 await page.getByRole('button',{name:'Governança',exact:false}).click();
 await expect(page.locator('.pillar-grid article')).toHaveCount(6);
 await expect(page.locator('.governance-view')).toContainText('16000 caracteres');
 await expect(page.locator('.governance-view')).toContainText('Diagnóstico operacional restrito');
 await expect(page.getByRole('button',{name:'Operação',exact:false})).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
test('operations displays measured outcomes after a query and preserves the collection window',async({page})=>{
 await connect(page,'l2');
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.locator('.response')).toBeVisible();
 await page.getByRole('button',{name:'Operação',exact:false}).click();
 await expect(page.locator('.ops-window')).toContainText('Processo');
 await expect(page.locator('.metric-grid')).toContainText('Taxa de sucesso');
 await expect(page.locator('.request-history article').first()).toContainText('Concluída');
 await expect(page.locator('.execution-health')).toContainText('execuções finalizadas');
 await page.getByRole('button',{name:'Governança',exact:false}).click();
 await page.getByRole('button',{name:'Consultar capacidade e modelos'}).click();
 await expect(page.locator('.governance-view')).toContainText('Diagnóstico de modelos locais disponível apenas para Ollama.');
});

test('compact view fits the three overview sections and preserves access to full details',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 await connect(page,'l2');
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.getByLabel('Comparação calculada pelo backend')).toBeVisible();
 await page.getByRole('button',{name:'Visão compacta',exact:true}).click();
 await expect(page.locator('.compact-mode')).toBeVisible();
 await expect(page.getByRole('banner',{name:'Sessão ativa'})).toContainText('Consulta nível 2');
 await expect(page.locator('.full-answer')).not.toHaveAttribute('open','');
 await expect(page.locator('.opening-label')).toContainText('Trecho inicial');
 await page.screenshot({path:'test-results/compact-investigation.png'});
 let bottom=await page.locator('.notice').evaluate(el=>el.getBoundingClientRect().bottom);
 expect.soft(bottom).toBeLessThanOrEqual(900);
 await page.getByRole('button',{name:'Governança',exact:true}).click();
 await expect(page.getByLabel('Visão compacta da governança')).toBeVisible();
 await expect(page.locator('.governance-overview .pillar-grid article')).toHaveCount(6);
 await expect(page.locator('.governance-overview')).toContainText('sem certificação');
 await page.screenshot({path:'test-results/compact-governance.png'});
 bottom=await page.locator('.governance-overview').evaluate(el=>el.getBoundingClientRect().bottom);
 expect.soft(bottom).toBeLessThanOrEqual(900);
 await page.getByRole('button',{name:'Arquitetura',exact:true}).click();
 await expect(page.getByLabel('Diagrama de componentes da solução')).toBeVisible();
 await page.screenshot({path:'test-results/compact-architecture.png'});
 bottom=await page.locator('.architecture-panel').evaluate(el=>el.getBoundingClientRect().bottom);
 expect.soft(bottom).toBeLessThanOrEqual(900);
 await page.getByRole('button',{name:'Sair da visão compacta',exact:true}).click();
 await expect(page.locator('.compact-mode')).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Conhecimento',exact:false})).toBeVisible();
});

test('compact model response with usage fits and full text remains available',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 await connect(page,'l2');
 const fullText='## Resumo\n\n'+('Investigue a taxa de erros e compare as evidências autorizadas antes de propor qualquer mitigação. '.repeat(8))+'FINAL-DO-TEXTO';
 await page.route('**/api/chat',async route=>{
  const response=await route.fetch();const result=await response.json();
  // Layout-only fixture: not a model evaluation or measured token benchmark.
  result.answer=fullText;result.provider='ollama';result.chat_model='layout-fixture';
  result.usage={input_tokens:1294,output_tokens:267,output_tokens_per_second:9.78,cost_estimate:null};
  await route.fulfill({response,json:result});
 });
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Investigar →',exact:true}).click();
 await expect(page.locator('.response').first()).toContainText('Investigue');
 await page.getByRole('button',{name:'Visão compacta',exact:true}).click();
 await expect(page.locator('.usage-metrics')).toContainText('1294');
 expect(await page.locator('.notice').evaluate(el=>el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(900);
 await expect(page.locator('.answer-panel>.response')).toContainText('…');
 await page.locator('.full-answer>summary').click();
 await expect(page.locator('.full-answer')).toContainText('FINAL-DO-TEXTO');
});

test('governance pillars have distinct visual identities and policies live in performance',async({page})=>{
 await connect(page,'l2');
 await page.getByRole('button',{name:'Governança',exact:false}).click();
 const grid=page.locator('.governance-full .pillar-grid');
 await expect(grid.locator(':scope > article')).toHaveCount(6);
 const colors=await grid.locator(':scope > article').evaluateAll(elements=>elements.map(el=>getComputedStyle(el).backgroundColor));
 expect(new Set(colors).size).toBe(6);
 const performance=grid.locator('[data-pillar="performance"]');
 await expect(performance.getByLabel('Políticas aplicadas no backend')).toBeVisible();
 await expect(performance.locator('.policy-values')).toContainText('30 / min');
 await expect(performance.locator('.policy-values')).toContainText('16000 caracteres');
 await expect(page.locator('.governance-full > section').filter({hasText:'POLÍTICAS APLICADAS NO BACKEND'})).toHaveCount(1);
 await performance.getByText('Escopo das políticas',{exact:true}).click();
 await expect(performance).toContainText('retorna 429');
});

test('reference playbooks expose proposed triggers without claiming active fallback or autoscaling',async({page})=>{
 await connect(page,'l2');
 await page.getByRole('button',{name:'Governança',exact:false}).click();
 const grid=page.locator('.governance-full .pillar-grid');
 const reliability=grid.locator('[data-pillar="reliability"]');
 await reliability.locator('.pillar-reference>summary').click();
 await expect(reliability.locator('.reference-warning').first()).toContainText('não estão ativos');
 await reliability.getByText('Dois modelos e circuit breaker',{exact:true}).click();
 await expect(reliability.locator('.reference-model-plan')).toContainText('não estão implementados');
 await expect(reliability.locator('.reference-model-plan')).toContainText('qwen2.5:1.5b');
 await expect(reliability.locator('.reference-model-plan')).toContainText('demo sem LLM ativo');
 await reliability.getByText('Métricas e gatilhos propostos',{exact:true}).click();
 await expect(reliability.locator('.reference-trigger').first()).toContainText('5 falhas transitórias');
 const performance=grid.locator('[data-pillar="performance"]');
 await performance.locator('.pillar-reference>summary').click();
 await performance.getByText('Escalabilidade e elasticidade',{exact:true}).click();
 await expect(performance).toContainText('Compose atual não cria ou remove réplicas automaticamente');
 const cost=grid.locator('[data-pillar="cost"]');
 await cost.locator('.pillar-reference>summary').click();
 await cost.getByText('Orçamento e elasticidade de custos',{exact:true}).click();
 await expect(cost).toContainText('Ainda não bloqueiam gasto');
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('compact workspace uses wide screens and expanded pillars do not stretch siblings',async({page})=>{
 await page.setViewportSize({width:1920,height:1080});
 await connect(page,'l2');
 await page.getByRole('button',{name:'Visão compacta',exact:true}).click();
 const main=page.locator('.compact-mode>main');
 const bounds=await main.boundingBox();
 expect(bounds!.width).toBeGreaterThanOrEqual(1900);
 await page.getByRole('button',{name:'Governança',exact:true}).click();
 const grid=page.locator('.governance-overview .pillar-grid');
 await expect(grid.locator(':scope > article')).toHaveCount(6);
 const operations=grid.locator('[data-pillar="operations"]');
 const security=grid.locator('[data-pillar="security"]');
 await operations.locator('.pillar-reference>summary').click();
 await operations.getByText('Métricas e gatilhos propostos',{exact:true}).click();
 const heights=await Promise.all([operations,security].map(locator=>locator.evaluate(el=>el.getBoundingClientRect().height)));
 expect(heights[0]).toBeGreaterThan(heights[1]+100);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('header downloads the entire expanded page as JPEG and restores the workspace',async({page},testInfo)=>{
 await page.setViewportSize({width:1440,height:900});
 await connect(page,'l2');
 await page.getByRole('button',{name:'Visão compacta',exact:true}).click();
 await page.getByRole('button',{name:'Governança',exact:true}).click();
 const details=page.locator('[data-pillar="operations"] .pillar-reference').first();
 await details.locator(':scope > summary').click();
 await page.locator('[data-pillar="operations"]').getByText('Métricas e gatilhos propostos',{exact:true}).click();
 const height=await page.locator('.shell').evaluate(el=>el.scrollHeight);
 expect(height).toBeGreaterThan(900);
 const button=page.getByRole('button',{name:'Baixar página completa em JPG'});
 const pending=page.waitForEvent('download');
 await button.click();
 const download=await pending;
 expect(download.suggestedFilename()).toMatch(/^enterprise-ai-workbench-.*\.jpg$/);
 const file=testInfo.outputPath('full-page.jpg');
 await download.saveAs(file);
 const {readFile}=await import('node:fs/promises');
 const bytes=await readFile(file);
 expect([...bytes.subarray(0,3)]).toEqual([255,216,255]);
 const dimensions=await page.evaluate(async data=>{
  const image=await createImageBitmap(new Blob([new Uint8Array(data)],{type:'image/jpeg'}));
  return {width:image.width,height:image.height};
 },[...bytes]);
 expect(dimensions.height).toBeGreaterThan(height-2);
 expect(dimensions.width).toBeGreaterThanOrEqual(1440);
 await expect(button).toBeEnabled();
 await expect(details).toHaveAttribute('open','');
 expect(await page.locator('.shell').evaluate(el=>el.classList.contains('page-export')||(el as HTMLElement).inert)).toBeFalsy();
});
