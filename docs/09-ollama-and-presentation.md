# Ollama e apresentação visual — v0.3

## Objetivo

Executar geração e embeddings reais e tornar as evidências legíveis na demonstração: perfil conectado, modelo ativo, fontes autorizadas, ferramenta MCP e tempos medidos. O modo apresentação apenas reorganiza a tela. Não muda permissões, não simula tráfego e não fabrica indicadores.

## Executar no Windows / Docker Desktop

Com Git atualizado e o `.env` já existente, na raiz do projeto:

```powershell
git pull --ff-only
docker compose -f compose.yaml -f compose.oidc.yaml -f compose.ollama.yaml up --build
```

O serviço ollama-models baixa o modelo CHAT_MODEL e o EMBEDDING_MODEL antes de iniciar o backend. No exemplo, qwen2.5:3b e nomic-embed-text. O primeiro download pode demorar; os arquivos ficam no volume ollamadata e são reutilizados. Ollama não publica porta no host: o backend usa http://ollama:11434 na rede Docker.

O exemplo usa imagem oficial ollama/ollama:latest para laboratório. A tag é mutável; registre versão e inventário após provisionar e fixe versão/digest antes de exigir reprodução estrita.

Para a RTX 4050 NVIDIA, se o Docker Desktop / WSL2 já tiver suporte de GPU configurado:

```powershell
docker compose -f compose.yaml -f compose.oidc.yaml -f compose.ollama.yaml -f compose.gpu.yaml up --build
```

Se o Docker rejeitar o dispositivo, execute sem compose.gpu.yaml para CPU ou configure o suporte NVIDIA/WSL2 primeiro. Não concluímos que a GPU está sendo usada apenas por escolher esse arquivo. Verifique:

```powershell
docker compose -f compose.yaml -f compose.oidc.yaml -f compose.ollama.yaml exec ollama ollama ps
docker compose -f compose.yaml -f compose.oidc.yaml -f compose.ollama.yaml exec ollama ollama --version
```

Execute ollama ps durante ou logo após uma consulta para conferir o processador/modelo carregado. O benchmark da sua máquina ainda precisa ser realizado. A configuração inicial limita contexto a 4096 e saída a 512 tokens; não garante determinada latência ou consumo de VRAM.

## Caso Ollama já esteja instalado no Windows

Não é necessário outro servidor. Baixe os dois modelos no host, configure PROVIDER=ollama e OLLAMA_BASE_URL=http://host.docker.internal:11434 no `.env` e execute apenas compose.yaml + compose.oidc.yaml. Não acrescente compose.ollama.yaml nesse cenário, pois ele aponta explicitamente para o serviço em contêiner. Valide acesso pela rede Docker sem expor o daemon à internet.

## Confirmação na interface

Abra http://localhost:8080, atualize com Ctrl+F5 e entre como consulta2. Confira o modelo ativo e o indicador **LLM via Ollama**. Se ainda aparecer extractive-demo, a aplicação ainda está no modo demo ou usa contêiner/build anterior.

Pergunta de demonstração:

> A API de pedidos apresenta erros HTTP 500. Consulte as métricas e o runbook, diferencie evidências de hipóteses e proponha os próximos passos sem executar alterações.

Habilite MCP e investigue. A resposta é gerada pelo modelo. As métricas do serviço continuam sintéticas. As fontes são trechos recuperados, não confirmação automática de todas as afirmações da resposta.

## Persistência de conhecimento

O namespace de embeddings muda ao trocar demo por Ollama. Documentos particulares precisam ser reingeridos com o novo modelo. O corpus sintético é indexado automaticamente. Memória continua volátil. Para PostgreSQL, use STORE=postgres e inicie o serviço db com --profile vector antes do backend, conforme README; os modelos do Ollama permanecem em volume independente.

## Tempos medidos

O backend mede recuperação (inclui embedding da pergunta e busca), chamada MCP se solicitada e composição/geração. A UI exibe esses tempos somente após concluir. Enquanto aguarda, mostra duração decorrida no navegador, sem animação que afirme uma etapa já executada. Etapa MCP não solicitada aparece como não usada, sem duração inventada. Autorização do token acontece antes desses tempos; não é um span medido nessa tela.

Tokens, custo e avaliação de groundedness/recall continuam não medidos. Nenhum percentual de confiança é inferido da similaridade.

## Verificação real de modelo no CI

O job ollama-real-smoke é opt-in por mensagem de commit contendo `[ollama-smoke]`. Executa CPU com qwen2.5:3b e nomic-embed-text, incluindo saída para revisão manual de atribuição das fontes. O primeiro smoke histórico utilizou o modelo 0.5B. Valida geração, embeddings, fontes e MCP reais. Não mede qualidade e não comprova desempenho do modelo 3B na RTX 4050. Os outros jobs continuam exercitando a demo e os contratos simulados.

Referências: [Ollama Docker](https://docs.ollama.com/docker), [Qwen2.5](https://ollama.com/library/qwen2.5).
