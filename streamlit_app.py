import datetime
import os

import dateparser
import streamlit as st
import pandas as pd
import sqlalchemy
from bokeh.models.widgets import Div
from dotenv import load_dotenv

from style import Style


class DB:
    def __init__(self, conn_string):
        self.conn_string = conn_string

    def select(self, db_name):
        args = {
            'dbname': db_name,
            'sslrootcert': 'certs/DigiCertGlobalRootCA.crt.pem',
            'sslmode': 'verify-full'
        }
        db = sqlalchemy.create_engine(self.conn_string, connect_args=args)
        return db


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
    load_dotenv()
    psql = DB(os.environ['AZURE_POSTGRES_DB_STRING'])
    db = psql.select('postgres').connect()
    min_ = db.execute(
        f'SELECT * FROM articles ORDER BY published ASC LIMIT 1;').fetchall()
    max_ = db.execute(
        f'SELECT * FROM articles ORDER BY published DESC LIMIT 1;').fetchall()
    return db, min_, max_


def page_config():
    st.set_page_config(page_title='NCSU Biodiversity Lab: Coyote Search',
    page_icon='favicon.ico',
    layout='wide',
    initial_sidebar_state='auto',
    menu_items={
    'Get help': None,
    'Report a Bug': None,
    'About': '#### [PyGon](https://github.com/Biodiversity-CatTracker2/PyGoN)\n'
    '###### NC State University & NC Museum of Natural Sciences\n' \
    'Maintained by [Mohammad Alyetama](https://github.com/Alyetama)\n' \
    '---'})
    style = Style()
    st.markdown(style.set_footer(), unsafe_allow_html=True)
    st.markdown(style.get_badges(), unsafe_allow_html=True)
    st.sidebar.image(
        'https://brand.ncsu.edu/assets/logos/ncstate-brick-4x1-blk.png')
    st.sidebar.write('')
    if st.sidebar.button('Source code 💻'):
        js = "window.open('https://github.com/Biodiversity-CatTracker2/PyGoN')"
        html = f'<img src onerror="{js}">'
        div = Div(text=html)
        st.bokeh_chart(div)

    if st.sidebar.button('Report a bug 🐛'):
        js = "window.open('mailto:malyeta@ncsu.edu?subject=Bug%20Report%20%28Coyotes%20News%20Web%20App%29')"
        html = f'<img src onerror="{js}">'
        div = Div(text=html)
        st.bokeh_chart(div)
    st.sidebar.markdown('---')


def main(min_, max_):
    col1, col2 = st.columns(2)
    today_ = datetime.datetime.today()
    with col1:
        from_date = st.sidebar.date_input('From',
                                          today_ - datetime.timedelta(days=30),
                                          key=0,
                                          min_value=dateparser.parse(min_[0][2]),
                                          max_value=dateparser.parse(max_[0][2]))
    with col2:
        to_date = st.sidebar.date_input('To',
                                        dateparser.parse(max_[0][2]),
                                        key=1,
                                        min_value=dateparser.parse(min_[0][2]),
                                        max_value=dateparser.parse(max_[0][2]))

    language = st.sidebar.selectbox(
        'Language', ('English (US/Canada)', 'Spanish (México)'))

    language = 'en' if language == 'English (US/Canada)' else 'es'
    country = 'US' if language == 'en' else 'MX'

    if language == 'en':
        query = 'coyote (bite OR attack OR kill OR chase OR aggressive OR nip) intitle:coyote'
    else:
        query = 'coyote (mordida OR ataque OR caza OR agresivo OR mordisco) intitle:coyote'

    kwargs = {
        'query': query,
        'from_date': from_date,
        'to_date': to_date,
        'language': language,
        'country': country,
    }
    return kwargs


if __name__ == '__main__':
    #-------------------------------------------------------------------------
    page_config()
    #-------------------------------------------------------------------------
    db, min_, max_ = load_db()
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
    del df['Index']
    df.reset_index(drop=True, inplace=True)
    placeholder = st.empty()
    placeholder_1 = st.empty()

    if len(df) > 300:
        placeholder.warning('Date range is too wide. Select a narrower range!')
        if placeholder_1.button('Run anyway...'):
            placeholder_1.empty()
            placeholder.markdown(df.to_markdown())
    else:
        st.markdown(df.to_markdown())
    #-------------------------------------------------------------------------
    st.sidebar.markdown('---')
    st.sidebar.subheader('Request')
    kwargs.update({'query_results_count': len(df)})
    st.sidebar.json(kwargs)
    #-------------------------------------------------------------------------
    st.sidebar.markdown('---')
    download_file_button(df)
    #-------------------------------------------------------------------------
    st.sidebar.markdown('<p><small><a href="https://www.flaticon.com/premium-icon/coyote_2128189">Favicon source</a></small></p>', unsafe_allow_html=True)
