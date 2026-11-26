import pandas as pd
import pytest
from src.analysis.sentiment import classify_sentiment, sentiment_summary, enrich_sentiment


@pytest.mark.parametrize('text,expected', [
    ('British Airways offers excellent service.', 'Positive'),
    ('BA is unreliable and expensive.', 'Negative'),
    ('British Airways flies from London.', 'Neutral'),
    ('British Airways has excellent service but poor value.', 'Mixed'),
    ('British Airways is not reliable.', 'Negative'),
    ('British Airways is not bad.', 'Positive'),
    ('British Airways is not only reliable but excellent.', 'Positive'),
    ('Virgin Atlantic is excellent. British Airways flies from London.', 'Neutral'),
    ('British Airways is reliable; Virgin Atlantic is poor.', 'Positive'),
    ('Virgin Atlantic is excellent.', 'Not discussed'),
    ('', 'Not discussed'),
    ('**British Airways**\n- Excellent service.\n- Poor value.', 'Mixed'),
    ('British Airways offers excellent service.\n**Virgin Atlantic**\nPoor reliability.', 'Positive'),
])
def test_target_sentiment(text, expected):
    result=classify_sentiment(text,'British Airways',('BA',),{'Virgin Atlantic':()})
    assert result['Sentiment']==expected
    if expected=='Not discussed':
        assert result['SentimentEvidence']==''


def test_missing_and_competitor_comparison_is_flagged():
    row=classify_sentiment('British Airways is worse than Virgin Atlantic.','British Airways',('BA',),{'Virgin Atlantic':()})
    assert row['SentimentReview']
    assert classify_sentiment(None,'British Airways')['Sentiment']=='Not discussed'


def test_summary_denominators_mixed_absence_and_no_mutation():
    frame=pd.DataFrame({'PromptID':['A','B','C','D','E'],'Subject':['Service']*4+['Loyalty'],
        'ResponseText':['BA is excellent.','BA is poor.','BA is excellent but expensive.','Virgin Atlantic is great.','No mention.'],
        'ModelName':['one']*5})
    original=frame.copy(deep=True)
    evidence=enrich_sentiment(frame,'British Airways',('BA',))
    summary=sentiment_summary(evidence,'Subject').set_index('Subject')
    row=summary.loc['Service']
    assert row['Responses']==4 and row['Discussed']==3 and row['Not discussed']==1
    assert row['Positive']==row['Negative']==row['Mixed']==1
    assert row['Positive %']==pytest.approx(100/3)
    assert pd.isna(summary.loc['Loyalty','Positive %'])
    pd.testing.assert_frame_equal(frame,original)
    assert sentiment_summary(evidence.iloc[:0],'Subject').empty


def test_explicit_inability_to_judge_is_review_not_negative():
    row=classify_sentiment("I don't have access to current, specific data about British Airways. Passengers should expect good service during poor weather.",'British Airways')
    assert row['Sentiment']=='Neutral'
    assert row['SentimentReview']


@pytest.mark.parametrize('text,label',[
    ("BA isn't reliable.",'Negative'),
    ("BA can't be recommended.",'Negative'),
    ("BA is not unreliable.",'Positive'),
])
def test_contracted_negation(text,label):
    assert classify_sentiment(text,'British Airways',('BA',))['Sentiment']==label
