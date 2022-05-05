import hashlib
import os
from datetime import datetime

import sqlalchemy
from dotenv import load_dotenv

import pygon


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


def hash(input_):
    hash_object = hashlib.md5(str(input_).encode())
    return hash_object.hexdigest()


def main():
    psql = DB(os.environ['AZURE_POSTGRES_DB_STRING'])
    db = psql.select('postgres').connect()

    languages = {
        'spanish': {
            'table':
            'articles_es',
            'language':
            'es',
            'country':
            'MX',
            'query':
            'coyote (mordida OR ataque OR caza OR agresivo OR mordisco) intitle:coyote'
        },
        'english': {
            'table':
            'articles',
            'language':
            'en',
            'country':
            'US',
            'query':
            'coyote (bite OR attack OR kill OR chase OR aggressive OR nip) intitle:coyote'
        }
    }

    for language in languages:

        kwargs = {
            'query': query,
            'month': int(datetime.now().strftime('%m')),
            'year': int(datetime.now().strftime('%Y')),
            'language': language,
            'country': country,
            'testing': False,
            'silent': True
        }

        try:
            search = pygon.Search(**kwargs)
            results = search.run()
            export = pygon.ExportData(results, **kwargs)
            df = export._to_pandas()
            del df['Id'], df['Source']
            df['Summary'] = df.Summary.apply(export.remove_bad_chars)
            df['Title'] = df.Title.apply(export.remove_bad_chars)
            df['Link'] = df.Link.apply(export.md_link)
            df['Keywords'] = df.Keywords.apply(export.style_keywords)
            df['Index'] = [hash(x) for x in df['Title']]
            df.rename(columns=dict([(x, x.lower()) for x in df.columns]),
                      inplace=True)
            df.set_index('index', inplace=True)
            md = df.to_markdown()
            df.to_sql(table, db, if_exists='append', index=False)
        except pygon.NoEntriesExit:
            continue


if __name__ == '__main__':
    load_dotenv()
    main()
