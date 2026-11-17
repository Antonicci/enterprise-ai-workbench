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
 await expect(page.getByLabel('Permissões atuais')).toBeVisible();
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
 await page.getByRole('button',{name:'Observabilidade',exact:false}).click();
 await page.getByRole('button',{name:'Consultar métricas do assistente'}).click();
 await expect(page.getByText('✓ get_ai_quality_metrics', {exact:false})).toBeVisible();
 await page.getByRole('button',{name:'Arquitetura',exact:false}).click();
 await page.getByRole('button',{name:'Login e acesso',exact:true}).click();
 await page.getByRole('button',{name:'API e políticas',exact:true}).click();
 await expect(page.locator('.component-detail')).toContainText('Resolve perfil no servidor');
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
