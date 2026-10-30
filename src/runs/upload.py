"""Read the client-facing prompt sheet without requiring execution metadata."""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pandas as pd

INPUT_COLUMNS = ['Market', 'Persona', 'Subject', 'Category', 'Prompt']


def list_sheets(content: bytes, filename: str) -> list[str]:
    suffix = Path(filename).suffix.lower()
    if suffix == '.csv':
        return []
    if suffix != '.xlsx':
        raise ValueError('Please upload an XLSX workbook or CSV file.')
    with pd.ExcelFile(BytesIO(content), engine='openpyxl') as workbook:
        return workbook.sheet_names


def _canonical_headers(columns) -> list[str]:
    headers = [str(value).strip() for value in columns]
    folded = [value.casefold() for value in headers]
    if len(folded) != len(set(folded)):
        raise ValueError('Duplicate headings found. Each heading must appear once.')
    canonical = {value.casefold(): value for value in INPUT_COLUMNS}
    missing = [value for key, value in canonical.items() if key not in folded]
    if missing:
        raise ValueError('Missing required headings: ' + ', '.join(missing))
    return [canonical.get(value.casefold(), value) for value in headers]


def read_upload(content: bytes, filename: str, *, sheet_name: str | None = None) -> pd.DataFrame:
    if not content:
        raise ValueError('The uploaded file is empty.')
    suffix = Path(filename).suffix.lower()
    if suffix == '.csv':
        raw = pd.read_csv(BytesIO(content), header=None, dtype=object,
                          encoding='utf-8-sig', keep_default_na=False, skip_blank_lines=False)
    elif suffix == '.xlsx':
        sheets = list_sheets(content, filename)
        if sheet_name is None and len(sheets) != 1:
            raise ValueError('Select a workbook sheet before continuing.')
        selected = sheet_name or sheets[0]
        if selected not in sheets:
            raise ValueError('The selected sheet is not in this workbook.')
        raw = pd.read_excel(BytesIO(content), sheet_name=selected, engine='openpyxl',
                            header=None, dtype=object, keep_default_na=False)
    else:
        raise ValueError('Please upload an XLSX workbook or CSV file.')
    if raw.empty:
        raise ValueError('The selected sheet is empty.')
    # Read headings as cells so pandas cannot silently rename duplicate headings.
    headers = _canonical_headers(raw.iloc[0].fillna('').tolist())
    frame = raw.iloc[1:].copy()
    frame.columns = headers
    # Index zero represents spreadsheet row two, including blank separator rows.
    frame.index = frame.index - 1
    return frame


@dataclass
class PromptUpload:
    prompts: pd.DataFrame
    issues: pd.DataFrame

    @property
    def valid(self) -> bool:
        return self.issues.empty


def prepare_prompts(frame: pd.DataFrame, *, organisation_name: str) -> PromptUpload:
    working = frame.copy()
    working.columns = _canonical_headers(working.columns)
    cleaned = working.fillna('').astype(str).apply(lambda column: column.str.strip())
    # Entirely empty spreadsheet rows are separators, rather than prompt rows.
    cleaned = cleaned.loc[cleaned.ne('').any(axis=1)]
    prompts = cleaned[INPUT_COLUMNS].copy()
    issues = []
    for row_index, row in prompts.iterrows():
        for column in INPUT_COLUMNS:
            if not row[column]:
                issues.append({'Row': int(row_index) + 2, 'Column': column,
                               'Issue': 'Required value is blank'})
    if prompts.empty:
        issues.append({'Row': None, 'Column': '', 'Issue': 'No prompt rows were found'})
    prompts = prompts.reset_index(drop=True)
    prompts.insert(0, 'PromptID', [f'UPLOAD-{index + 1:05d}' for index in range(len(prompts))])
    prompts['Organisation'] = organisation_name
    prompts['Platform'] = 'OpenRouter'
    prompts['PromptSource'] = 'client'
    prompts['GenerationMethod'] = 'uploaded_sheet'
    for column in ['ExpertiseArea', 'Intent', 'PersonaTemplateID']:
        prompts[column] = ''
    return PromptUpload(prompts, pd.DataFrame(issues, columns=['Row', 'Column', 'Issue']))
