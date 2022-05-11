#!/usr/bin/env python3
# coding: utf-8

import json

import bullet
from rich.console import Console

from google_news_api import Search, ExportData, Count


class Check(bullet.Check):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_choices = 1

    @bullet.keyhandler.register(bullet.charDef.NEWLINE_KEY)  # noqa
    def accept(self):
        if self.valid():
            return super().accept()

    def valid(self):
        return self.min_choices <= sum(1 for x in self.checked if x)


def any2(string, lst):
    return any(string in x for x in lst)


def main():
    cli = bullet.VerticalPrompt([
        bullet.Input('Query: '),
        bullet.Numbers('Month (integer): ', type=int),
        bullet.Numbers('Year (integer): ', type=int),
        bullet.Input('Language (two-letter code): '),
        bullet.Input('Country (two-letter code): '),
    ],
                                spacing=1)
    result = cli.launch()
    keys = [
        x.replace(': ', '').split(' ')[0].lower()
        for x in list(zip(*result))[0]
    ]
    values = list(zip(*result))[1]
    kwargs = {k: v for k, v in zip(keys, values)}
    kwargs.update({'testing': False, 'silent': True})
    search = Search(**kwargs)
    results = search.run()
    if Count.count == 0:
        return
    cli_1 = Check(prompt='- Check/Un-check an item by pressing space.',
                  choices=['Print', 'Export'],
                  check='✅ ')
    response_1 = cli_1.launch()
    if 'Print' in response_1:
        Console().print(json.dumps(results.improved, indent=4))  # noqa
    if 'Export' in response_1:
        export = ExportData(results, **kwargs)
        options = [
            'to HTML (.html)', 'to Pickle (.pkl)', 'to Excel ('
            '.xlsx)', 'to JSON (.json)'
        ]
        cli_2 = Check(choices=options, check='  ✅ ')
        selected_options = cli_2.launch()
        if any2('HTML', selected_options):
            export.to_html()
        if any2('Pickle', selected_options):
            export.to_pickle()
        if any2('Excel', selected_options):
            export.to_excel()
        if any2('JSON', selected_options):
            export.to_json()


if __name__ == '__main__':
    main()
