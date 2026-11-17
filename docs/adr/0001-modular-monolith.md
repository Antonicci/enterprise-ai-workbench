# ADR 0001 — Monólito modular e execução explícita de ferramentas

Status: aceito para o laboratório v0.1.

## Contexto

Precisamos demonstrar arquitetura de IA com hardware limitado, execução reproduzível e fronteiras compreensíveis. Uma plataforma distribuída ou agente universal ampliaria o esforço antes de validar utilidade.

## Decisão

Frontend React separado, backend FastAPI modular, LangChain somente nos adaptadores, MCP stdio para ferramentas locais. Pessoa solicita métricas explicitamente; backend autoriza e executa. Modelo não possui ferramentas. PostgreSQL com pgvector é opção persistente; memória permite demonstração sem infraestrutura.

## Alternativas

- Microserviços: independência de escala, mas custo de rede, identidade e operação desnecessários nesta etapa.
- Banco vetorial dedicado: pode atender escala e recursos próprios; introduz outro banco e sincronização de permissões.
- Agente autônomo com tool calling: maior flexibilidade; exige modelos capazes, budgets, autorização por chamada e avaliação de loops.
- MCP remoto: interoperabilidade de rede; exige autenticação, autorização, transporte e gestão de sessão específicos.

## Consequências

Fácil reprodução e teste. O processo MCP por chamada custa startup; conexão persistente fica para uma evolução. Memória não escala entre workers. Biblioteca de modelos pode ser substituída sem mudar políticas. Suporte a API compatível não implica suporte universal a qualquer provedor.
