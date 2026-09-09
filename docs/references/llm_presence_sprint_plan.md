# LLM presence analytics sprint plan

The product measures how organisations are represented in LLM answers across
personas, topics, prompts and models. Each sprint adds one coherent analysis
view, using the same response-level observation contract.

## Sprint 1 — Measurement foundation (complete)

- Standardise one observation as organisation × prompt × persona × topic × model × response.
- Add explainable derived fields: mention, prompted/organic, recommendation, shortlist, first-mentioned order, prominence, citations, competitor count, association and confidence.
- Keep raw response text as the audit source; no extra model/API calls.
- Cover the rules with unit tests and load them through the existing Streamlit data path.

## Sprint 2 — Presence and narrative overview (complete)

Existing `07_Visibility_Analysis` is now the executive view of presence:

- mention rate and average prominence by model, persona, topic and prompt mode;
- recommendation and shortlist rates;
- positive/neutral/negative association split;
- cited vs uncited answer coverage;
- filters that preserve organic vs prompted comparisons.

## Sprint 3 — Competitive landscape (complete)

`08_Competitor_Analysis` now exposes the competitive signals already present in
the responses:

- share of recognised organisation mentions;
- first-mentioned and shortlist share;
- competitor co-occurrence matrix;
- model/persona differences in who is surfaced;
- downloadable evidence rows for every comparison.

## Sprint 4 — Topic and persona diagnostics (complete)

`10_Topic_Persona_Diagnostics` groups the dimensions into one decision-focused
analysis page rather than creating a separate metric page for every dimension:

- reputation strengths and gaps by subject/expertise area;
- persona-specific recommendation and association patterns;
- prompt clusters with weak or missing presence;
- sample responses behind each outlier;
- CSV downloads for segment diagnostics and outlier evidence.

## Sprint 5 — Evidence and action loop (complete)

`09_Recommendations` now connects measurement to action, with the execution/audit
views remaining the source for full response detail:

- prioritise gaps by reach (eligible responses), confidence and prominence;
- show cited evidence and response excerpts beside each recommendation;
- track reruns over time with matched RunDate sweep comparison;
- export a client-ready summary without exposing API credentials;
- export recommendation evidence and run-history tables as CSV.

Each sprint should ship with tests, a small set of representative response
fixtures, and a clear link from the aggregate chart back to its source rows.
