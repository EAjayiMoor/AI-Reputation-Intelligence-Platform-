# LLM presence measurement contract

Each scored response is one observation: organisation × prompt × persona × topic × model × response.
The app derives the following fields deterministically from the stored response and parser outputs:

| Field | Definition |
| --- | --- |
| `Mentioned` | The target organisation is present in the response. |
| `Prompted` / `Organic` | Whether the prompt explicitly named an organisation (`PromptMentionType`). |
| `Recommended` | The target appears in the same sentence/line as a recommendation or strong-choice signal. |
| `Shortlisted` | The target appears in the same sentence/line as shortlist, finalist or top-options language. |
| `FirstMentioned` | The target appears before recognised competitor aliases (or is the only recognised organisation). |
| `ProminenceScore` | A transparent rank-derived score using the existing 1–3, 4–5 and 6–10 bands. |
| `CitationPresent` / `CitationCount` | Citation source entries and URLs detected in the response. |
| `CompetitorMentionCount` | Number of recognised competitor organisations present in the response. |
| `AssociationLabel` / `AssociationScore` | Target-context lexicon result: Positive, Neutral, Negative or Not mentioned. |
| `EvidenceConfidence` | High when mentioned and cited, Medium when mentioned without a citation, otherwise Low. |

These are measurement signals, not claims of factual truth. The original response remains the audit source, and the rules are covered by automated tests.
