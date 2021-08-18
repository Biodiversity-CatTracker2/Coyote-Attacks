#!/usr/bin/env python3
# coding: utf-8

import calendar
import concurrent.futures
import json
import os
import shutil
import sys
import tempfile
import time
import warnings
from collections import defaultdict, namedtuple
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import NamedTuple

import dill
import grip
import newspaper
import pandas as pd
from pygooglenews import GoogleNews
from rich.console import Console


class NoEntriesError(Exception):
    pass


class Search:
    def __init__(self,
                 query: str,
                 month: int,
                 year: int,
                 lang: str,
                 country: str) -> None:
        self.query = query
        self.month = month
        self.year = year
        self.lang = lang
        self.country = country
        self.testing = False

    def create_date(self) -> str:
        if self.month <= 9:
            self.month = f'0{self.month}'
        if int(self.month) in [1, 3, 5, 7, 8, 10, 12]:
            last_day = 31
        elif int(self.month) == 2:
            if calendar.isleap(self.year):
                last_day = 29
            else:
                last_day = 28
        else:
            last_day = 30
        return last_day

    def request(self) -> dict:
        console = Console()
        gn = GoogleNews(lang=self.lang, country=self.country)

        last_day = Search.create_date(self)
        from_ = f'{self.year}-{self.month}-01'
        to_ = f'{self.year}-{self.month}-{last_day}'

        month_name = calendar.month_name[int(self.month)]
        console.rule(f'{month_name}, {self.year}')

        res = gn.search(self.query, from_=from_, to_=to_)
        count = len(res['entries'])
        if count == 100:
            console.print(f'Found +{count} entries')
        else:
            console.print(f'Found {count} entries')
        if count >= 100:
            res['entries'].clear()
            for day in range(1, last_day):
                if day <= 9:
                    if day != 9:
                        next_day = f'0{day + 1}'
                    day = f'0{day}'
                else:
                    next_day = day + 1
                res_1 = gn.search(self.query,
                                  from_=f'{self.year}-{self.month}-{day}',
                                  to_=f'{self.year}-{self.month}-{next_day}')
                res['entries'].extend(res_1['entries'])
        return res

    def improve_results(self, raw_data: dict) -> dict:
        def iterate_over_articles(article):
            exclude_keys = [
                'title_detail', 'links', 'summary_detail', 'guidislink',
                'sub_articles', 'published_parsed', 'summary'
            ]
            article = {
                k: v
                for k, v in article.items() if k not in exclude_keys
            }

            article_obj = newspaper.Article(article['link'], language=self.lang)
            try:
                article_obj.download()
                article_obj.parse()
                article_obj.nlp()
                article['keywords'] = article_obj.keywords
                article['summary'] = article_obj.summary
            except newspaper.article.ArticleException:
                print(f'Skipped nlp for {article["title"]}...')
                article['keywords'] = []
                article['summary'] = ''
            return article

        output_dict = defaultdict(dict)
        output_dict['feed'] = raw_data['feed']
        output_dict['results']['entries'] = entries = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = [
                executor.submit(iterate_over_articles, article)
                for article in raw_data['entries']
            ]
            for future in concurrent.futures.as_completed(results):
                entries.append(future.result())
        return output_dict

    def filename(self) -> str:
        Search.create_date(self)
        if self.testing:
            fname = f'{self.query}__results_{self.year}_{self.month}'
        else:
            fname = f'results_{self.year}_{self.month}'
        return fname

    def mkdir_ifnot(self, subdir: str) -> str:
        if self.lang.lower() == 'en':
            path = f'data/{self.year}/{subdir}/EN'
        elif self.lang.lower() == 'es':
            path = f'data/{self.year}/{subdir}/ES'
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def run(self) -> NamedTuple:
        Data = namedtuple('Data', ['raw', 'improved'])
        Data.raw = Search.request(self)
        Data.improved = Search.improve_results(self, Data.raw)
        return Data


