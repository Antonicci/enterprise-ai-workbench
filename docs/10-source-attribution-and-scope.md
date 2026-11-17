# Atribuição de fontes e escopo documental

## Problema observado

Na demonstração, o modelo atribuiu ao runbook a taxa observada de 4,8%, que veio do MCP. O runbook contém um limiar de 2% por 5 minutos. Também foram recuperados documentos de pagamentos numa pergunta sobre pedidos, e a resposta negou a existência de verificações que constavam no documento.

## Alterações

1. **Escopo por metadados:** documentos declaram services: orders-api, payments-api, ambos ou lista vazia para procedimentos gerais. O filtro de serviço e o filtro de acesso são aplicados antes do ranking/top-k, em memória e PostgreSQL. Escopo não substitui autorização.
2. **Roteamento explícito:** a UI permite automático, pedidos, pagamentos ou todos os serviços autorizados. Automático reconhece nomes de serviços e termos portugueses de pedidos/pagamentos; em caso ambíguo usa contexto amplo, ou o serviço MCP selecionado. Não é um classificador universal. Pergunta e serviço MCP contraditórios pedem ajuste, em vez de misturar medições silenciosamente.
3. **Proveniência tipada:** o prompt recebe documents e tool_results separados. Cada registro tem source_type e source_id; medições da ferramenta recebem mcp:get_service_metrics, janela temporal e indicador sintético. Similaridade não é entregue ao modelo como fato de negócio.
4. **Regras de resposta:** orientações/limiares devem citar o documento, observações devem citar MCP; comparação deve citar ambos e respeitar a janela. Não afirmar ausência de instruções quando elas estão no contexto.
5. **Evidência visual independente:** o painel FONTE MCP apresenta os números diretamente do retorno da ferramenta, separado do texto gerado. As fontes documentais têm rótulo DOCUMENTO e escopo. O texto do LLM continua sujeito a revisão.

## Comparação correta do caso

- Documento orders-runbook-1: o limiar para investigação é taxa acima de 2% por 5 minutos; verificar dependências, mudanças recentes, pool e timeouts.
- Ferramenta mcp:get_service_metrics: observação sintética de 4,8%, p95 1450 ms, janela de 5 minutos.
- Interpretação: o sinal simulado excede o limiar documental na mesma janela. Isso não identifica a causa raiz e não autoriza intervenção automática.

## Dados existentes

Em memória, o corpus é recriado no restart. Em PostgreSQL, uma migração apenas de metadados adiciona services, associa os dois runbooks conhecidos aos respectivos serviços e mantém documentos particulares como gerais. Preserva texto editado, nível de acesso e vetores. Alterações explícitas posteriores para Geral não são revertidas no startup. O gestor pode revisar a aplicabilidade na biblioteca.

Não é necessário apagar volumes ou reingerir todo o corpus para essa alteração de metadados.

## O que os testes comprovam

Filtros anteriores ao top-k mesmo com vetor irrelevante de maior score; bloqueio de documento restrito; escolha de escopo; rejeição de conflito entre pergunta e métricas; separação do contexto enviado ao provedor; preservação de dados na migração; rótulos e escopos no navegador. O smoke real usa Qwen 3B em CPU e inclui saída para revisão manual.

Não existe verificador semântico automático de todas as frases do modelo. O prompt e a recuperação reduzem os erros observados, mas não garantem ausência de alucinações, citações erradas ou omissões. Não apresentamos esse teste como nota de groundedness, garantia universal ou benchmark de GPU.
