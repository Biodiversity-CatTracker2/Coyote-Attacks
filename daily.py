#!/usr/bin/env python
# coding: utf-8

# NOT FOR USE IN PRODUCTION!!

import datetime
import hashlib
import os
import signal
import sys
from datetime import datetime

import nltk
import numpy as np
import pandas as pd
import ray
import requests
import sqlalchemy
from dotenv import load_dotenv
from tqdm import tqdm

import google_news_api


class DB:

    def __init__(self, conn_string):
        self.conn_string = conn_string

    def select(self, db_name):
        args = {
            'dbname': db_name,
            # 'sslrootcert': 'certs/DigiCertGlobalRootCA.crt.pem',
            # 'sslmode': 'verify-full'
        }
        db = sqlalchemy.create_engine(self.conn_string, connect_args=args)
        return db


def keyboard_interrupt_handler(sig: int, _) -> None:
    print(f'KeyboardInterrupt (id: {sig}) has been caught...')
    print('Terminating the session gracefully...')
    sys.exit(1)


def _hash(x):
    return hashlib.md5(x.encode('utf-8')).hexdigest()


@ray.remote
def loop(vals, year, month):
    if month > int(datetime.now().strftime('%m')) or year > int(
            datetime.now().strftime('%Y')):
        return

    kwargs = {
        'query': vals['query'],
        'month': month,
        'year': year,
        'language': vals['language'],
        'country': vals['country'],
        'testing': False,
        'silent': True
    }

    try:
        search = google_news_api.Search(**kwargs)
        results = search.run()
        export = google_news_api.ExportData(results, **kwargs)
        df = export._to_pandas()
        df.drop(columns=['Id', 'Source'], inplace=True)
        df['Summary'] = df.Summary.apply(export.remove_bad_chars)
        df['Title'] = df.Title.apply(export.remove_bad_chars)
        df['Link'] = df.Link.apply(export.md_link)
        df['Keywords'] = df.Keywords.apply(export.style_keywords)
        df['Index'] = df.Title.apply(_hash)
        df.rename(columns=dict([(x, x.lower()) for x in df.columns]),
                  inplace=True)
        df.set_index('index', inplace=True)
        return df
    except google_news_api.NoEntriesExit:
        return


def google_news():
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    psql = DB(os.environ['POSTGRES_CON_STRING'])
    db = psql.select('postgres').connect()

    languages = {
        'english': {
            'table':
            'articles',
            'language':
            'en',
            'country':
            'US',
            'query':
            'coyote (bite OR attack OR kill OR chase OR aggressive OR nip) '
            'intitle:coyote'
        },
        'spanish': {
            'table':
            'articles_es',
            'language':
            'es',
            'country':
            'MX',
            'query':
            'coyote (mordida OR ataque OR caza OR agresivo OR mordisco) '
            'intitle:coyote'
        }
    }

    for language, vals in languages.items():
        for year in tqdm(range(2010, 2024), desc='Years'):

            futures = []
            for month in range(1, 13):
                futures.append(loop.remote(vals, year, month))

            presents = []
            for future in tqdm(futures, desc='Futures'):
                presents.append(ray.get(future))

            for df in tqdm(presents, desc='Presents'):
                if df is not None:
                    existing_ids = []
                    try:
                        for idx in df.index:
                            res = db.execute(
                                f'SELECT index FROM articles WHERE \'{idx}\' ~ '
                                'index;').one_or_none()
                            if res:
                                existing_ids.append(idx)
                    except sqlalchemy.exc.ProgrammingError:
                        pass
                    df = df[~df.index.isin(existing_ids)]
                    df.to_sql(vals['table'],
                              db,
                              if_exists='append',
                              index=True)


def bing_news():
    psql = DB(os.environ['AZURE_POSTGRES_DB_STRING'])
    db = psql.select('postgres').connect()

    subscription_key = os.environ['BING_SEARCH_V7_SUBSCRIPTION_KEY']
    endpoint = os.environ['BING_SEARCH_V7_ENDPOINT']
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}

    query = "coyote (bite OR attack OR kill OR chase OR aggressive OR nip) intitle:coyote"

    for mkt in tqdm(['en-CA', 'en-US']):
        params = {'q': query, 'mkt': mkt, 'count': 100, 'sortBy': 'Date'}

        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()

            res = response.json()['value']
            df = pd.DataFrame.from_dict(res)

            types_ = {
                'name': 'string',
                'url': 'string',
                'datePublished': 'datetime64[ns]',
            }

            types_ = {k: v for k, v in types_.items() if k in list(df.columns)}
            df = df.astype(types_)

            df.rename(columns={
                'name': 'title',
                'url': 'link',
                'datePublished': 'published'
            },
                      inplace=True)
            df['summary'] = np.nan
            df['keywords'] = np.nan

            print(df)
            df['index'] = df['title'].apply(_hash)

            df = df[[
                'index', 'title', 'link', 'published', 'keywords', 'summary'
            ]]

            df['link'] = df.link.apply(lambda link: f'[Link]({link})')
            df['published'] = df['published'].apply(lambda x: x.date())
            df.set_index('index', inplace=True)

            existing_ids = []
            q_p = 'SELECT index FROM articles WHERE'
            for idx in df.index:
                q = f'{q_p} \'{idx}\' ~ index;'
                res = db.execute(q).fetchall()
                if res:
                    existing_ids.append(idx)
            df = df[~df.index.isin(existing_ids)]
        except Exception as e:
            print('Unexpected exception!', '>' * 58)
            print(e)
            print('<' * 58, 'Unexpected exception!')


if __name__ == '__main__':
    load_dotenv()
    nltk.download('punkt')
    google_news()
    # bing_news()
