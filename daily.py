#!/usr/bin/env python3
# coding: utf-8

import json
from datetime import date

from bs4 import BeautifulSoup

from pygon import Search, ExportData


def main(query: str, language: str = 'en', country: str = 'US') -> None:
    yr, mo = [int(x) for x in str(date.today()).split('-')[:-1]]
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
    cur_data = json.loads(json.dumps(results.raw, ensure_ascii=False))
    if mo <= 9:
        mo = f'0{mo}'
    with open(f'docs/{yr}/{language.upper()}/results_{yr}_{mo}.html') as h:
        html_content = h.read()
    table_content = [[cell.text for cell in row('td')]
                     for row in BeautifulSoup(html_content, 'lxml')('tr')][1:]
    prev_len = len(table_content)
    cur_len = len(cur_data['entries'])
    if prev_len != cur_len:
        export = ExportData(results, **kwargs)
        export.to_html(to_ghpages=True)
        print(language.upper(), 'Found new results, exporting...')


if __name__ == '__main__':
    q_en = 'coyote (bite OR attack OR kill OR chase OR aggressive OR ' \
           'nip) intitle:coyote'
    q_es = 'coyote (mordida OR ataque OR caza OR agresivo OR mordisco) ' \
           'intitle:coyote '
    main(query=q_en)
    main(query=q_es, language='es', country='MX')
