from io import BytesIO

import pandas as pd
import pytest

from src.runs import upload


def reader():
    return upload


def workbook():
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame([['UK', 'Student', 'Engineering', 'Careers', 'Compare careers support.']],
                     columns=[' Market ', 'Persona', 'Subject', 'Category', 'Prompt']).to_excel(
                         writer, index=False, sheet_name='Client prompts')
        pd.DataFrame({'Notes': ['Instructions only']}).to_excel(writer, index=False, sheet_name='Notes')
    return output.getvalue()


def test_excel_sheet_selection_and_five_column_mapping():
    adapter = reader()
    content = workbook()
    assert adapter.list_sheets(content, 'client.xlsx') == ['Client prompts', 'Notes']
    with pytest.raises(ValueError, match='sheet'):
        adapter.read_upload(content, 'client.xlsx')
    frame = adapter.read_upload(content, 'client.xlsx', sheet_name='Client prompts')
    result = adapter.prepare_prompts(frame, organisation_name='Example University')
    assert result.valid
    assert result.prompts['Category'].tolist() == ['Careers']
    assert result.prompts['Subject'].tolist() == ['Engineering']
    assert result.prompts['Organisation'].tolist() == ['Example University']
    assert result.prompts['PromptSource'].tolist() == ['client']
    assert result.prompts['Platform'].tolist() == ['OpenRouter']
    assert result.prompts['Intent'].tolist() == ['']


@pytest.mark.parametrize('content', [
    b'Market,Persona,Subject,Category,Prompt, prompt \nUK,Student,Engineering,Careers,Q,Q',
    b'Market,Persona,Subject,Prompt\nUK,Student,Engineering,Q',
])
def test_bad_headers_are_reported_before_pandas_can_rename_them(content):
    adapter = reader()
    with pytest.raises(ValueError, match='heading'):
        adapter.read_upload(content, 'client.csv')


def test_blank_cells_report_spreadsheet_row_without_silently_dropping_rows():
    adapter = reader()
    content = b'Market,Persona,Subject,Category,Prompt\nUK,Student,Engineering,Careers,Q\nUK,,Medicine,Careers,Q\n,,,,\n'
    frame = adapter.read_upload(content, 'client.csv')
    result = adapter.prepare_prompts(frame, organisation_name='University')
    assert not result.valid
    assert result.issues.to_dict('records') == [{'Row': 3, 'Column': 'Persona', 'Issue': 'Required value is blank'}]
    assert len(result.prompts) == 2


def test_repeated_prompts_keep_distinct_ids_and_na_is_a_valid_market_label():
    adapter = reader()
    content = b'Market,Persona,Subject,Category,Prompt\nNA,Student,Engineering,Careers,Q\nNA,Student,Engineering,Careers,Q'
    result = adapter.prepare_prompts(adapter.read_upload(content, 'client.csv'), organisation_name='University')
    assert result.valid
    assert result.prompts['Market'].tolist() == ['NA', 'NA']
    assert len(result.prompts) == result.prompts['PromptID'].nunique() == 2


def test_empty_file_is_not_a_valid_run():
    adapter = reader()
    with pytest.raises(ValueError, match='empty'):
        adapter.read_upload(b'', 'empty.csv')
    result = adapter.prepare_prompts(pd.DataFrame(columns=adapter.INPUT_COLUMNS), organisation_name='University')
    assert not result.valid


def test_direct_dataframe_validation_uses_excel_row_numbers():
    adapter = reader()
    frame = pd.DataFrame([['UK', '', 'Medicine', 'Careers', 'Q']], columns=adapter.INPUT_COLUMNS)
    result = adapter.prepare_prompts(frame, organisation_name='University')
    assert result.issues['Row'].tolist() == [2]
