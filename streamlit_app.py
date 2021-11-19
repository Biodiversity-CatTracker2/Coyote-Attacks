import datetime

import streamlit as st
import pandas as pd
from pygon import Search, ExportData, Count


def style():
    padding_top = 5
    padding_right = 1
    padding_left = 1
    padding_bottom = 10

    st.markdown(
        f"""
    <style>
        .reportview-container .main .block-container{{
            padding-top: {padding_top}rem;
            padding-right: {padding_right}rem;
            padding-left: {padding_left}rem;
            padding-bottom: {padding_bottom}rem;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def keywords(l):
    return ', '.join([f'`{x}`' for x in l])


def main():
    query = st.sidebar.text_input('Query')

    col1, col2 = st.columns(2)
    with col1:
        from_date = st.sidebar.date_input('From',
                                          datetime.date(2019, 1, 1),
                                          key=0)
    with col2:
        to_date = st.sidebar.date_input('To', datetime.datetime.today(), key=1)

    language = st.sidebar.selectbox(
        'Language', ('English (US/Canada)', 'Spanish (México)'))

    language = 'en' if language == 'English (US/Canada)' else 'es'
    country = 'US' if language == 'en' else 'MX'

    kwargs = {
        'query': query,
        'month': from_date.month,
        'year': from_date.year,
        'language': language,
        'country': country,
        'testing': False,
        'silent': True
    }

    return kwargs


def return_md_table(export_res):
    df = export._to_pandas()
    del df['Id'], df['Source']
    # df['Source'] = df.Source.apply(export.source)
    df['Summary'] = df.Summary.apply(export.remove_bad_chars)
    df['Title'] = df.Title.apply(export.remove_bad_chars)
    df['Link'] = df.Link.apply(export.md_link)
    df['Keywords'] = df.Keywords.apply(keywords)
    md = df.to_markdown()
    return df, md


@st.cache(persist=True)
def convert_df(df):
    return df.to_csv().encode('utf-8')


def download_file_button(df):
    df = convert_df(df)
    st.sidebar.download_button(
        label="Download data as CSV",
        data=df,
        file_name='results.csv',
        mime='text/csv',
    )


if __name__ == '__main__':
    style()
    kwargs = main()
    print(kwargs)
    if kwargs.get('query'):
    	search = Search(**kwargs)
    	results = search.run()
    	export = ExportData(results, **kwargs)
    	df, md = return_md_table(export)

    	with st.container():
        	st.markdown(md)

    	st.sidebar.subheader('Request')
    	res = {k: v for k, v in kwargs.items() if k not in ['testing', 'silent']}
    	st.sidebar.write(res)
    	download_file_button(df)
