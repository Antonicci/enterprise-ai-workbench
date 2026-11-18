from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from workbench.config import Settings
from workbench.main import create_app
from workbench.models import Citation
from workbench.numeric_checks import compare_runbook,validate_draft

TEXT='Documento sintético. Uma taxa de erros acima de 2% por 5 minutos exige investigação.'
def source(text=TEXT,services=None):
    return Citation(id='orders-1',document_id='orders',title='Runbook',excerpt=text,score=.9,services=services or ['orders-api'])
def metrics(rate=4.8,window=5):
    return {'service':'orders-api','error_rate_pct':rate,'window_minutes':window,'synthetic':True}

@pytest.mark.parametrize('rate,relation,triggered',[('4.8','>',True),('2','=',False),('1.9','<',False),('2.0001','>',True),('0','<',False),('100','>',True)])
def test_decimal_upper_threshold_boundary(rate,relation,triggered):
    check=compare_runbook([source()],metrics(rate))[0]
    assert check['relation']==relation and check['triggered'] is triggered
    assert check['document_source']=='orders-1' and check['tool_source']=='mcp:get_service_metrics'
    assert check['computed_by']=='backend_decimal'
    if rate=='4.8':assert check['difference_percentage_points']=='2.8'

@pytest.mark.parametrize('rate',[None,'NaN','Infinity',-1,101,'invalid'])
def test_missing_or_invalid_measurement_does_not_produce_verdict(rate):
    result=compare_runbook([source()],metrics(rate))[0]
    assert result['status']=='missing_measurement'
    assert 'triggered' not in result

def test_window_mismatch_other_service_and_unsupported_rule_are_not_inferred():
    assert compare_runbook([source()],metrics(window=1))[0]['status']=='window_mismatch'
    assert not compare_runbook([source(services=['payments-api'])],metrics())
    assert not compare_runbook([source('Não é verdade que uma taxa de erros acima de 2% por 5 minutos exige investigação.')],metrics())
    assert not compare_runbook([source('Talvez um valor de 2% seja relevante.')],metrics())
    assert not compare_runbook([source()],None)

def test_conflicting_sources_do_not_choose_a_threshold():
    other=source(TEXT.replace('2%','3%'));other.id='other-1'
    results=compare_runbook([source(),other],metrics())
    assert all(result['status']=='conflicting_rules' for result in results)
    assert all('triggered' not in result for result in results)

@pytest.mark.parametrize('draft',[
    'A taxa atual (4,8%) está dentro deste limiar.',
    'A taxa de erros está abaixo do limite.',
    '4,8% < 2%.',
    '2% > 4.8%.'
])
def test_recognized_numeric_contradictions_are_blocked(draft):
    assert validate_draft(draft,compare_runbook([source()],metrics()))['status']=='blocked'

def test_correct_negation_and_arithmetic_are_not_labeled_fully_validated():
    checks=compare_runbook([source()],metrics())
    assert validate_draft('4,8% > 2%. Não está dentro deste limiar.',checks)['status']=='no_known_conflict'
    assert validate_draft('Análise sem cálculo.',[])['status']=='not_checked'

def test_reported_bad_model_output_is_replaced_without_exposing_draft():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.retrieval.provider.answer=AsyncMock(return_value='A taxa atual (4,8%) está dentro deste limiar. DRAFT-ERROR-MARKER')
        response=client.post('/api/chat',headers={'Authorization':'Bearer demo-ops'},json={'question':'Como investigar erros HTTP 500 na API de pedidos?','include_metrics':True})
        assert response.status_code==200,response.text
        result=response.json()
        assert result['answer_validation']['status']=='blocked'
        assert 'DRAFT-ERROR-MARKER' not in response.text
        assert '4,8% > 2%' in result['answer']
        assert result['comparisons'][0]['triggered'] is True
        assert result['comparisons'][0]['difference_percentage_points']=='2.8'

def test_rule_on_unretrieved_or_unauthorized_document_is_not_consulted():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.retrieval.search=lambda *args:[]
        result=client.post('/api/chat',headers={'Authorization':'Bearer demo-ops'},json={'question':'Pedidos','include_metrics':True}).json()
        assert result['comparisons']==[]
        assert result['answer_validation']['status']=='not_checked'
