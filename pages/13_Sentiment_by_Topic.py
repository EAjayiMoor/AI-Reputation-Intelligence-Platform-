import streamlit as st
from src.ui import (apply_filters, apply_moorhouse_theme, apply_prompt_scope_filter,
    load_core_data, render_empty_state_guidance, render_page_header,
    render_prompt_scope_selector, render_sidebar_filters, require_active_tenant)
from src.ui.sentiment import render_sentiment

st.set_page_config(page_title='Sentiment by topic',page_icon=':material/sentiment_satisfied:',layout='wide')
apply_moorhouse_theme()
tenant=require_active_tenant()
render_page_header('Sentiment by topic','Explore model portrayals with supporting response evidence',eyebrow='Reputation analysis')
scope=render_prompt_scope_selector(key='sentiment_scope')
try:
    _,_,frame=load_core_data(org_id=tenant.org_id)
except (OSError,ValueError) as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()
frame=apply_prompt_scope_filter(frame,scope=scope)
if frame.empty:
    render_empty_state_guidance(tenant,area='Sentiment by topic')
    st.stop()
filters=render_sidebar_filters(frame,key_prefix='sentiment_live_v1')
render_sentiment(apply_filters(frame,filters),tenant)
