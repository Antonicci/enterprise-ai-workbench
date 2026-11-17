# Discovery e escopo — v0.2

O caso é apoiar investigação de incidentes com runbooks autorizados e sinais operacionais. O assistente reúne evidências; a pessoa decide e executa a mitigação fora do laboratório.

## Perguntas antes da implementação

Quem consulta? Quem edita? Quais documentos são restritos? Quais ferramentas cada perfil pode chamar? Quais dados podem sair da rede? Como medir tempo economizado e risco de resposta errada? Quem aprova mudanças de acesso e quais ações exigem aprovação humana?

## Escopo entregue

Três perfis, tokens demo ou OIDC/Keycloak, fontes nível 1/2, biblioteca com edição, resposta extrativa ou adaptadores LLM, RAG, ferramentas MCP de leitura, contadores medidos do assistente e mapa visual. Sem automação de remediação ou monitoramento contínuo.

## Critérios de aceitação

- Consulta1 não recebe documentos nível2 em listagem, leitura direta ou contexto do modelo.
- Consulta2 lê ambos os níveis e métricas, sem escrita documental.
- Gestor inclui/edita/classifica ambos os níveis, sem métricas operacionais.
- OIDC valida token e não aceita fallback demo. Permissões do cliente não são confiadas.
- Ferramentas verificam identidade novamente no worker da mesma aplicação.
- Mudança de classificação remove o documento do acesso anterior na recuperação seguinte.
- UI separa métrica sintética, contador medido e qualidade/custo não medidos.

Fora do escopo: multitenancy, RLS, ações externas, PDF/OCR, fine-tuning, detector preditivo, auditoria imutável e SLA. Entra ID tem guia e fronteira configurável; validação com tenant real é uma etapa própria.
