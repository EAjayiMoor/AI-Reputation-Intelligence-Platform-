# Product Specification: AI Reputation Intelligence Platform PoC

## 1. Product Summary

**Product name:** AI Reputation Intelligence Platform  
**PoC client/use case:** University of Southampton Digital Reputation Audit  
**Primary user:** Consultant / audit analyst  
**Build type:** Streamlit proof of concept  
**Data approach for PoC:** Excel/CSV-driven, no production database required  

This PoC will demonstrate a reusable product concept for assessing how an organisation appears across AI-powered discovery experiences. The first use case is the University of Southampton, where the client wants to understand how visible and reputable the university is across LLM/search-style journeys, particularly across strategic markets, subjects and expertise areas.

The tool should help consultants create and manage prompt banks, import LLM visibility results, analyse whether Southampton appears, benchmark competitors, identify gaps, and generate practical recommendations.

---

## 2. Problem Statement

Prospective students, researchers, partners and stakeholders are increasingly using AI tools and AI-enhanced search to discover universities. Traditional SEO reporting does not fully explain what AI tools say, whether an organisation is mentioned, which competitors dominate, and what content or authority gaps are limiting visibility.

The University of Southampton needs a structured way to answer:

- What does AI surface about Southampton for priority audiences?
- Does Southampton appear for relevant prompts?
- How does this differ across the UK, India and China?
- Which subjects or expertise areas are strongest or weakest?
- Which competitors appear more often?
- What actions would improve Southampton’s AI visibility and reputation?

---

## 3. Product Vision

Build a product-shaped PoC that serves the Southampton engagement while creating reusable IP for future clients.

The platform should become a repeatable **AI Reputation Intelligence** product that measures AI visibility, competitor positioning and reputation gaps across sectors.

For the PoC, it must remain focused and practical:

- Streamlit application
- Uploadable Excel/CSV inputs
- Rule-based scoring and recommendations
- Filterable dashboards
- Exportable findings

---

## 4. Primary Objective

Enable a consultant to assess AI visibility for the University of Southampton across markets, personas, subjects and expertise areas, using structured prompt-bank and visibility-result data.

The expected output is not just a dashboard. The tool should accelerate the production of an audit narrative:

> “For this audience and subject area, this is how visible Southampton is, who appears instead, why this may be happening, and what Southampton should improve.”

---

## 5. Scope

### 5.1 In Scope for PoC

- Streamlit front end
- Excel/CSV upload
- Prompt-bank explorer
- Audience journey simulator
- Visibility analysis
- Competitor analysis
- Market/subject/persona filtering
- Rule-based scoring
- Rule-based recommendation generation
- Export of results to CSV/Excel
- Export-ready insight summaries
- Southampton as the default organisation
- Configurable competitor list

### 5.2 Out of Scope for PoC

- User authentication
- Role-based access
- Live LLM API orchestration
- Web crawling
- SEO scanning
- Production database
- Multi-client tenant model
- Azure deployment
- Power BI embedding
- Workflow approvals
- Automated scheduled monitoring

### 5.3 Future Product Capabilities

- Live LLM API integrations
- Scheduled prompt runs
- Trend analysis across time
- SQL/PostgreSQL/Azure SQL database
- Multi-organisation support
- Authentication and permissions
- Export to PowerPoint
- CRM/commercial pipeline integration
- Sector-specific prompt templates

---

## 6. Target Users

### 6.1 Consultant / Analyst

Needs to:

- Upload prompt banks and audit results
- Filter by market, subject, persona and expertise area
- Understand visibility performance
- Identify competitor patterns
- Generate recommendations
- Export findings for client deliverables

### 6.2 Client Stakeholder

Needs to:

- Understand where Southampton is visible or invisible
- See priority weaknesses
- Compare against competitors
- Understand what actions to take
- See evidence in a simple and visual format

### 6.3 Future Product Owner

Needs to:

- Reuse the tool with other organisations
- Extend prompt templates
- Add more sectors and clients
- Move from PoC to product architecture

---

## 7. Core User Stories

### Prompt Bank

1. As a consultant, I want to upload a prompt bank so that I can define the questions being tested.
2. As a consultant, I want to filter prompts by market, subject, persona, expertise area and intent so that I can inspect relevant prompt sets.
3. As a consultant, I want to see how many prompts exist for each segment so that I can identify coverage gaps.

### Visibility Results

4. As a consultant, I want to upload visibility results so that I can analyse whether Southampton appears in AI outputs.
5. As a consultant, I want the app to calculate visibility percentage so that I can quickly understand performance.
6. As a consultant, I want to see average rank where Southampton appears so that I can understand prominence.

