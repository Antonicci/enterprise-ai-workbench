from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from workbench.config import Settings
from workbench.providers import Provider, normalize_answer

@pytest.mark.parametrize('fence',['```markdown','```md','```','```Markdown'])
def test_whole_answer_wrapper_is_removed(fence):
    assert normalize_answer(f' {fence}\n## Resumo\n\nTexto **com fontes**.\n```\n')=='## Resumo\n\nTexto **com fontes**.'

@pytest.mark.parametrize('text',[
    '## Resumo\nTexto.',
    'Exemplo:\n```python\nprint(1)\n```',
    '```python\nprint(1)\n```',
])
def test_content_and_code_are_preserved(text):
    assert normalize_answer(text)==text

def test_unclosed_or_multiple_fences_are_not_stripped():
    assert normalize_answer('```markdown\nTexto')=='```markdown\nTexto'
    text='```\nPrimeiro\n```\nSegundo\n```'
    assert normalize_answer(text)==text

@pytest.mark.asyncio
async def test_llm_adapter_normalizes_response_before_returning():
    provider=Provider(Settings(_env_file=None))
    provider.chat=SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content='```markdown\n## Resumo\nRecomenda-se investigar.\n```')))
    result=await provider.answer('Investigar?', [SimpleNamespace(id='runbook',title='Runbook',excerpt='Verificar dependências.',services=[])], None)
    assert result=='## Resumo\nRecomenda-se investigar.'
    messages=provider.chat.ainvoke.call_args.args[0]
    assert 'não realizou esse processamento' in messages[0].content
