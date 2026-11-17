# Qual técnica usar — e quando dispensar IA

| Necessidade | Primeira opção | Trade-off |
|---|---|---|
| Campo obrigatório, limite fixo, roteamento previsível | Código e regras | Fácil de testar; não aprende padrões |
| Anomalia em uma série de métricas | Estatística ou ML tradicional | Exige histórico, baseline e avaliação de falsos positivos |
| Resumir texto já fornecido | LLM com contexto controlado | Variabilidade, custo e revisão |
| Responder usando documentos atualizados | RAG | Depende de qualidade, acesso e atualização da recuperação |
| Consultar um estado atual do sistema | API/ferramenta, opcionalmente MCP | O contrato da ferramenta e a identidade continuam necessários |
| Mudar comportamento/estilo do modelo | Prompts e avaliação primeiro; fine-tuning se justificado | Fine-tuning não substitui acesso atualizado a documentos |
| Executar ação com efeito financeiro/operacional | Fluxo determinístico e aprovação | LLM não é autoridade de permissão |

## Por que RAG + MCP aqui

RAG fornece trechos de runbooks autorizados. MCP padroniza o contrato de ferramentas e permite demonstrar interoperabilidade com um cliente local. Não substitui embeddings, autorização, banco ou observabilidade.

A aplicação não exige um LLM com tool calling: a pessoa pede explicitamente métricas e o backend executa a ferramenta permitida. Isso reduz variabilidade e facilita comparar modelos pequenos. O LLM recebe somente evidências e não possui interface de execução.

## Modelos locais versus API

Local oferece controle do ambiente e pode permitir operação sem egress após provisionamento; exige capacidade, manutenção e avaliação. API simplifica capacidade e acesso a modelos, mas envia dados ao provedor e introduz custo variável e dependência externa. Não há um vencedor universal.

No laboratório, chat e embeddings usam o mesmo tipo de provedor. Separar provedores para embeddings locais e geração remota é uma evolução possível, mas exige política de dados e configuração própria. A chave de namespace inclui provedor e modelo de embedding. Se trocar pesos/dimensão de um modelo sob o mesmo nome, planeje namespace novo e reindexação.

## ML tradicional: etapa seguinte

Começar com limite fixo e baseline estatístico. Só depois experimentar detecção de anomalias sobre série sintética versionada. Medir precision, recall, falsos alertas e latência de detecção. O LLM explica o sinal junto ao runbook; não inventa o cálculo nem substitui o detector.
