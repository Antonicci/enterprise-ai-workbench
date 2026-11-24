"""Evidence-based governance view; no automatic certification or hardware tuning."""
from datetime import datetime,timezone
import httpx

def governance_report(settings,user):
    return {
        "framework":"Referência: seis pilares AWS Well-Architected",
        "scope":"Laboratório; não é avaliação oficial nem certificação de conformidade.",
        "identity":{"mode":settings.auth_mode,"roles":list(user.roles),"permissions":sorted(user.permissions)},
        "limits":{"requests_per_minute":settings.requests_per_minute,"max_concurrent_requests":settings.max_concurrent_requests,
                  "max_prompt_chars":settings.max_prompt_chars,"max_output_tokens":settings.max_output_tokens,
                  "ollama_num_ctx":settings.ollama_num_ctx if settings.provider=="ollama" else None,
                  "request_timeout_seconds":settings.request_timeout,"scope":"Processo atual; limites de consulta não cobrem ingestão."},
        "pricing":{"enabled":settings.provider=="openai-compatible" and settings.price_model==settings.chat_model and settings.input_price_per_million is not None and settings.output_price_per_million is not None,
                   "model":settings.price_model or None,"input_per_million":str(settings.input_price_per_million) if settings.input_price_per_million is not None else None,
                   "output_per_million":str(settings.output_price_per_million) if settings.output_price_per_million is not None else None,
                   "currency":settings.price_currency,"scope":"Estimativa da geração; não inclui embeddings, retries, infraestrutura ou impostos."},
        "pillars":[
            {"name":"Excelência operacional","status":"parcial","evidence":"Tempos por etapa, taxas de execução, identificador do processo, período e consultas recentes sem prompts.",
             "gap":"Persistência de telemetria, alertas e agregação entre workers ainda planejadas."},
            {"name":"Segurança","status":"parcial","evidence":("OIDC/PKCE configurado; JWT validado por emissor, audiência, assinatura e expiração." if settings.auth_mode=="oidc" else "Autenticação demo: apenas dados sintéticos; OIDC não está ativo.")+" Perfis e ACL aplicados no backend antes da recuperação e ferramentas.",
             "gap":"Keycloak local usa HTTP/start-dev; TLS de produção, gestão de segredos, revisão de ameaças e auditoria durável pendentes."},
            {"name":"Confiabilidade","status":"parcial","evidence":"Timeout de consulta, limite de admissão, respostas explícitas 413/429/503 e retenção de contradições numéricas reconhecidas.",
             "gap":"Sem SLA, HA, circuit breaker ou cancelamento garantido no provedor. Trabalho síncrono pode continuar após timeout."},
            {"name":"Eficiência de performance","status":"parcial","evidence":"Limites configuráveis de contexto e saída, tempos medidos e tokens/s quando informados pelo Ollama.",
             "gap":"Diagnóstico via API do Ollama não mede VRAM total/livre. Seleção do modelo é explícita; benchmark depende da carga e host."},
            {"name":"Otimização de custos","status":"parcial","evidence":"Uso de geração informado pelo provedor e estimativa com preços configurados para o modelo de API.",
             "gap":"Sem orçamento financeiro bloqueante, quota exata de tokens, cobrança conciliada ou custo de energia/infraestrutura local."},
            {"name":"Sustentabilidade","status":"planejado","evidence":"Contexto, saída e concorrência limitados podem evitar trabalho excessivo; benefício energético não medido.",
             "gap":"Sem medição de energia/carbono. Avaliar menor modelo que atenda qualidade e latência com dados de teste."}
        ]}

def _bytes(value):
    return value if isinstance(value,int) and not isinstance(value,bool) and value>=0 else None

def runtime_models(inventory,loaded):
    result=[]
    by_name={m.get("name"):m for m in loaded if isinstance(m,dict)}
    for item in inventory[:100]:
        if not isinstance(item,dict): continue
        name=item.get("name")
        if not isinstance(name,str): continue
        running=by_name.get(name)
        details=item.get("details") or {}
        result.append({"name":name,"download_bytes":_bytes(item.get("size")),"parameters":details.get("parameter_size"),
                       "quantization":details.get("quantization_level"),"loaded":running is not None,
                       "loaded_bytes":_bytes(running.get("size")) if running else None,
                       "loaded_vram_bytes":_bytes(running.get("size_vram")) if running else None,
                       "context_length":running.get("context_length") if running else None})
    return result

async def runtime_report(settings):
    base={"provider":settings.provider,"configured_model":settings.chat_model,"collected_at":datetime.now(timezone.utc).isoformat(),
          "declared_host":{"ram_gb":settings.host_ram_gb,"vram_gb":settings.host_vram_gb,"source":"operator-declared; not detected"},
          "models":[],"available":False,
          "limitations":["/api/ps informa memória dos modelos carregados, não VRAM total ou livre do host.",
                         "Tamanho em disco não é requisito de VRAM. Contexto, cache KV, quantização e outras cargas afetam memória.",
                         "Nenhuma troca ou download automático. Altere CHAT_MODEL e reinicie após validar qualidade e carga."]}
    if settings.provider!="ollama":
        return {**base,"reason":"Diagnóstico de modelos locais disponível apenas para Ollama."}
    try:
        async with httpx.AsyncClient(timeout=3,follow_redirects=False) as client:
            tags=await client.get(settings.ollama_base_url.rstrip("/")+"/api/tags")
            tags.raise_for_status()
            ps=await client.get(settings.ollama_base_url.rstrip("/")+"/api/ps")
            ps.raise_for_status()
        inventory=tags.json().get("models",[])
        loaded=ps.json().get("models",[])
        if not isinstance(inventory,list) or not isinstance(loaded,list): raise ValueError("Invalid inventory")
        return {**base,"available":True,"models":runtime_models(inventory,loaded)}
    except (httpx.HTTPError,ValueError,TypeError,AttributeError):
        return {**base,"reason":"Ollama indisponível para diagnóstico; verifique o serviço configurado."}
