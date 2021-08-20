import os

import bottle

from main import Search, ExportData

app = bottle.Bottle()


@bottle.get('/search')
def search_func():
    return '''
        <form action="/search" method="post">
            Query: <input name="query" type="text" />
            Month: <input name="month" type="number" />
            Year: <input name="year" type="number" />
            <input value="Search" type="submit" />
        </form>
    '''


@bottle.post('/search')
def do_search():
    query = bottle.request.forms.get('query')
    month = int(bottle.request.forms.get('month'))
    year = int(bottle.request.forms.get('year'))
    kwargs = {
        'query': query,
        'month': month,
        'year': year,
        'lang': 'es',
        'country': 'US',
        'testing': False,
        'silent': True
    }
    search = Search(**kwargs)
    results = search.run()
    export = ExportData(results, **kwargs)
    lines = export.to_html()
    lines = ''.join(lines)
    return lines


if os.environ.get('APP_LOCATION') == 'heroku':
    bottle.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    bottle.run(host='localhost', port=8080, debug=True)
