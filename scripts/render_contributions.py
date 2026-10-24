#!/usr/bin/env python3
"""Render the public GitHub contribution calendar; Python standard library only."""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'assets' / 'contributions'

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.labels = {}
        self.target = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and 'data-date' in a and 'data-level' in a:
            self.cells[a['id']] = {'date': a['data-date'], 'level': int(a['data-level'])}
        if tag == 'tool-tip' and a.get('for'):
            self.target = a['for']
            self.parts = []

    def handle_data(self, data):
        if self.target is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.target is not None:
            self.labels[self.target] = ''.join(self.parts).strip()
            self.target = None

def parse_calendar(html, minimum_days=350):
    parser = CalendarParser()
    parser.feed(html)
    days = []
    for key, cell in parser.cells.items():
        label = parser.labels.get(key, '')
        match = re.match(r'([\d,]+) contributions? on ', label)
        if match:
            count = int(match.group(1).replace(',', ''))
        elif label.startswith('No contributions on '):
            count = 0
        else:
            raise ValueError(f'Missing or unsupported contribution label for {cell["date"]}')
        day = date.fromisoformat(cell['date'])
        if not 0 <= cell['level'] <= 4 or (count == 0) != (cell['level'] == 0):
            raise ValueError(f'Inconsistent contribution level on {day}')
        days.append({**cell, 'count': count})
    days.sort(key=lambda d: d['date'])
    if len(days) < minimum_days:
        raise ValueError(f'Incomplete calendar ({len(days)} days); retaining the previous chart')
    dates = [date.fromisoformat(d['date']) for d in days]
    if len(set(dates)) != len(dates) or any(b - a != timedelta(days=1) for a, b in zip(dates, dates[1:])):
        raise ValueError('Calendar dates are duplicated or not consecutive')
    return days

def summary(days):
    counts = [d['count'] for d in days]
    return {'total': sum(counts), 'active_days': sum(c > 0 for c in counts),
            'peak_day': max(counts, default=0), 'from': days[0]['date'], 'to': days[-1]['date']}

def render(days, mode):
    from calendar_design import render_calendar
    return render_calendar(days, mode)


def build(html, output=OUTPUT):
    days=parse_calendar(html)
    result={'username':'Nelpine','source':'https://github.com/users/Nelpine/contributions',
            'summary':summary(days),'days':days}
    # Parse and validate everything before touching existing chart assets.
    files={'orbit-dark.svg':render(days,'dark'),'orbit-light.svg':render(days,'light'),
           'calendar.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n'}
    output.mkdir(parents=True,exist_ok=True)
    for name,body in files.items():
        temp=output/(name+'.tmp')
        temp.write_text(body,encoding='utf-8')
        os.replace(temp,output/name)
    return result['summary']

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-html',type=Path)
    args=parser.parse_args()
    if args.source_html:
        html=args.source_html.read_text(encoding='utf-8')
    else:
        request=Request('https://github.com/users/Nelpine/contributions',
                        headers={'User-Agent':'Nelpine-Profile-Calendar','Accept-Language':'en-US,en;q=0.9'})
        with urlopen(request,timeout=40) as response:
            html=response.read().decode('utf-8')
    print(json.dumps(build(html)))

if __name__=='__main__':
    main()
