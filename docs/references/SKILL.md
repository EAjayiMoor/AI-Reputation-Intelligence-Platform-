# SKILL.md: AI Reputation Intelligence PoC Builder

## Purpose

This skill guides an AI coding agent to build, maintain and improve the AI Reputation Intelligence Platform PoC.

The platform is a Streamlit-based proof of concept designed to assess how an organisation appears across AI-powered search and LLM-style discovery journeys. The initial use case is the University of Southampton Digital Reputation Audit.

The tool must support a product-shaped PoC while remaining focused on the Southampton use case.

---

## Core Product Objective

Build a Streamlit application that enables users to:

1. Upload or use a sample prompt bank.
2. Upload or use sample LLM visibility results.
3. Filter by market, subject, persona, expertise area, intent and platform.
4. Calculate AI visibility scores.
5. Calculate ranking and reputation scores.
6. Identify competitor visibility patterns.
7. Generate rule-based recommendations.
8. Export filtered data and recommendations.

---

## Important Product Context

The tool is not a generic SEO dashboard. It is an AI visibility and reputation audit accelerator.

The first client scenario is:

- Organisation: University of Southampton
- Strategic markets: UK, India, China
- Use case: Understand how Southampton appears in AI/LLM search experiences
- Example audience journey: Prospective Chinese student interested in Engineering
- Main output: Insights and recommendations to improve AI visibility and reputation

---

## Build Principles

When implementing or modifying this product:

1. Keep the PoC simple and demo-ready.
2. Do not introduce a SQL database for the PoC unless explicitly asked.
3. Use Excel/CSV files as the data layer.
4. Avoid unnecessary authentication or deployment complexity.
5. Make all scoring logic transparent.
6. Prefer readable, modular Python code.
7. Do not hard-code Southampton everywhere. Use it as the default organisation.
8. Make the product reusable for future clients.
9. Prioritise consultant usability and client-facing clarity.
10. Ensure the app can run locally with sample data.

---

## Expected Technology Stack

- Python
- Streamlit
- pandas
- plotly
- openpyxl
- pytest

Do not add heavy dependencies unless necessary.

---

## Required Repo Structure

```text
ai-reputation-intelligence-poc/
├── app.py
├── README.md
├── requirements.txt
├── data/
│   ├── sample_prompts.csv
│   ├── sample_results.csv
│   └── sample_recommendation_rules.csv
├── src/
│   ├── data_loader.py
│   ├── validators.py
│   ├── scoring.py
│   ├── recommendations.py
│   ├── charts.py
│   └── narrative.py
├── pages/
│   ├── 1_Executive_Dashboard.py
│   ├── 2_Prompt_Bank_Explorer.py
│   ├── 3_Audience_Journey.py
│   ├── 4_Visibility_Analysis.py
│   ├── 5_Competitor_Analysis.py
│   └── 6_Recommendations.py
├── tests/
│   ├── test_scoring.py
│   ├── test_validators.py
│   └── test_recommendations.py
└── docs/
    ├── product_spec.md
    ├── sprint_plan.md
    └── data_dictionary.md
```

---

## Required Data Inputs

### Prompt Bank

Required columns:

- PromptID
- Organisation
- Market
- Persona
- Subject
- ExpertiseArea
- Intent
- Platform
- Prompt

### Visibility Results

Required columns:

- ResultID
- PromptID
- Platform
- ResponseText
- SouthamptonVisible
- SouthamptonRank
- CompetitorsMentioned
- CitationSources
- RunDate

### Recommendation Rules

Required columns:

- RuleID
- ConditionType
- Threshold
- RecommendationCategory
- RecommendationText
- Priority

---

## Required Pages

### 1. Executive Dashboard

Must show:

- Overall visibility score
- Overall reputation score
- Prompt count
- Southampton mention count
- Average rank
- Visibility by market
- Visibility by subject
- Top competitors
- Priority recommendations

### 2. Prompt Bank Explorer

Must show:

- Prompt upload
- Prompt filters
- Prompt table
- Coverage summary
- Download filtered prompts

### 3. Audience Journey Simulator

Must allow users to select:

- Market
- Persona
- Subject
- Expertise area
- Platform

Must show:

- Relevant prompts
- Visibility results
- Competitors
- Citations
- Narrative summary

### 4. Visibility Analysis

Must show:

- Visibility heatmap
- Visibility by platform
- Visibility by intent
- Average rank by subject
- Low-performing segments

### 5. Competitor Analysis

Must show:

- Most mentioned competitors
- Competitors by market
- Competitors by subject
- Prompt-level competitor data

### 6. Recommendations

Must show:

- Recommendation category
- Priority
- Rationale
- Suggested action
- Export option

---

## Scoring Rules

### Visibility Score

```text
Visibility Score = Southampton Visible Prompts / Total Prompts * 100
```

### Rank Score

- Rank 1 = 100
- Rank 2 = 90
- Rank 3 = 80
- Rank 4-5 = 70
- Rank 6-10 = 50
- Visible but unknown rank = 40
- Not visible = 0

### Citation Score

- Southampton-owned source cited = 100
- Authoritative third-party source cited = 80
- Generic source cited = 50
- No citation = 0

### Reputation Score

```text
Reputation Score =
(Visibility Score * 0.5) +
(Average Rank Score * 0.3) +
(Average Citation Score * 0.2)
```

---

## Recommendation Rules

Generate recommendations when:

- Visibility is low.
- Southampton is absent but competitors are present.
- Citation sources are weak or missing.
- A market/subject/persona segment underperforms.
- A subject is weak across all markets.

Recommendation categories:

- Content gap
- Schema / structured data
- Entity clarity
- E-E-A-T / authority signals
- Internal linking
- Market-specific content
- Third-party citation opportunity
- AI-friendly FAQ content

---

## Coding Standards

- Use clear function names.
- Keep scoring functions pure and unit-testable.
- Avoid duplicating logic across pages.
- Use `src/` modules for reusable logic.
- Use Streamlit session state only where useful.
- Use pandas for data transformations.
- Handle missing values safely.
- Display user-friendly validation errors.
- Keep chart labels clear and concise.

---

## Testing Requirements

Create tests for:

- Required-column validation
- Visibility score calculation
- Rank score calculation
- Reputation score calculation
- Competitor parsing
- Recommendation rule triggers

Tests should be runnable with:

```bash
pytest
```

---

## Demo Requirements

The app must launch locally and load sample Southampton data without requiring uploads.

The demo flow should support:

1. Executive dashboard overview.
2. Filter to China / Engineering / Prospective Student.
3. Show prompt journey.
4. Show whether Southampton appears.
5. Show key competitors.
6. Show recommendations.
7. Export findings.

---

## Avoid These Mistakes

- Do not make the app a generic SEO tool.
- Do not over-engineer with a database for PoC.
- Do not require API keys for the first version.
- Do not hide the scoring methodology.
- Do not make recommendations too vague.
- Do not make Southampton the only possible organisation in the data model.
- Do not create pages that look impressive but do not help answer the client ask.

---

## Definition of Done

The build is complete when:

- The Streamlit app runs locally.
- Sample data loads by default.
- All six pages are available.
- Filters work across the app.
- Scores calculate correctly.
- Competitor analysis works.
- Recommendations generate.
- Exports work.
- Tests pass.
- README is complete.
- The app is demo-ready for the Southampton use case.
