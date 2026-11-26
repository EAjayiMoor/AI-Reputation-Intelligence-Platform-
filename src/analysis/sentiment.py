"""Indicative, auditable target sentiment grouped by existing prompt topics.

This is a text-rule measurement, not an LLM judgement or customer sentiment.
"""
from __future__ import annotations

import re
import pandas as pd
from src.analysis.response_parser import organisation_name_pattern

METHOD = 'Target text rules v1'
LABELS = ('Positive', 'Neutral', 'Negative', 'Mixed', 'Not discussed')
POSITIVE = set('admired best better good great competitive credible distinctive effective excellent leading preferred reliable respected strong successful trusted innovative recommended collaborative affordable helpful comfortable consistent friendly responsive valuable outstanding enjoyable efficient'.split())
NEGATIVE = set('behind concern concerns controversial disappointing expensive inconsistent limited negative poor risk unclear unproven weak unreliable bad worse worst overpriced unhelpful rude uncomfortable delays cancellations disruption disrupted inefficient fails lacking'.split())


def classify_sentiment(text, organisation_name, aliases=(), competitors=None):
    text = '' if text is None or pd.isna(text) else str(text)
    target = re.compile(organisation_name_pattern(organisation_name, aliases), re.I)
    other_names = [name for canonical, values in (competitors or {}).items() for name in [canonical, *values]]
    other = re.compile(organisation_name_pattern('', other_names), re.I) if other_names else None
    if not target.search(text):
        return dict(Sentiment='Not discussed', SentimentEvidence='', SentimentSignals='', SentimentReview=False, SentimentMethod=METHOD)
    if re.search(r"(?:don['’]t have access|do not have access|cannot (?:assess|judge|verify)|can['’]t (?:assess|judge|verify))", text[:400], re.I):
        return dict(Sentiment='Neutral', SentimentEvidence=text[:2000],
                    SentimentSignals='Insufficient information: review required',
                    SentimentReview=True, SentimentMethod=METHOD)
    positive, negative, evidence, signals = False, False, [], []
    active, review = False, False
    for chunk in re.split(r'(?<=[.!?])\s+|\r?\n+', text):
        for clause in re.split(r';|\s+(?:but|while|whereas|however|although)\s+', chunk, flags=re.I):
            mentions = bool(target.search(clause))
            competitor = bool(other and other.search(clause))
            if competitor:
                active = mentions
                if mentions:
                    review = True
                    evidence.append(clause.strip())
                # Comparative attribution is ambiguous; don't count rival adjectives.
                continue
            if mentions:
                active = True
            if not active or not clause.strip():
                continue
            evidence.append(clause.strip())
            if re.search(r'\b(?:if|could|might|may|perhaps|than|not always)\b', clause, re.I):
                review = True
            words = re.findall(r"[a-z]+", clause.casefold().replace('’', chr(39)).replace("n't", ' not').replace('not only', ''))
            for index, word in enumerate(words):
                if word not in POSITIVE and word not in NEGATIVE:
                    continue
                negated = any(w in {'not','never','no','without','hardly'} for w in words[max(0,index-3):index])
                is_positive = (word in POSITIVE) != negated
                positive |= is_positive
                negative |= not is_positive
                signals.append(('Positive: ' if is_positive else 'Negative: ') + ('negated ' if negated else '') + word)
    label = 'Mixed' if positive and negative else 'Positive' if positive else 'Negative' if negative else 'Neutral'
    return dict(Sentiment=label, SentimentEvidence=' '.join(evidence)[:2000],
                SentimentSignals='; '.join(dict.fromkeys(signals)),
                SentimentReview=review or label in {'Neutral','Mixed'}, SentimentMethod=METHOD)


def enrich_sentiment(frame, organisation_name, aliases=(), competitors=None):
    result = frame.copy()
    records = [classify_sentiment(row.get('ResponseText'), organisation_name, aliases, competitors)
               for _, row in frame.iterrows()]
    for column in ['Sentiment','SentimentEvidence','SentimentSignals','SentimentReview','SentimentMethod']:
        result[column] = [r[column] for r in records]
    return result


def sentiment_summary(frame, topic='Subject', by_model=False):
    groups = [topic, 'ModelName'] if by_model and topic != 'ModelName' else [topic]
    columns = [*groups, 'Responses', 'Discussed', *LABELS, 'Review suggested',
               *[label+' %' for label in LABELS if label != 'Not discussed']]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    working = frame.copy()
    for column in groups:
        if column not in working:
            working[column] = 'Unspecified'
        working[column] = working[column].fillna('').astype(str).replace('', 'Unspecified')
    records = []
    for key, rows in working.groupby(groups, dropna=False, sort=True):
        keys = key if isinstance(key, tuple) else (key,)
        counts = rows.Sentiment.value_counts()
        record = dict(zip(groups,keys))
        discussed = int(len(rows)-counts.get('Not discussed',0))
        record.update(Responses=len(rows), Discussed=discussed)
        record.update({label:int(counts.get(label,0)) for label in LABELS})
        record['Review suggested'] = int(rows.SentimentReview.sum())
        record.update({label+' %': 100*record[label]/discussed if discussed else None
                       for label in LABELS if label!='Not discussed'})
        records.append(record)
    return pd.DataFrame(records, columns=columns)
