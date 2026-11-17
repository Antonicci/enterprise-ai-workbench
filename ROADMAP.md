# Roadmap

## v0.1 — Fundamento executável

- [x] Frontend e API; ingestão de texto e consulta com fontes.
- [x] Demo extrativa sem modelo; adaptadores Ollama e API compatível.
- [x] Memória e PostgreSQL + pgvector; filtro de grupos.
- [x] MCP stdio real: busca documental e métricas sintéticas.
- [x] Documentação corporativa, decisões e testes de autorização.

## v0.2 — Qualidade e operação

- [ ] Executar e publicar benchmark de modelos na RTX 4050, sem estimativas apresentadas como resultado.
- [ ] Corpus de avaliação versionado e relatório de recuperação/geração.
- [x] OIDC/Keycloak, três perfis, edição e autorização por ferramenta.
- [x] Mapa interativo de componentes e contadores medidos do assistente.
- [ ] Rate limiting, concorrência limitada e tracing distribuído.
- [ ] Ingestão assíncrona, exclusão, proveniência e versionamento.
- [x] CI com PostgreSQL, MCP e cenários de navegador demo/OIDC.
- [ ] Testes de carga e falhas de infraestrutura.

## v0.3 — Monitoramento e interoperabilidade

- [ ] Série sintética temporal, regras e detector de anomalias comparados.
- [ ] Conector de observabilidade somente leitura, com ambiente de teste.
- [ ] Revisar SDK MCP v2 e requisitos para transporte remoto autenticado.
- [ ] Adaptadores específicos para provedores corporativos conforme demanda.

## Etapa posterior — Ações governadas

- [ ] Proposta de ação com aprovação específica, idempotência e trilha durável.
- [ ] Integração ITSM em sandbox; sem remediação automática na infraestrutura real.
- [ ] Página de estudo no site do Studio e vídeo com evidências de execução.
