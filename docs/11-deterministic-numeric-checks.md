# Comparação numérica determinística e retenção de rascunho

## Caso observado

O modelo afirmou que 4,8% estava dentro do limiar documental de 2%. O sistema passa a calcular essa relação com Decimal no backend: **4,8% > 2%**, diferença de **2,8 pontos percentuais**, na mesma janela de 5 minutos. O modelo recebe o resultado; não é a autoridade para decidir a comparação.

## Escopo deliberadamente limitado

A v0.3 reconhece uma forma controlada de frase afirmativa completa em trechos recuperados:

> Uma taxa de erros acima de X% por Y minutos exige investigação.

X aceita ponto ou vírgula decimal, entre 0 e 100; Y é inteiro entre 1 e 1440. Não é um parser geral de políticas, não interpreta sinônimos arbitrários nem extrai regras de texto livre com um segundo LLM. Formulações não reconhecidas não são calculadas. Uma evolução corporativa deveria manter regras tipadas, versionadas e aprovadas pelo dono do runbook.

A regra só é considerada se estiver num trecho já recuperado e autorizado, com serviço compatível com a medição MCP. Não consulta documentos ocultos para completar uma regra. Janela diferente, medição ausente/inválida e regras conflitantes não geram uma conclusão de investigação. O operador é estritamente acima: igualdade a 2% não satisfaz >2%.

## Proveniência

Cada comparação retorna documento, trecho exato da regra, fonte MCP, valor observado, limiar, janela, relação e diferença em pontos percentuais. O indicador de dados sintéticos é preservado. Não conclui causa raiz e não executa intervenção.

## Guard do texto gerado

Depois da geração, há uma detecção conservadora e limitada:

- Para taxa de erros calculada acima do limiar, identifica formulações como dentro deste limiar e abaixo do limite, com tratamento de negação simples.
- Verifica comparações matemáticas explícitas envolvendo os dois valores reconhecidos, como 4,8% < 2%.
- Quando encontra conflito, não retorna o rascunho ao cliente; entrega o relatório determinístico e um aviso de revisão humana.

Não é validação semântica completa. Pode deixar passar paráfrases não reconhecidas e pode reter citações/negações complexas que não sejam realmente contraditórias. O estado no_known_conflict significa apenas que os padrões implementados não encontraram conflito; não é selo de correção da resposta. O texto retido não é colocado em logs.

## Interface

O bloco REGRA + MEDIÇÃO mostra o cálculo do backend e as duas fontes. A resposta mantém aviso de revisão. Se o rascunho for retido, há um aviso explícito e o texto incorreto não é apresentado como análise aprovada. A linha de execução distingue geração de verificação numérica.

## Regressões

Os testes cobrem 4,8 versus 2, igualdade, abaixo, decimais, medição inválida, janela incompatível, outro serviço, regra não reconhecida, negação no documento, conflito entre fontes, saída incorreta fornecida pelo modelo e ausência de fontes recuperadas. A interface é exercitada também com uma resposta retida. Nenhum desses testes é nota global de qualidade de LLM.


## Apresentação e fidelidade textual

O adaptador remove uma cerca externa única `markdown`, `md` ou sem linguagem que envolva toda a resposta. Blocos internos, outras linguagens e cercas incompletas permanecem intactos. Essa normalização só altera a apresentação, sem reescrever afirmações.

O prompt pede recomendações sem alegar execução, proíbe inventar remoção de senhas e distingue aprovação operacional de ausência de capacidade de execução neste laboratório. Também atribui a comparação ao backend, enquanto o MCP fornece medições. São instruções ao modelo, não uma garantia nem um filtro semântico de todas as afirmações. A proteção determinística continua restrita aos padrões numéricos documentados acima.