class ExportData(Search):
    def __init__(self, data: NamedTuple, query: str, month: int,
                 year: int, lang: str, country: str) -> None:
        super().__init__(query, month, year, lang, country)
        self.data = data
        self.fname = Search.filename(self)
        if not self.data.raw['entries']:
            raise NoEntriesError('Cannot export because no entries were found.')

    def to_pandas(self) -> pd.DataFrame:
        df = pd.DataFrame.from_dict(self.data.improved['results']['entries'])
        df.columns = df.columns.str.capitalize()
        df['Published'] = pd.to_datetime(df.Published).dt.date
        df.sort_values('Published', inplace=True)
        df.replace(r'\\n', ' ', regex=True, inplace=True)
        df.reset_index(inplace=True)
        df.pop('index')
        return df

    def to_excel(self) -> None:
        path = Search.mkdir_ifnot(self, 'excel')
        df = ExportData.to_pandas(self)
        df.to_excel(f'{path}/{self.fname}.xlsx',
                    encoding='utf-8-sig')

    def to_json(self) -> None:
        path_raw = Search.mkdir_ifnot(self, 'json/raw')
        path = Search.mkdir_ifnot(self, 'json')
        with open(f'{path_raw}/raw/raw_{self.fname}.json',
                  'w') as j:
            json.dump(self.data.raw, j, indent=4)

        with open(f'{path}/{self.fname}.json', 'w') as j:
            json.dump(self.data.improved, j, indent=4, ensure_ascii=False)

    def to_pickle(self) -> None:
        path = Search.mkdir_ifnot(self, 'pickle')
        D = self.data(self.data.raw, self.data.improved)
        with open(f'{path}/{self.fname}.pkl', 'wb') as pkl:
            dill.dump(D, pkl)

    def to_html(self, keep_md=False) -> str:
        def remove_bad_chrs(x: str) -> str:
            return x.replace('|', ' ').replace('\n', ' ').replace('  ', ' ')

        def md_link(link: str) -> str:
            return f'[Link]({link})'

        def source(d: dict) -> str:
            stitle = ''.join(
                [' ' if x in list('()[]|') else x for x in d['title']])
            slink = d["href"]
            return f'[{stitle}]({slink})'

        df = ExportData.to_pandas(self)
        df['Summary'] = df.Summary.apply(remove_bad_chrs)
        df['Title'] = df.Title.apply(remove_bad_chrs)
        df['Link'] = df.Link.apply(md_link)
        df['Source'] = df.Source.apply(source)
        df.pop('Id')
        md = df.to_markdown()
        path = Search.mkdir_ifnot(self, 'html')
        html_path = f'{path}/{self.fname}.html'
        new_name = f'{self.month}_{self.year} - {self.query}'
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(md.encode('utf-8'))
            fp.seek(0)
            fp.read().decode('utf-8')
            if keep_md:
                path_md = Search.mkdir_ifnot(self, 'md')
                os.link(fp.name, f'{path_md}/{self.fname}.md')
            warnings.simplefilter("ignore", ResourceWarning)
            grip.export(path=fp.name,
                        out_filename=html_path,
                        title=new_name,
                        quiet=True)
        stdout = sys.stdout
        with open(os.devnull, 'w') as f:
            sys.stdout = f
            grip.clear_cache()
        sys.stdout = stdout
        with open(html_path, 'r+') as f:
            lines = f.readlines()
        return lines


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    if sys.argv[1:]:
        query = ' '.join(
            [_item for _item in sys.argv[1:] if type(_item) is str])
        for _item in sys.argv[1:]:
            try:
                if int(_item) <= 12:
                    month = int(_item)
                elif int(_item) > 12:
                    year = int(_item)
            except (TypeError, ValueError):
                continue
    else:
        query = 'coyote (mordida OR ataque OR caza OR agresivo OR mordisco) intitle:coyote'
        # month = 1
        year = 2021
        lang = 'es'
        country = 'MX'
        for month in range(1, 9):
            args = query, month, year, lang, country
            search = Search(*args)
            search.testing = False
            results = search.run()
            try:
                export = ExportData(results, *args)
                export.to_html()
            except NoEntriesError:
                continue
