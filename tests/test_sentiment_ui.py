from streamlit.testing.v1 import AppTest


def test_sentiment_view_shows_topic_model_evidence_and_exports():
    app = AppTest.from_string('''
import pandas as pd
from src.tenants import load_tenant
from src.ui.sentiment import render_sentiment
frame=pd.DataFrame([
 {'PromptID':'BA1','Subject':'Service','Category':'Cabin','ModelName':'model-a','ResponseText':'British Airways is excellent.'},
 {'PromptID':'BA2','Subject':'Value','Category':'Fares','ModelName':'model-b','ResponseText':'BA is expensive.'},
 {'PromptID':'BA3','Subject':'Service','Category':'Cabin','ModelName':'model-a','ResponseText':'Virgin Atlantic is good.'}])
render_sentiment(frame,load_tenant('british_airways'))
''', default_timeout=30).run()
    assert not app.exception
    assert any('Sentiment by topic' in element.value for element in app.subheader)
    assert len(app.dataframe)>=2
    assert len(app.get('download_button'))==2
    app.selectbox(key='sentiment_topic').set_value('Category').run()
    assert not app.exception
    assert 'Category' in app.dataframe[0].value.columns
    app.selectbox(key='sentiment_evidence_label').set_value('Negative').run()
    assert not app.exception
    assert any('BA is expensive.' in element.value for element in app.text)
