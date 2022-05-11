#!/usr/bin/env python3
# coding: utf-8

import json
from datetime import datetime

from bs4 import BeautifulSoup

from google_news_api import Search, ExportData, NoEntriesError


def main(query: str, language: str = 'en', country: str = 'US') -> None:
    for yr in range(2019, 2024):
        if yr > int(datetime.now().strftime('%Y')):
            return
        for mo in range(1, 13):

            if mo > int(datetime.now().strftime('%m')) and yr == int(
                    datetime.now().strftime('%Y')):
                return

            kwargs = {
                'query': query,
                'month': mo,
                'year': yr,
                'language': language,
                'country': country.upper(),
                'testing': False,
                'silent': True
            }
            search = Search(**kwargs)
            results = search.run()
            try:
                export = ExportData(results, **kwargs)
                export.to_html(to_ghpages=True)
            except NoEntriesError:
                pass

            cur_data = json.loads(json.dumps(results.raw, ensure_ascii=False))
            if mo <= 9:
                mo = f'0{mo}'

            with open(f'docs/{yr}/{language.upper()}/results_{yr}_{mo}.html'
                      ) as h:
                html_content = h.read()
            table_content = [[
                cell.text for cell in row('td')
            ] for row in BeautifulSoup(html_content, 'lxml')('tr')][1:]
            prev_len = len(table_content)
            cur_len = len(cur_data['entries'])
            if prev_len != cur_len:
                try:
                    export = ExportData(results, **kwargs)
                    export.to_html(to_ghpages=True)
                    print(language.upper(), 'Found new results, exporting...')
                except NoEntriesError:
                    pass


if __name__ == '__main__':
    q_en = 'coyote (bite OR attack OR kill OR chase OR aggressive OR ' \
           'nip) intitle:coyote'
    q_es = 'coyote (mordida OR ataque OR caza OR agresivo OR mordisco) ' \
           'intitle:coyote '
    main(query=q_en)
    main(query=q_es, language='es', country='MX')
