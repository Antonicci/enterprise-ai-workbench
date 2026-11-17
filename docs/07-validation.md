# Evidências de validação

Primeira validação: 17/11/2026. Ambiente: Python 3.12 e Node 24. Dependências Python registradas em backend/requirements.lock; frontend em package-lock.json.

| Verificação | Resultado local |
|---|---|
| Autenticação e negação de acesso | Testes automatizados |
| Documento restrito ausente do contexto do modelo para analyst | Teste automatizado que captura os trechos enviados |
| Métricas negadas antes de chamar MCP | Teste negativo com verificação da chamada |
| Ingestão, troca de grupos e substituição | Testes automatizados |
| Falha do provedor sem exposição de detalhes | Teste automatizado |
| Limites de entrada e serviço em allowlist | Testes automatizados |
| MCP handshake, descoberta e chamada por stdio | Testes reais do protocolo em subprocesso |
| Adaptadores Ollama e API compatível | Contratos HTTP testados contra servidor local simulado |
| Build TypeScript e Vite | Executado com sucesso |
| PostgreSQL + pgvector | Teste de integração disponível; não executado localmente por ausência do banco |
| Docker Compose | Arquivos preparados; Docker indisponível neste ambiente |
| Geração com Ollama/GPU ou API corporativa real | Não executada; requer modelos/endpoint |
| Inspeção visual e fluxo de navegador | Não concluídos: o navegador local não iniciou por restrição de socket do ambiente |

Suite inicial: **12 testes passando e 1 teste PostgreSQL ignorado** quando TEST_DATABASE_URL não é definido. O workflow do GitHub está configurado para executar também o teste PostgreSQL com serviço pgvector. O resultado do workflow deve ser consultado em Actions; a configuração não é prova de aprovação.

Os testes de contrato não comprovam qualidade semântica, desempenho, compatibilidade com todo provedor ou segurança contra prompt injection. Ainda é necessário executar o laboratório na máquina de destino, revisar a interface e publicar avaliação real antes de apresentar resultados de modelo.
