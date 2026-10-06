# Recommendation methodology

## Purpose

The Recommendations page converts observed gaps into testable interventions. It does not claim access to proprietary foundation-model ranking, training, or retrieval logic, and it does not forecast guaranteed uplift.

Each recommendation records the measured baseline, intervention level, affected signal, rationale, evidence strength, target calculation, validation method, and confidence.

## Intervention levels

- **Firm-wide:** an issue present across the selected benchmark, such as weak overall discovery or citation coverage.
- **Sector/service:** a subject-specific gap supported by the corresponding prompt subset.
- **Market:** a location-specific gap supported by the corresponding market subset.
- **Persona:** an audience-specific gap supported by the corresponding persona subset.
- **Model/platform:** a sufficiently sampled difference that requires model-specific diagnosis before action.

These labels prevent a local segment finding from being presented as a firm-wide conclusion.

## Target calculation

For binary measures such as mentions or citation presence:

1. The baseline is shown as both a count and a rate.
2. Samples below 30 responses are labelled directional and receive no percentage uplift target.
3. For samples of 30 or more, the tool finds the smallest next-run success count whose upper-tail probability is at most 5% under a binomial model using the observed baseline rate.
4. The result is labelled a **measurement threshold, not a forecast**.
5. The same prompts, models, and scoring rules must be used in the rerun, and the signal must repeat in a second matched rerun before it is treated as sustained evidence.

The binomial calculation is an indicative benchmark. Foundation-model responses are not perfectly independent, and content changes, model updates, retrieval changes, and sampling variability can all affect results. Meeting the threshold therefore does not prove that the intervention caused the change.

For rank and other non-binary outcomes, the tool does not invent a numeric uplift. It requires matched observation and repeated evidence.

## Evidence basis and limitations

The intervention rationales use documented retrieval principles while treating model-output effects as experimental:

- Google documents crawling, indexing, and serving as separate stages and states that compliance does not guarantee that a page will be crawled, indexed, or served: <https://developers.google.com/search/docs/fundamentals/how-search-works>
- Google documents crawlable links and descriptive anchor text as mechanisms that help systems find pages and understand linked content: <https://developers.google.com/search/docs/crawling-indexing/links-crawlable>
- Google recommends helpful, reliable, people-first content that demonstrates expertise and provides original, substantive information: <https://developers.google.com/search/docs/fundamentals/creating-helpful-content>
- Google states that even technically eligible pages are not guaranteed to be indexed: <https://developers.google.com/search/docs/essentials/technical>

These sources support discoverability and content-quality practices. They do not establish a direct causal rule for inclusion in every foundation-model response. The application therefore labels actions as supported practice, evidence-led hypothesis, diagnostic hypothesis, or experimental hypothesis as appropriate.

## Interpretation

A recommendation is decision support, not a promise. A credible claim of improvement requires:

- a fixed or explicitly versioned prompt bank;
- the same model set and scoring rules;
- an adequate sample;
- recorded intervention dates;
- a matched post-intervention rerun; and
- replication before causal language is used.
