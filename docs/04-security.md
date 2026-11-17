# Segurança e modelo de ameaças

## Implementado no laboratório

- Bearer obrigatório nos endpoints de negócio. Tokens são comparados no servidor; grupos não são aceitos do cliente.
- Ingestão e métricas exigem operations. Ingestão só pode atribuir grupos pertencentes ao autor.
- Documento é visível quando pelo menos um grupo coincide. Aplicar esse filtro antes de construir contexto é obrigatório.
- Restrição equivalente dentro do servidor MCP; esconder um botão não é controle de segurança.
- Ferramentas de leitura com serviços em allowlist. Nenhum shell, URL, comando ou servidor arbitrário vindo do usuário.
- Pergunta limitada a 2.000 caracteres; texto por documento limitado a 30.000; corpo no Nginx limitado a 256 KB.
- SQL parametrizado; namespaces de vetores por provedor/modelo; transação na substituição.
- UI renderiza texto com escape do React. Tokens somente em memória; sem dependências externas de fontes/scripts.
- Logs registram IDs, duração e contagens, sem conteúdo e sem credenciais. Falhas devolvem mensagem genérica e trace.
- Portas Compose publicadas somente em loopback. Banco não é publicado no host. Contêiner backend sem root.

## Ameaças e risco residual

| Ameaça | Controle atual | Risco residual / próximo controle |
|---|---|---|
| Vazamento entre grupos | Filtro antes do ranking, testes negativos | Um administrador de banco pode ler tudo; adotar RLS e isolamento de tenant |
| Prompt injection documental | Instrução de sistema e modelo sem ferramentas | Modelo pode obedecer texto malicioso; exigir red team, detecção e revisão |
| Confused deputy MCP | Host fornece token e servidor valida grupo | Processo local herda a identidade do host; remoto exige OAuth/autorização por usuário |
| Extração de segredos | Nenhum segredo no contexto; logs minimizados | Dependências/provedores podem registrar telemetria; revisar egress e retenção |
| Negação de serviço/custo | Limites textuais e timeout | Sem quotas, fila ou rate limiting; threads podem continuar após timeout |
| Conteúdo malicioso/XSS | Renderização como texto; headers Nginx | Validação de build e dependências continua necessária |
| Corpus contaminado | Escrita restrita a operações | Autor autorizado ainda pode inserir conteúdo errado; adicionar revisão e proveniência |
| Roubo de token | Memória no browser e loopback | Tokens estáticos não expiram; substituir por SSO/OIDC e TLS |

## Antes de dados corporativos

1. Classificar dados e aprovar finalidade, base de tratamento, residência e retenção com responsáveis.
2. Integrar IdP: validar assinatura, issuer, audience, expiração e mapear grupos no servidor. Não confiar em JWT apenas decodificado.
3. Separar identidades de aplicação, banco, ingestão e conectores. Segredos em cofre; rotação e revogação.
4. Aplicar TLS, rede privada, egress em allowlist, quotas e autorização por documento/tenant em todos os conectores.
5. Definir exclusão de documentos, vetores, backups e logs. Embeddings também são dados derivados que exigem proteção.
6. Implementar auditoria durável com política de retenção e acesso; testar restauração.
7. Avaliar exfiltração, prompt injection, tool poisoning, acesso cruzado e falhas dos provedores.
8. Só adicionar ações após autorização determinística, confirmação específica, idempotência e estratégia de recuperação.

## Offline

PROVIDER=ollama não prova ausência de egress. Auditar imagens, modelos, telemetria, DNS e chamadas de dependências. Embeddings, geração e conectores devem permanecer locais. Provisionamento inicial requer downloads. Nenhum fallback remoto silencioso é permitido.

Não reporte vulnerabilidades contendo dados ou tokens reais em uma issue pública. Este repositório não oferece SLA de segurança ou certificação de conformidade.
