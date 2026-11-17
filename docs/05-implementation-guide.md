# Implementação corporativa passo a passo

Este guia distingue o laboratório executável dos controles que uma empresa precisa implementar. Não representa aprovação para produção.

## 1. Descobrir e aprovar o caso

Preencha escopo, personas, fontes, classificação de dados e risco de resposta errada. Escolha uma tarefa mensurável e um responsável de negócio. Entregável: escopo aprovado e casos de aceitação, incluindo negações de acesso.

## 2. Selecionar a abordagem

Use a matriz de técnicas. Compare busca convencional, regra e RAG. Para monitoramento, comece com limiares e dados históricos. Entregável: ADR com alternativas, custo esperado e restrições.

## 3. Validar o ambiente demo

Siga o README sem alterar o provedor. Verifique analyst versus operations, ingestão e MCP. Use apenas dados sintéticos. Entregável: execução reproduzível e testes passando.

## 4. Ativar o provedor e a persistência

Baixe modelos locais ou obtenha endpoint corporativo aprovado. Escolha chat e embedding separadamente pelo propósito. Gere credenciais de laboratório novas, configure `.env` e inicie o PostgreSQL antes do backend. Nunca versione `.env`.

Exemplo de geração de token: `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Gere dois valores e atribua os grupos no JSON AUTH_TOKENS. O laboratório rejeita credenciais com prefixo demo- quando o provedor real é ativado.

Teste a implantação com o mesmo corpus. Se o endpoint não suportar embeddings e chat nos contratos configurados, escreva um adaptador e testes de contrato. Não use fallback remoto para contornar uma falha local sem aprovação.

## 5. Integrar identidade e dados

Substitua tokens por validação OIDC. Preserve identidade até a recuperação e as ferramentas. Mapeie permissões da fonte; nunca torne documento amplo por falta de metadados. Configure tenant como dimensão independente de grupo antes de qualquer uso multitenant.

A v0.1 aceita texto via API/UI. Para PDFs, SharePoint e outros conectores, implemente extração, proveniência, detecção de mudanças, remoção, revisão e política de acesso. O indexador precisa de uma identidade própria e escopo mínimo.

## 6. Avaliar antes de disponibilizar

Monte um conjunto representativo de perguntas com fontes e respostas esperadas. Separe desenvolvimento e validação. Compare recuperação, groundedness, abstinência, segurança e custo. Registre modelo, versão, corpus e configuração. Entregável: relatório de aprovação ou lista de lacunas.

## 7. Operar um piloto limitado

Use grupo pequeno, quotas, métricas técnicas e feedback. Configure logs duráveis, alertas, política de retenção, backups e responsáveis. Teste falha do modelo, embeddings e banco. Defina como suspender ingestão e consultas durante incidente.

## 8. Expandir somente com evidências

Amplie corpus, conectores ou automação após demonstrar valor e manter os critérios de segurança. Ações operacionais devem aparecer como proposta com impacto, parâmetros e aprovação. Não tratar uma recomendação textual como uma mudança executada.

## Configuração da v0.1

| Variável | Uso |
|---|---|
| PROVIDER | demo, ollama, openai-compatible |
| STORE | memory ou postgres |
| AUTH_TOKENS | JSON token → grupos, resolvido no servidor |
| CHAT_MODEL / EMBEDDING_MODEL | Identificadores dos modelos |
| OLLAMA_BASE_URL | Endpoint local, definido pelo administrador |
| API_BASE_URL / API_KEY | Endpoint corporativo compatível e segredo |
| DATABASE_URL | DSN PostgreSQL; não expor no frontend |
| TOP_K | 1–10 trechos por consulta |
| REQUEST_TIMEOUT | 1–180 s; limite do fluxo, não uma quota global |

## Recuperação e troubleshooting

- **401:** confirme token e AUTH_TOKENS. Não envie a credencial em issue.
- **403:** verifique grupos; não altere autorização para contornar erro.
- **503:** use trace e logs locais; confira modelo baixado, endpoint, rede e banco. Erros detalhados não são expostos ao usuário.
- **Startup falha:** banco indisponível, modelo de embeddings ausente ou configuração inválida. O startup reindexa o corpus, portanto depende de embeddings no modo real.
- **Documento desapareceu:** memória é volátil; IDs do corpus são restaurados no startup. Use IDs novos e PostgreSQL para persistência.
- **Vetores incompatíveis:** reindexe em namespace novo ao trocar pesos/dimensão; não compare embeddings de modelos diferentes.
