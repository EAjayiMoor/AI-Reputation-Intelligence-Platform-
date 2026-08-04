# Sprint Plan: AI Reputation Intelligence Platform PoC

## Sprint Goal

Build a Streamlit proof of concept that demonstrates how the University of Southampton’s AI visibility and reputation can be assessed across markets, personas, subjects and expertise areas using prompt-bank and visibility-result data.

The sprint should produce a demo-ready application, sample data, scoring logic, recommendation logic and exportable outputs.

---

## Delivery Principles

- Build the smallest useful product-shaped PoC.
- Keep the Southampton use case front and centre.
- Avoid production complexity.
- Use Excel/CSV inputs only.
- Make scoring and recommendations explainable.
- Prioritise client-demo clarity over technical sophistication.

---

## Sprint Backlog

### Epic 1: Project Setup

#### Story 1.1: Create repo structure

**Task:** Create the standard project structure.

Acceptance criteria:

- Repo contains `app.py`, `pages/`, `src/`, `data/`, `tests/`, `docs/`.
- App can be launched with `streamlit run app.py`.
- `requirements.txt` is included.

#### Story 1.2: Create README

**Task:** Create setup and run instructions.

Acceptance criteria:

- README explains product purpose.
- README lists dependencies.
- README explains how to run locally.
- README explains sample data files.

---

### Epic 2: Data Model and Sample Data

#### Story 2.1: Create sample prompt-bank data

**Task:** Build `sample_prompts.csv` using Southampton-focused examples.

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

Acceptance criteria:

- At least 30 sample prompts.
- Covers UK, India and China.
- Covers at least Engineering, Medicine, Computer Science and Business.
- Covers at least prospective student and researcher personas.

#### Story 2.2: Create sample visibility-results data

**Task:** Build `sample_results.csv` linked to prompt IDs.

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

Acceptance criteria:

- Each sample prompt has at least one result.
- Some prompts have Southampton visible.
- Some prompts have Southampton absent.
- Competitors are included.
- Citation sources are included.

#### Story 2.3: Create recommendation rules sample

**Task:** Build `sample_recommendation_rules.csv`.

Acceptance criteria:

- Rules cover low visibility.
- Rules cover weak citation presence.
- Rules cover market-specific gaps.
- Rules cover subject-level gaps.

---

### Epic 3: Data Loading and Validation

#### Story 3.1: Build data loader

**Task:** Create `src/data_loader.py`.

Acceptance criteria:

- Loads CSV files.
- Loads Excel files if provided.
- Returns pandas DataFrames.
- Handles missing files with meaningful messages.

#### Story 3.2: Build validators

**Task:** Create `src/validators.py`.

Acceptance criteria:

- Checks required prompt columns.
- Checks required results columns.
- Shows missing columns clearly in Streamlit.
- Prevents app failure if invalid data is uploaded.

---

### Epic 4: Scoring Engine

#### Story 4.1: Visibility score

**Task:** Implement visibility score.

Acceptance criteria:

- Calculates visible prompts / total prompts * 100.
- Handles empty data safely.
- Can calculate by overall, market, subject, persona and platform.

#### Story 4.2: Rank score

**Task:** Implement rank score.

Acceptance criteria:

- Rank 1 = 100.
- Rank 2 = 90.
- Rank 3 = 80.
- Rank 4-5 = 70.
- Rank 6-10 = 50.
- Visible but unknown rank = 40.
- Not visible = 0.

#### Story 4.3: Reputation score

**Task:** Implement combined reputation score.

Acceptance criteria:

- Uses visibility, rank and citation scores.
- Formula is visible in the app.
- Scores output from 0 to 100.

---

### Epic 5: Streamlit Navigation and Layout

#### Story 5.1: Create app shell

**Task:** Build `app.py` with clear landing page.

Acceptance criteria:

- Product name is visible.
- Southampton PoC context is visible.
- Navigation works.
- App loads sample data by default.

#### Story 5.2: Add sidebar filters

**Task:** Add reusable filters.

Acceptance criteria:

- Filters include market, subject, persona, expertise area, intent and platform.
- Filters update data tables and metrics.
- Filters handle “All” selections.

---

### Epic 6: Executive Dashboard

#### Story 6.1: Build headline metrics

**Task:** Build executive summary page.

Acceptance criteria:

- Shows overall visibility score.
- Shows reputation score.
- Shows prompt count.
- Shows Southampton mentions.
- Shows average rank.