### Audience Journey Simulator

7. As a consultant, I want to select a market, subject and persona so that I can simulate what that audience may encounter.
8. As a consultant, I want to see prompts, visibility, competitors and citations for the selected journey so that I can explain the audience view.

### Competitor Analysis

9. As a consultant, I want to see which competitors appear most often so that I can identify who dominates AI responses.
10. As a consultant, I want to compare Southampton with competitors by mention frequency and average rank so that I can benchmark performance.

### Recommendations

11. As a consultant, I want the app to generate recommendations based on low visibility, poor rank and weak citation patterns so that I can create client-ready outputs.
12. As a consultant, I want recommendations to be grouped by market, subject and priority so that I can explain where effort should be focused.

### Export

13. As a consultant, I want to export filtered data and insight summaries so that I can use them in PowerPoint or Word deliverables.

---

## 8. Application Structure

### Page 1: Home / Executive Dashboard

Purpose: Provide a high-level view of Southampton’s AI visibility.

Must include:

- Overall visibility score
- Overall reputation score
- Prompts tested
- Southampton mentions
- Average rank
- Number of competitors identified
- Visibility by market
- Visibility by subject
- Visibility by persona
- Top competitors by mention frequency
- High-priority recommendations summary

Suggested Streamlit components:

- `st.metric`
- `st.bar_chart`
- `plotly.express`
- `st.dataframe`

---

### Page 2: Prompt Bank Explorer

Purpose: Inspect and manage the prompt bank.

Must include:

- File upload for prompt bank
- Prompt table
- Filters:
  - Market
  - Subject
  - Persona
  - Expertise Area
  - Intent
  - Platform
- Prompt coverage summary
- Download filtered prompts

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

---

### Page 3: Audience Journey Simulator

Purpose: Translate the audit into an audience-specific discovery view.

Must include:

- Market selector
- Persona selector
- Subject selector
- Expertise Area selector
- Platform selector
- Results summary for selected segment
- Prompt-by-prompt output table
- Competitors appearing in that journey
- Citation sources used
- Auto-generated journey narrative

Example narrative:

> For a prospective Chinese student interested in Engineering, Southampton appears in X% of tested prompts. The most common competing institutions are A, B and C. The main visibility gaps relate to Y and Z.

---

### Page 4: Visibility Analysis

Purpose: Analyse performance across dimensions.

Must include:

- Visibility heatmap by Market x Subject
- Visibility by platform
- Visibility by intent
- Average rank by subject
- Presence/absence table
- Low-performing segments table

Suggested charts:

- Heatmap
- Bar chart
- Scatter plot of visibility vs average rank

---

### Page 5: Competitor Analysis

Purpose: Benchmark Southampton against competitors.

Must include:

- Top competitors by frequency
- Competitor average rank
- Competitor presence by subject
- Competitor presence by market
- Prompt-level competitor table

Required outputs:

- “Competitors most often appearing instead of Southampton”
- “Competitors most often appearing alongside Southampton”
- “Subjects where competitors dominate”

---

### Page 6: Recommendations

Purpose: Generate practical client-facing actions.

Must include:

- Recommendation rules engine
- Priority classification: High / Medium / Low
- Grouping by market, subject, persona and expertise area
- Recommended action
- Rationale
- Suggested owner category, e.g. Content, SEO, Digital, Academic, Marketing
- Export recommendations

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

## 9. Data Model

### 9.1 Prompt Bank Input

File name: `prompts.xlsx` or `prompts.csv`

Required columns:

| Column | Description | Example |
|---|---|---|
| PromptID | Unique prompt identifier | P001 |
| Organisation | Organisation being assessed | University of Southampton |
| Market | Market segment | China |
| Persona | Audience type | Prospective Student |
| Subject | Subject area | Engineering |
| ExpertiseArea | Strategic expertise area | AI / Sustainability |
| Intent | User intent | Compare Universities |
| Platform | AI platform tested | ChatGPT |
| Prompt | Actual prompt text | Best UK engineering universities for Chinese students |

### 9.2 Visibility Results Input

File name: `results.xlsx` or `results.csv`

Required columns:

