#!/usr/bin/env python3
"""Render the public GitHub contribution calendar; Python standard library only."""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import sys
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
    s = summary(days)
    dark = mode == 'dark'
    p = dict(bg='#101B29', line='#2B3E53', ink='#EAF2FC', sub='#91A9C2',
             zero='#223044', floor='#0C1521', colors=['#223044','#245B85','#357EAD','#47AAC4','#77E9DD']) if dark else dict(
             bg='#F4F7FC', line='#D4DFED', ink='#1D344E', sub='#617D98',
             zero='#D9E3F0', floor='#E6EDF6', colors=['#D9E3F0','#A6CADF','#73B5CF','#3999B8','#197C99'])
    start = date.fromisoformat(days[0]['date'])
    origin = start - timedelta(days=(start.weekday()+1) % 7)
    weeks = ((date.fromisoformat(days[-1]['date']) - origin).days // 7) + 1
    dx = 17.5
    origin_x, origin_y = 49, 248
    cells = []
    for d in days:
        day = date.fromisoformat(d['date'])
        delta = (day-origin).days
        week, weekday = divmod(delta, 7)
        x = origin_x + week*dx + weekday*7
        y = origin_y + weekday*8.2
        height = 2 if not d['count'] else 5 + min(107, math.log2(d['count']+1)*19)
        fill = p['colors'][d['level']]
        top = f'{x:.2f},{y-height:.2f} {x+12:.2f},{y-height-4:.2f} {x+18:.2f},{y-height+1:.2f} {x+6:.2f},{y-height+5:.2f}'
        front = f'{x+6:.2f},{y-height+5:.2f} {x+18:.2f},{y-height+1:.2f} {x+18:.2f},{y+1:.2f} {x+6:.2f},{y+5:.2f}'
        side = f'{x:.2f},{y-height:.2f} {x+6:.2f},{y-height+5:.2f} {x+6:.2f},{y+5:.2f} {x:.2f},{y:.2f}'
        tooltip = escape(f'{d["date"]}: {d["count"]} contributions')
        if d['count'] == 0:
            cells.append(f'<path class="zero" d="M{x:.1f} {y:.1f}l12 -4 6 5 -12 4Z"><title>{tooltip}</title></path>')
            continue
        glow = ''
        if d['level'] >= 3:
            delay = -((week*7+weekday) % 13)*.7
            glow = f'<polygon class="peak" points="{top}" fill="{fill}" filter="url(#glow)" style="animation-delay:{delay:.1f}s" opacity=".45"/>'
        cells.append(f'<g><title>{tooltip}</title><polygon points="{side}" fill="{fill}" opacity=".44"/><polygon points="{front}" fill="{fill}" opacity=".72"/><polygon points="{top}" fill="{fill}" stroke="{p["bg"]}" stroke-width=".55"/>{glow}</g>')
    month_labels=[]
    # Suppress the first partial month so adjacent short labels do not overlap.
    previous=start.month if start.day != 1 else None
    for d in days:
        day=date.fromisoformat(d['date'])
        if day.month != previous:
            previous=day.month
            col=(day-origin).days//7
            if col <= weeks-3:
                month_labels.append(f'<text x="{origin_x+col*dx+20:.1f}" y="336">{day.strftime("%b")}</text>')
    stats=''
    for x,value,label in [(49,s['total'],'CONTRIBUTIONS'),(282,s['active_days'],'ACTIVE DAYS'),(515,s['peak_day'],'PEAK / DAY')]:
        stats += f'<text x="{x}" y="119" font-size="31" font-weight="600" fill="{p["ink"]}">{value:,}</text><text x="{x}" y="141" fill="{p["sub"]}" font-family="Consolas,monospace" font-size="10" letter-spacing="1.5">{label}</text>'
    legend=''.join(f'<rect x="{916+i*16}" y="361" width="10" height="10" rx="2" fill="{color}"/>' for i,color in enumerate(p['colors']))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="406" viewBox="0 0 1100 406" role="img" aria-labelledby="title desc">
<title id="title">Nelpine GitHub contribution skyline</title><desc id="desc">{s['total']} contributions across {s['active_days']} active days, from {s['from']} to {s['to']}. Heights use a logarithmic scale; cell tooltips show exact daily counts. Only public profile data is used.</desc>
<defs><filter id="glow" x="-80%" y="-150%" width="260%" height="400%"><feGaussianBlur stdDeviation="2.2"/></filter><linearGradient id="scan" gradientUnits="userSpaceOnUse" x1="0" x2="1100"><stop stop-color="#77E9DD" stop-opacity="0"/><stop offset=".5" stop-color="#77E9DD" stop-opacity=".8"/><stop offset="1" stop-color="#77E9DD" stop-opacity="0"/></linearGradient><clipPath id="frame"><rect x="1" y="1" width="1098" height="404" rx="18"/></clipPath></defs>
<style>.zero{{fill:{p['zero']};stroke:{p['bg']};stroke-width:.55}}.peak{{animation:pulse 7s ease-in-out infinite}}.scan{{animation:scan 11s linear infinite;stroke-dasharray:70 1300}}@keyframes pulse{{0%,100%{{opacity:.18}}50%{{opacity:.65}}}}@keyframes scan{{to{{stroke-dashoffset:-1370}}}}@media(prefers-reduced-motion:reduce){{.peak,.scan{{animation:none}}}}</style>
<g clip-path="url(#frame)"><rect width="1100" height="406" fill="{p['bg']}"/>
<g font-family="Segoe UI,Arial,sans-serif"><path d="M48 42H53V54H48Z M57 35H62V54H57Z M66 29H71V54H66Z" fill="#79B6D7"/><text x="86" y="48" fill="{p['ink']}" font-size="19" font-weight="600">Contribution skyline</text><text x="1051" y="47" text-anchor="end" fill="{p['sub']}" font-size="11">{s['from']} — {s['to']}</text>
{stats}
<text x="1051" y="113" text-anchor="end" fill="{p['sub']}" font-family="Consolas,monospace" font-size="11" letter-spacing="1">NELPINE / GITHUB</text>
<text x="1051" y="137" text-anchor="end" fill="{p['sub']}" font-size="11">Daily refresh · Public profile data</text>
<path d="M37 247L1007 247L1065 305L94 305Z" fill="{p['floor']}" stroke="{p['line']}"/>
{''.join(cells)}
<g font-family="Consolas,monospace" font-size="11" fill="{p['sub']}">{''.join(month_labels)}</g>
<path d="M49 353H1051" stroke="{p['line']}" stroke-width=".7"/><path class="scan" d="M49 353H1051" stroke="url(#scan)" stroke-width="1"/>
<text x="49" y="375" font-size="11" fill="{p['sub']}">One column per day · Height: log scale · Exact counts in SVG tooltips</text>
<text x="882" y="370" fill="{p['sub']}" font-size="10">Less</text>{legend}<text x="1007" y="370" fill="{p['sub']}" font-size="10">More</text>
</g><rect x="1" y="1" width="1098" height="404" rx="18" fill="none" stroke="{p['line']}"/></g></svg>'''

def build(html, output=OUTPUT):
    days=parse_calendar(html)
    result={'username':'Nelpine','source':'https://github.com/users/Nelpine/contributions',
            'summary':summary(days),'days':days}
    # Parse and validate everything before touching existing chart assets.
    files={'skyline-dark.svg':render(days,'dark'),'skyline-light.svg':render(days,'light'),
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
