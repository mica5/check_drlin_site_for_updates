#!/usr/bin/env python
"""Check Dr. Lin's website for updates.

This code was hacked together. If Dr. Lin adds a new
directory to his site, this won't pick it up.

Version 0.1
2018-09-24
"""
import time
import argparse
import urllib
import os
from dateutil.parser import parse
import datetime
from contextlib import contextmanager

import pandas as pd
import requests
from bs4 import BeautifulSoup


drlin_page_urls = [
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/notes',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project',
]


class File:
    files = list()
    apache_pages = list()
    def __init__(self, url):

        self.url = url
        self.head = requests.head(url)
        self.resp = None
        self.visited = False
        self.bs = None

        try:
            # file (not apache directory)
            self.moddate = parse(self.head.headers['Last-Modified']).replace(tzinfo=None)
            is_apache_directory = False
        except KeyError:
            is_apache_directory = True
            self.moddate = None

        self.is_apache_directory = is_apache_directory
        if is_apache_directory:
            self.children = list()
            self.apache_pages.append(self)

        # file, not apache directory:
        else:

            self.children = None
            self.files.append(self)

        self.filename = urllib.parse.unquote(os.path.basename(url))
        self.get_children()

    def get_children(self):
        if self.resp is not None:
            return
        if self.visited:
            return
        if not self.is_apache_directory:
            return
        self.visited = True
        self.resp = requests.get(self.url)
        self.bs = BeautifulSoup(self.resp.content.decode(), features="html.parser")
        for a in self.bs.findAll('a'):
            url = self.url
            if not url.endswith('/'):
                url += '/'
            full_file_url = urllib.parse.urljoin(url, a.attrs['href'])
            self.children.append(File(full_file_url))
        for c in self.children:
            c.get_children()


@contextmanager
def micatime(name):
    d = dict()
    start = time.time()
    print('beginning "{}" at {}'.format(name, datetime.datetime.now()))
    yield d

    total_seconds = time.time() - start
    d['seconds'] = total_seconds
    print('finished "{}" at {}; took {:.2f} seconds ({:.2f} minutes)'.format(
        name,
        datetime.datetime.now(),
        total_seconds,
        total_seconds / 60,
    ))


def check_site_for_updates():
    roots = list()
    with micatime('downloading Dr. Lin website directory hierarchy'):
        for drlin_page_url in drlin_page_urls:
            roots.append(File(drlin_page_url))

    pd.options.display.max_columns = 0
    pd.options.display.max_colwidth = 0
    pd.options.display.max_rows = -1

    rows = list()
    is_file = False
    modified_time = None
    for ap in roots[0].apache_pages:
        rows.append((is_file, ap.url, modified_time))
    is_file = True
    for f in roots[0].files:
        modified_time = str(f.moddate)
        rows.append((is_file, f.url, modified_time))
    df = pd.DataFrame(
        rows,
        columns='is_file url modified_time'.split(),
    ).sort_values('modified_time', ascending=False)

    df['sorter'] = df.apply(lambda r: (not r.is_file, r.modified_time, r.url), axis=1)
    return df.sort_values('sorter', ascending=False).drop('sorter', axis=1)

@contextmanager
def unlimited_df_colwidth():
    original_max_colwidth = pd.options.display.max_colwidth
    pd.options.display.max_colwidth = -1
    yield
    pd.options.display.max_colwidth = original_max_colwidth


def show_html_updates_table(sites=None):
    from IPython.display import HTML

    if sites is None:
        sites = check_site_for_updates()

    with unlimited_df_colwidth():
        return HTML(sites.to_html(escape=False))


def run_main():
    args = parse_cl_args()

    df = check_site_for_updates()
    with unlimited_df_colwidth():
        printable = df.as_html(escape=False) if args.html else df
        print(printable)

    success = True
    return success


def parse_cl_args():
    argParser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    argParser.add_argument(
        '--html', default=False, action='store_true',
        help="get the response as html instead of a string-formatted pandas DataFrame.\n"
    )

    args = argParser.parse_args()
    return args


__all__ = [
    'File',
    'check_site_for_updates',
    'unlimited_df_colwidth',
    'show_html_updates_table',
]


if __name__ == '__main__':
    success = run_main()
    exit_code = 0 if success else 1
    exit(exit_code)