| Column | Description | Example |
|---|---|---|
| ResultID | Unique result identifier | R001 |
| PromptID | Links to prompt bank | P001 |
| Platform | AI platform tested | ChatGPT |
| ResponseText | Captured AI response | Text output |
| SouthamptonVisible | Whether Southampton appears | TRUE/FALSE |
| SouthamptonRank | Rank/order if present | 3 |
| CompetitorsMentioned | Comma-separated competitors | Imperial, Manchester, Warwick |
| CitationSources | Sources cited or referenced | QS, UCAS, Southampton website |
| RunDate | Date result captured | 2026-08-03 |

### 9.3 Recommendation Rules Input

File name: `recommendation_rules.xlsx` or embedded Python rules.

Required fields:

| Field | Description | Example |
|---|---|---|
| RuleID | Unique rule | RULE001 |
| ConditionType | Metric tested | Visibility |
| Threshold | Value threshold | <25 |
| RecommendationCategory | Type of recommendation | Content Gap |
| RecommendationText | Suggested action | Create AI-friendly FAQ content |
| Priority | High/Medium/Low | High |

---

## 10. Scoring Logic

### 10.1 Visibility Score

```text
Visibility Score = Southampton Visible Prompts / Total Prompts * 100
```

### 10.2 Rank Score

Recommended logic:

| Rank | Score |
|---|---:|
| 1 | 100 |
| 2 | 90 |
| 3 | 80 |
| 4-5 | 70 |
| 6-10 | 50 |
| Mentioned but rank unknown | 40 |
| Not visible | 0 |

### 10.3 Citation Score

For PoC, use a simple rule:

| Citation pattern | Score |
|---|---:|
| Southampton-owned source cited | 100 |
| Authoritative third-party source cited | 80 |
| Generic source cited | 50 |
| No citation | 0 |

### 10.4 Reputation Score

```text
Reputation Score =
(Visibility Score * 0.5) +
(Average Rank Score * 0.3) +
(Average Citation Score * 0.2)
```

For the PoC, this should be transparent and explained in the interface.

---

## 11. Recommendation Logic

### Rule Examples

```text
IF Visibility Score < 25
THEN Priority = High
Recommendation = Create targeted content for this market/persona/subject combination.
```

```text
IF SouthamptonVisible = FALSE AND competitors are repeatedly mentioned
THEN Recommendation = Analyse competitor content and create stronger comparison/authority content.
```

```text
IF CitationSources does not include Southampton-owned sources
THEN Recommendation = Improve on-site content clarity, schema and authority signals.
```

```text
IF Market = China AND Visibility Score is low
THEN Recommendation = Create China-specific audience content and international student FAQs.
```

```text
IF Subject visibility is low across all markets
THEN Recommendation = Prioritise subject-level content, FAQs, internal links and third-party citations.
```

---

## 12. Acceptance Criteria

### Functional Acceptance Criteria

- User can upload prompt-bank file.
- User can upload results file.
- App validates required columns and shows clear errors if missing.
- User can filter by market, subject, persona, expertise area, platform and intent.
- App calculates visibility score correctly.
- App calculates rank score correctly.
- App calculates reputation score correctly.
- App displays competitor frequency.
- App generates recommendations based on configured rules.
- User can export filtered data.
- User can export recommendations.

### Quality Acceptance Criteria

- App can run locally using `streamlit run app.py`.
- App has clear navigation.
- App handles missing values gracefully.
- App includes sample data.
- App avoids hard-coding Southampton wherever possible, except default PoC configuration.
- App has readable function names and modular structure.
- App includes a README with setup instructions.
- App includes unit-testable scoring functions.

---

## 13. Suggested Repo Structure

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

## 14. Non-Functional Requirements

- Local-first PoC
- Simple deployment using Streamlit
- No secrets required for PoC
- No live API calls required
- Works with sample CSVs
- Handles at least 1,000 prompts and 10,000 result rows
- Uses clear UK English labels
- Charts should be readable in a client demo
- Logic should be transparent and explainable

---

## 15. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Scope expands into production product | Keep PoC Excel/CSV-driven |
| Data quality issues | Build validation and missing-column warnings |
| Recommendations feel generic | Create rules based on market, subject, visibility and citation patterns |
| Dashboard becomes too busy | Prioritise executive summary and drill-down pages |
| Product story drifts from Southampton ask | Keep default examples and seed data focused on Southampton |

---

## 16. Definition of Done

The PoC is done when:

- The Streamlit app runs locally.
- Sample Southampton data loads successfully.
- Each page works without code edits.
- The user can filter by market, subject and persona.
- The app calculates visibility and reputation scores.
- The app shows competitor benchmarks.
- The app generates prioritised recommendations.
- The app exports filtered results.
- The README explains setup and use.
- The product is demo-ready using the Southampton scenario.
