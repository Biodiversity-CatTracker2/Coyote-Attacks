import datetime
import os
import webbrowser

import streamlit as st
import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

from pygon import Search, ExportData, Count


class DB:
    def __init__(self, conn_string):
        self.conn_string = conn_string

    def select(self, db_name):
        args = {
            'dbname': db_name,
            'sslrootcert': 'DigiCertGlobalRootCA.crt.pem',
            'sslmode': 'verify-full'
        }
        db = sqlalchemy.create_engine(self.conn_string, connect_args=args)
        return db


def keywords(l):
    return ', '.join([f'`{x}`' for x in l])


def main(min_, max_):

    col1, col2 = st.columns(2)
    today_ = datetime.datetime.today()
    with col1:
        from_date = st.sidebar.date_input('From',
                                          today_ - datetime.timedelta(days=30),
                                          key=0,
                                          min_value=min_[0][2],
                                          max_value=max_[0][2])
    with col2:
        to_date = st.sidebar.date_input('To',
                                        max_[0][2],
                                        key=1,
                                        min_value=min_[0][2],
                                        max_value=max_[0][2])

    language = st.sidebar.selectbox(
        'Language', ('English (US/Canada)', 'Spanish (México)'))

    language = 'en' if language == 'English (US/Canada)' else 'es'
    country = 'US' if language == 'en' else 'MX'

    kwargs = {
        'from_date': from_date,
        'to_date': to_date,
        'language': language,
        'country': country,
    }

    return kwargs


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


@st.cache(allow_output_mutation=True)
def load_db():
    psql = DB(os.environ['AZURE_POSTGRES_DB_STRING'])
    db = psql.select('postgres').connect()
    min_ = db.execute(
        f'SELECT * FROM articles ORDER BY published ASC LIMIT 1;').fetchall()
    max_ = db.execute(
        f'SELECT * FROM articles ORDER BY published DESC LIMIT 1;').fetchall()
    return db, min_, max_


def set_footer():
    hide_streamlit_style = """<style>
		footer {visibility: hidden;}
		footer::before {
			content:'© 2021 | NC State University & NC Museum of Natural Sciences | Developed and Maintained by Mohammad Alyetama'; 
			visibility: visible;
			position: fixed;
			left: 1;
			right: 1;
			bottom: 0;
			text-align: center;
			# color: green;
		}
	</style>"""
    return st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def badge(name, image, link):
    return f'<a href="{link}" target="_blank"><img alt="{name}" src="{image}"></a>'


if __name__ == '__main__':
    st.set_page_config(page_title='NCSU Biodiversity Lab: Coyote Search',
    page_icon='🐺',
    layout='wide',
    initial_sidebar_state='auto',
    menu_items={
    'About': '#### [PyGon](https://github.com/Biodiversity-CatTracker2/PyGoN)\n'
    '###### NC State University & NC Museum of Natural Sciences\n' \
    'Maintained by [Mohammad Alyetama](https://github.com/Alyetama)\n' \
    '---'})

    set_footer()

    load_dotenv()
    streamlit_badge = badge(
        'Streamlit',
        'https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white',
        'https://streamlit.io')
    python_badge = badge(
        'Python 3.10.0rc1',
        'https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=darkgreen',
        'https://www.python.org/')
    postgres_badge = badge(
        'PostgreSQL',
        'https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white',
        'https://www.postgresql.org/')
    docker_badge = badge(
        'Docker',
        'https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white',
        'https://www.docker.com/')
    azure_badge = badge(
        'Microsoft Azure',
        'https://img.shields.io/badge/microsoft%20azure-0089D6?style=for-the-badge&logo=microsoft-azure&logoColor=white',
        'https://azure.microsoft.com')

    st.sidebar.write('')
    db, min_, max_ = load_db()
    if st.sidebar.button('Source code 💻'):
        webbrowser.open_new_tab(
            'https://github.com/Biodiversity-CatTracker2/PyGoN')

    if st.sidebar.button('Report a bug 🐛'):
        webbrowser.open_new_tab(
            'mailto:malyeta@ncsu.edu?subject=Bug%20Report%20%28Coyotes%20News%20Web%20App%29'
        )
    st.sidebar.markdown('---')
    kwargs = main(min_, max_)

    if kwargs.get('language') == 'en':
        db_table = 'articles'
    else:
        db_table = 'articles_es'
    df = pd.read_sql(
        f"SELECT * FROM {db_table} WHERE published BETWEEN \'{kwargs.get('from_date')}\' AND \'{kwargs.get('to_date')}\';",
        db)

    df.rename(columns=dict([(x, x.capitalize()) for x in df.columns]),
              inplace=True)
    placeholder = st.empty()
    placeholder_1 = st.empty()

    if len(df) > 300:
        placeholder.warning('Date range is too wide. Select a narrower range!')
        if placeholder_1.button('Run anyway... (not recommended ⚠️)'):
            placeholder_1.empty()
            placeholder.markdown(df.to_markdown())
    else:
        st.markdown(df.to_markdown())

    st.sidebar.markdown('---')
    st.sidebar.subheader('Request')
    res = kwargs
    res.update({'total_results_count': len(df)})
    st.sidebar.json(kwargs)
    st.sidebar.markdown('---')
    download_file_button(df)
