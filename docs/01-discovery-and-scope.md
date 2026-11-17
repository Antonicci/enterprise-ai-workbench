# Discovery e análise de escopo

## Caso de negócio

Um analista precisa reunir runbooks e sinais operacionais para investigar falhas. O custo atual é o tempo de localizar documentos, conferir acesso e reconstruir contexto. O assistente oferece evidências; o responsável decide e executa a mitigação fora deste laboratório.

| Pergunta de discovery | Resposta do laboratório | Decisão necessária na empresa |
|---|---|---|
| Quem usa? | employees e operations | Personas, grupos no IdP e responsáveis |
| Qual decisão é apoiada? | Próximos passos de investigação | Risco de resposta incorreta e aprovação |
| Que dados entram? | Runbooks e métricas sintéticas | Classificação, consentimento, retenção e residência |
| Quais integrações? | MCP local somente leitura | Dono, contrato, SLA e permissões por integração |
| Como medir valor? | Qualidade de recuperação e tempo da consulta | Tempo de investigação antes/depois e adoção |
| Qual orçamento? | Laboratório sem compromisso de SLA | Tokens, embeddings, banco, GPU e operação |
| Pode sair da rede? | Configurável local/API | Egress permitido e termos do provedor |

## Dentro da v0.1

Consulta textual, ingestão de texto, grupos definidos no servidor, corpus pequeno, fontes com IDs, métricas sintéticas MCP, troca de provedor, busca em memória ou pgvector, interface e documentação reproduzível.

## Fora da v0.1

Remediação automática, agentes autônomos, leitura arbitrária de disco/URLs, múltiplos tenants, conector de SharePoint, PDF/OCR, produção de alertas contínuos, SLA, treinamento ou fine-tuning.

## Critérios de aceitação

- Analista consulta documentos employees e não recebe marcador restrito, nem no contexto do provedor.
- Operações consulta o documento restrito e solicita métricas por MCP.
- Chamadas diretas à API não contornam os controles da interface.
- Modelo e embeddings podem ser configurados sem alterar regras de autorização.
- Falha do provedor gera erro explícito, sem resposta fabricada de contingência.
- A demonstração declara dados sintéticos e distingue recuperação lexical de semântica.

## Evolução de escopo

Só adicionar um conector quando houver caso de uso, dono, autorização, contrato e critério de avaliação. Um novo modelo exige comparar qualidade, latência, custo e capacidade de executar com os dados permitidos. Uma ação de escrita exige análise de impacto, idempotência, aprovação e recuperação. Não transformar uma ferramenta de estudo em ambiente corporativo apenas trocando credenciais.
