"""Bounded, deterministic checks over an explicitly supported runbook sentence.

This is not a general language parser or semantic faithfulness evaluator.
"""
from decimal import Decimal,InvalidOperation
import re
import unicodedata

# Require a complete affirmative sentence. Negated/quoted/unsupported prose is not interpreted.
RULE=re.compile(r'(?:^|(?<=[.!?\n]))\s*(Uma taxa de erros acima de (\d+(?:[.,]\d+)?)% por (\d+) minutos exige investiga[çc][ãa]o\.)',re.I)

def number(value):
    try:
        parsed=Decimal(str(value).replace(',','.'))
        return parsed if parsed.is_finite() else None
    except (InvalidOperation,ValueError):return None

def decimal_text(value):return format(value.normalize(),'f').replace('.',',')

def compare_runbook(citations,metrics):
    if not metrics:return []
    matches=[]
    for citation in citations:
        if citation.services and metrics.get('service') not in citation.services:continue
        for rule in RULE.finditer(citation.excerpt):
            threshold=number(rule.group(2));window=int(rule.group(3))
            if threshold is None or not 0<=threshold<=100 or not 1<=window<=1440:continue
            matches.append({'document_source':citation.id,'tool_source':'mcp:get_service_metrics','service':metrics.get('service'),
                            'metric':'error_rate_pct','operator':'>','threshold':str(threshold),'window_minutes':window,
                            'rule_excerpt':rule.group(1),'synthetic':metrics.get('synthetic',False)})
    # Conflicting thresholds in the same window require curation, never model arbitration.
    for match in matches:
        thresholds={m['threshold'] for m in matches if m['window_minutes']==match['window_minutes']}
        observed=number(metrics.get('error_rate_pct'))
        if len({number(t) for t in thresholds})>1:
            match.update(status='conflicting_rules',reason='Fontes recuperadas têm limiares diferentes para a mesma janela.');continue
        if number(metrics.get('window_minutes'))!=Decimal(match['window_minutes']):
            match.update(status='window_mismatch',reason='Janelas diferentes; comparação não aplicada.');continue
        if observed is None or not 0<=observed<=100:
            match.update(status='missing_measurement',reason='Medição inválida ou ausente.');continue
        threshold=number(match['threshold']);triggered=observed>threshold
        relation='>' if observed>threshold else '<' if observed<threshold else '='
        match.update(status='evaluated',observed=str(observed),relation=relation,triggered=triggered,
                     difference_percentage_points=str(observed-threshold),computed_by='backend_decimal',
                     summary=f'{decimal_text(observed)}% {relation} {decimal_text(threshold)}% na janela de {match["window_minutes"]} min. '+
                     ('Condição de investigação atendida.' if triggered else 'Condição estrita acima do limiar não atendida.'))
    return matches

def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')

def validate_draft(answer,comparisons):
    evaluated=[c for c in comparisons if c['status']=='evaluated']
    reasons=[]
    for comparison in evaluated:
        # Conservative phrase guard for the demonstrated upper-bound error-rate case.
        if comparison['relation']=='>':
            for sentence in re.split(r'\n|(?<=[.!?])\s+',normalized(answer)):
                negated=re.search(r'nao\s+(?:esta|se encontra|fica)\s+(?:mais\s+)?(?:dentro|abaixo)',sentence)
                contradiction=re.search(r'(?:dentro|abaixo)\s+(?:deste|desse|do|dos|de um|de seu)\s+(?:limiar|limite)',sentence)
                if contradiction and not negated and not ('latencia' in sentence and 'erros' not in sentence and 'taxa' not in sentence):
                    reasons.append('O rascunho descreve a medição como dentro/abaixo do limiar, mas o cálculo está acima.');break
        # Check explicit numeric comparisons involving this observed value and threshold.
        for left,operator,right in re.findall(r'(\d+(?:[.,]\d+)?)\s*%?\s*(<=|>=|<|>|=|≤|≥)\s*(\d+(?:[.,]\d+)?)\s*%?',answer):
            a,b=number(left),number(right)
            if {a,b}!={number(comparison['observed']),number(comparison['threshold'])}:continue
            valid={'<':a<b,'>':a>b,'=':a==b,'<=':a<=b,'>=':a>=b,'≤':a<=b,'≥':a>=b}[operator]
            if not valid:reasons.append('O rascunho contém uma comparação numérica falsa para os valores verificados.')
    return {'status':'blocked' if reasons else 'no_known_conflict' if evaluated else 'not_checked',
            'reasons':list(dict.fromkeys(reasons)),
            'scope':'Guard limitado a padrões reconhecidos; não é validação semântica completa.'}

def safe_report(comparisons):
    lines=['### Resultado calculado pelo backend']
    for c in comparisons:
        if c['status']=='evaluated':lines.append(f"- {c['summary']} [{c['document_source']}] [{c['tool_source']}]")
    lines+=['### Revisão necessária','O rascunho do modelo foi retido por possível contradição com o cálculo. Consulte os trechos autorizados e revise os próximos passos. Nenhuma alteração foi executada.']
    return '\n\n'.join(lines)