#### Story 6.2: Build core charts

**Task:** Add charts to dashboard.

Acceptance criteria:

- Visibility by market chart.
- Visibility by subject chart.
- Top competitors chart.
- High-priority recommendations preview.

---

### Epic 7: Prompt Bank Explorer

#### Story 7.1: Build prompt table

**Task:** Display and filter prompt bank.

Acceptance criteria:

- Prompt table displays all fields.
- Filters work.
- Prompt count updates.
- Filtered prompts can be downloaded.

#### Story 7.2: Coverage summary

**Task:** Show prompt coverage by market, subject and persona.

Acceptance criteria:

- Coverage table or chart included.
- Empty or thin segments are identifiable.

---

### Epic 8: Audience Journey Simulator

#### Story 8.1: Build journey selector

**Task:** Let user select market, subject, persona and expertise area.

Acceptance criteria:

- User can simulate a defined audience journey.
- App displays relevant prompts and results.

#### Story 8.2: Generate journey narrative

**Task:** Create a simple narrative summary.

Acceptance criteria:

- Narrative includes visibility score.
- Narrative includes top competitors.
- Narrative includes key gap.
- Narrative is written in clear UK English.

---

### Epic 9: Visibility Analysis

#### Story 9.1: Build visibility heatmap

**Task:** Show visibility by Market x Subject.

Acceptance criteria:

- Heatmap renders correctly.
- Values are percentages.
- Missing values handled gracefully.

#### Story 9.2: Add rank analysis

**Task:** Show average rank by subject/platform.

Acceptance criteria:

- Rank analysis displays only visible prompts where appropriate.
- Empty values are not misleading.

---

### Epic 10: Competitor Analysis

#### Story 10.1: Parse competitor mentions

**Task:** Split comma-separated competitor fields.

Acceptance criteria:

- Competitors are counted accurately.
- Leading/trailing spaces are trimmed.
- Empty competitors are ignored.

#### Story 10.2: Competitor dashboard

**Task:** Display competitor rankings.

Acceptance criteria:

- Shows most frequently mentioned competitors.
- Shows competitors by subject.
- Shows competitors by market.

---

### Epic 11: Recommendation Engine

#### Story 11.1: Implement rule checks

**Task:** Generate recommendations from result patterns.

Acceptance criteria:

- Low visibility generates recommendation.
- Weak citations generate recommendation.
- Market-specific low visibility generates recommendation.
- Subject-level weakness generates recommendation.

#### Story 11.2: Recommendation page

**Task:** Display recommendations.

Acceptance criteria:

- Recommendations have priority.
- Recommendations have rationale.
- Recommendations have category.
- Recommendations can be exported.

---

### Epic 12: Testing and Quality

#### Story 12.1: Add unit tests

**Task:** Create tests for scoring and validation.

Acceptance criteria:

- Tests cover visibility score.
- Tests cover rank score.
- Tests cover required-column validation.
- Tests pass locally.

#### Story 12.2: Demo readiness check

**Task:** Final polish for demo.

Acceptance criteria:

- No obvious broken pages.
- Sample data loads by default.
- Charts are readable.
- Labels are clear.
- Recommendations are understandable.

---

## Suggested Sprint Sequence

### Build Slice 1: Foundations

- Repo structure
- Requirements
- Sample data
- Data loader
- Validators

### Build Slice 2: Core Analytics

- Scoring engine
- Executive dashboard
- Filters
- Prompt explorer

### Build Slice 3: Client Value

- Audience journey simulator
- Competitor analysis
- Recommendation engine

### Build Slice 4: Polish

- Exports
- Tests
- README
- Demo script
- UX tidy-up

---

## Definition of Ready

A story is ready when:

- Required input columns are known.
- Expected output is clear.
- Acceptance criteria are written.
- Dependencies are identified.

---

## Definition of Done

A story is done when:

- Code is implemented.
- Page/function runs without error.
- Sample data demonstrates the feature.
- Acceptance criteria are met.
- Relevant tests are added where appropriate.
- README or docs updated where needed.

---

## Demo Script

1. Open app.
2. Show executive dashboard for Southampton.
3. Explain overall visibility score.
4. Filter to China / Engineering / Prospective Student.
5. Open audience journey simulator.
6. Show prompts and visibility results.
7. Show competitors appearing more often.
8. Open recommendations page.
9. Export recommendations.
10. Explain how this can become a broader product.
