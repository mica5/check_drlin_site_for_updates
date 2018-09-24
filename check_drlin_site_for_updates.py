#!/usr/bin/env python
"""Check Dr. Lin's website for updates.

This code was hacked together. If Dr. Lin adds a new
directory to his site, this won't pick it up.

Version 0.1
2018-09-24
"""
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
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/notes/',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project/',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project/temp_data/',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project/Homework/',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project/DB1/',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project/DB2/',
    'http://xanadu.cs.sjsu.edu/~drtylin/classes/cs157A/Project/DB3/',
]


class File:
    def __init__(self, url):

        head = requests.head(url)
        self.head = head

        try:
            self.moddate = parse(head.headers['Last-Modified']).replace(tzinfo=None)
        except KeyError:
            self.moddate = None

        self.url = url
        self.filename = urllib.parse.unquote(os.path.basename(url))


def check_site_for_updates():
    all_site_files = list()
    for drlin_page_url in drlin_page_urls:

        # get a main page directory listing
        resp = requests.get(drlin_page_url)

        # parse out the page
        bs = BeautifulSoup(resp.content.decode(), features="html.parser")

        # grab the urls and updated dates of the files listed on the page
        for a in bs.findAll('a'):
            full_file_url = urllib.parse.urljoin(drlin_page_url, a.attrs['href'])
            all_site_files.append(File(full_file_url))

    now = datetime.datetime.now()
    min_moddate = now
    for f in all_site_files:
        if not f.moddate:
            continue
        if f.moddate < min_moddate:
            min_moddate = f.moddate

    files = [
        (f.moddate, f.filename, f.url)
        for f in sorted(
            all_site_files,
            key=lambda f: (f.moddate if f.moddate else min_moddate),
            reverse=True,
        )
    ]
    df = pd.DataFrame(
        files,
        columns='moddate filename url'.split(),
    ).set_index('moddate')

    df['mod_ago'] = now - df.index

    return df


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
