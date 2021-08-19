#!/usr/bin/env python3
# coding: utf-8

from datetime import date

from main import Search, ExportData


def main(query, lang='en', country='US'):
    yr, mo = str(date.today()).split('-')[:-1]
    kwargs = {
        'query': query,
        'month': int(mo),
        'year': int(yr),
        'lang': 'en',
        'country': 'US',
        'testing': False
    }
    search = Search(**kwargs)
    results = search.run()
    export = ExportData(results, **kwargs)
    export.to_html(to_ghpages=True)


if __name__ == '__main__':
    main('coyote (bite OR attack OR kill OR chase OR aggressive OR nip) intitle:coyote')
