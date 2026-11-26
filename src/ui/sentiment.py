"""Shared sentiment panel; data stays in the selected workspace/run."""
import altair as alt
import streamlit as st
from src.analysis.sentiment import enrich_sentiment, sentiment_summary, LABELS


def render_sentiment(frame, tenant):
    st.subheader('Sentiment by topic')
    st.caption(f'Indicative sentiment towards {tenant.display_name} in model responses, not customer sentiment. '
               'Topics come from the prompt bank; a response is grouped under its prompt topic, not split into inferred aspects.')
    with st.expander('How sentiment is measured'):
        st.write('Target text rules v1 looks for positive and negative wording in organisation-specific text, '
                 'including common negations. Mixed retains both positive and negative signals. '
                 'Neutral means no recognised polarity or an explicit inability to judge; Not discussed means the organisation is absent. '
                 'Comparisons involving competitors are flagged for review. Sarcasm, implicit references and '
                 'complex comparisons can be missed; review the excerpts and original responses before drawing conclusions. '
                 'These labels do not change the existing reputation score. No additional model calls are made.')
    evidence = enrich_sentiment(frame, tenant.display_name, tenant.aliases, tenant.competitors.aliases_by_name)
    topics = [c for c in ['Subject','Category','ExpertiseArea'] if c in frame and frame[c].fillna('').astype(str).str.strip().ne('').any()]
    if not topics:
        topics = ['Subject']
    topic = st.selectbox('Topic grouping',topics,key='sentiment_topic')
    summary = sentiment_summary(evidence,topic)
    if summary.empty:
        st.info('No saved responses match these filters.')
        return
    discussed = int(summary.Discussed.sum())
    cols = st.columns(3)
    cols[0].metric('Responses in view',len(evidence))
    cols[1].metric('Organisation discussed',discussed)
    cols[2].metric('Not discussed',len(evidence)-discussed)
    st.caption('Sentiment percentages use discussed responses only (including Mixed). '
               'No discussed responses means percentages are unavailable. Chart bars show counts, including absence.')
    chart_rows = summary.sort_values('Responses',ascending=False).head(20)
    if len(summary)>20:
        st.caption(f'Chart shows the 20 largest of {len(summary)} topics. The table and downloads include every topic.')
    chart = chart_rows[[topic, *LABELS]].melt(id_vars=[topic],value_vars=list(LABELS),var_name='Sentiment',value_name='Responses')
    st.altair_chart(alt.Chart(chart).mark_bar().encode(
        y=alt.Y(f'{topic}:N',title='Prompt topic'),x=alt.X('Responses:Q',title='Responses'),
        color=alt.Color('Sentiment:N',scale=alt.Scale(domain=list(LABELS),range=['#008573','#9b9b9b','#b44248','#8762aa','#dedede'])),
        tooltip=[topic,'Sentiment','Responses']).properties(height=max(260,min(800,len(chart_rows)*35))))
    st.dataframe(summary,hide_index=True)
    st.download_button('Download sentiment summary (CSV)',summary.to_csv(index=False).encode('utf-8'),
                       file_name=f'{tenant.org_id}_sentiment_by_topic.csv',mime='text/csv',on_click='ignore')
    if 'ModelName' in evidence:
        with st.expander('Compare models by topic'):
            st.dataframe(sentiment_summary(evidence,topic,by_model=True),hide_index=True)
    st.subheader('Sentiment evidence')
    label = st.selectbox('Sentiment to inspect',['All',*LABELS],key='sentiment_evidence_label')
    selected = evidence if label=='All' else evidence[evidence.Sentiment.eq(label)]
    columns = [c for c in ['ResultID','RunBatchID','PromptID','ModelName',topic,'Sentiment','SentimentReview','SentimentEvidence','SentimentSignals','SentimentMethod','ResponseText'] if c in selected]
    columns = list(dict.fromkeys(columns))
    st.dataframe(selected[columns],hide_index=True,column_config={
        'ResultID':'Result ID','RunBatchID':'Run ID','PromptID':'Prompt ID','ModelName':'Model','SentimentReview':'Review suggested',
        'SentimentEvidence':'Evidence excerpt','SentimentSignals':'Detected wording',
        'SentimentMethod':'Method','ResponseText':'Original response'})
    st.download_button('Download sentiment evidence (CSV)',selected[columns].to_csv(index=False).encode('utf-8'),
                       file_name=f'{tenant.org_id}_sentiment_evidence.csv',mime='text/csv',on_click='ignore')
    if not selected.empty:
        index = st.selectbox('Read original response',list(range(len(selected))),
            format_func=lambda i:f"{selected.iloc[i].get('PromptID','Response')} · {selected.iloc[i].get('ModelName','')} · {selected.iloc[i].Sentiment}",key='sentiment_original')
        row=selected.iloc[index]
        st.caption('Review suggested' if row.SentimentReview else 'Inspect the original response to verify the label.')
        st.text(str(row.get('ResponseText','')))
