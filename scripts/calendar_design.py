"""A data-driven contribution orbit and daily reference matrix."""
from datetime import date, timedelta
from html import escape
import math


def render_calendar(days, mode):
    dark = mode == 'dark'
    p = dict(bg='#090F20', end='#141E38', text='#EDF3FF', muted='#889BBB', line='#293858', cyan='#78F3DD', violet='#ADAAFF', colors=['#293956','#5368A8','#7C88D9','#8BBEEB','#78F3DD']) if dark else dict(bg='#F0F4FC', end='#DEE7F7', text='#243859', muted='#607498', line='#C3CEE3', cyan='#148F85', violet='#706BC7', colors=['#C4CFE3','#A3B6DB','#8494CF','#549DB5','#148F85'])
    start, end = date.fromisoformat(days[0]['date']), date.fromisoformat(days[-1]['date'])
    total, active, peak = sum(d['count'] for d in days), sum(d['count']>0 for d in days), max(d['count'] for d in days)
    dots, matrix, route, months = [], [], [], []
    monday = start-timedelta(days=start.weekday())
    step = min(18, 974/((end-monday).days//7+1))
    last_month = None
    for i, d in enumerate(days):
        t = i/max(len(days)-1,1)
        a, radius = -math.pi/2+t*6*math.pi, 64+t*122
        x,y = 292+radius*math.cos(a), 231+radius*math.sin(a)
        count, level = d['count'], d['level']
        c, r = p['colors'][level], 1.45 if not count else 3+level*.7
        title = escape(f'{d["date"]}: {count} contributions')
        halo = f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r*2}" fill="{c}" opacity=".6" filter="url(#glow)"/>' if count else ''
        pulse = f'<circle class="pulse" cx="{x:.2f}" cy="{y:.2f}" r="{r+5}" fill="none" stroke="{c}" opacity=".4"/>' if level>=3 else ''
        dots.append(f'<g data-date="{d["date"]}" data-count="{count}"><title>{title}</title>{halo}<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{c}"/>{pulse}</g>')
        if count:
            route.append(f'{x:.2f},{y:.2f}')
        day = date.fromisoformat(d['date'])
        col,row = divmod((day-monday).days,7)
        mx,my = 68+col*step,458+row*9
        matrix.append(f'<rect x="{mx:.2f}" y="{my}" width="{step-5:.2f}" height="5" rx="2.5" fill="{c}"><title>{title}</title></rect>')
        if (day.year,day.month)!=last_month:
            months.append(f'<text x="{mx:.2f}" y="449">{day.strftime("%b")}</text>')
            last_month=(day.year,day.month)
    rings=''.join(f'<circle cx="292" cy="231" r="{r}" fill="none" stroke="{p["line"]}" stroke-width=".7"/>' for r in (84,130,177,204))
    ticks=[]
    for i in range(60):
        a=i*math.tau/60
        r=215 if i%5==0 else 211
        ticks.append(f'<path d="M{292+208*math.cos(a):.2f} {231+208*math.sin(a):.2f}L{292+r*math.cos(a):.2f} {231+r*math.sin(a):.2f}" stroke="{p["muted"]}" opacity=".4"/>')
    trail=f'<polyline points="{" ".join(route)}" fill="none" stroke="url(#accent)" stroke-width="1.2" opacity=".5"/>' if len(route)>1 else ''
    legend=''.join(f'<circle cx="{944+i*18}" cy="539" r="3" fill="{c}"/>' for i,c in enumerate(p['colors']))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="565" viewBox="0 0 1100 565" role="img" aria-labelledby="title desc">
<title id="title">Nelpine contribution orbit</title>
<desc id="desc">{total} public contributions on {active} active days from {start} to {end}. One orbit dot and matrix cell per date. Brighter colors mean more contributions. Lines connect active dates chronologically.</desc>
<defs>
<linearGradient id="bg" x2="1" y2="1"><stop stop-color="{p['bg']}"/><stop offset="1" stop-color="{p['end']}"/></linearGradient>
<linearGradient id="accent"><stop stop-color="{p['violet']}"/><stop offset="1" stop-color="{p['cyan']}"/></linearGradient>
<linearGradient id="metal" x2=".7" y2="1"><stop stop-color="{p['text']}"/><stop offset=".5" stop-color="{p['violet']}"/><stop offset="1" stop-color="{p['cyan']}"/></linearGradient>
<radialGradient id="aura"><stop stop-color="{p['violet']}" stop-opacity=".14"/><stop offset="1" stop-color="{p['violet']}" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
<pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="{p['line']}" stroke-width=".5" opacity=".18"/></pattern>
<clipPath id="clip"><rect x=".5" y=".5" width="1099" height="564" rx="22"/></clipPath>
</defs>
<style>.scan{{transform-origin:292px 231px;animation:orbit 35s linear infinite}}.pulse{{animation:pulse 5s ease-in-out infinite}}.shine{{stroke-dasharray:42 126;animation:trace 8s linear infinite}}@keyframes orbit{{to{{transform:rotate(360deg)}}}}@keyframes pulse{{50%{{opacity:.08;stroke-width:3}}}}@keyframes trace{{to{{stroke-dashoffset:-168}}}}@media(prefers-reduced-motion:reduce){{.scan,.pulse,.shine{{animation:none}}}}</style>
<g clip-path="url(#clip)"><rect width="1100" height="565" fill="url(#bg)"/><rect width="1100" height="565" fill="url(#grid)"/>
<ellipse cx="310" cy="230" rx="310" ry="250" fill="url(#aura)"/>
<g font-family="Consolas,monospace" fill="{p['muted']}" font-size="10" letter-spacing="1.5"><text x="34" y="31">NELPINE / GITHUB</text><text x="1066" y="31" text-anchor="end">PUBLIC ACTIVITY · AUTO SYNC</text></g>
<g transform="translate(30 16) scale(.89)">{rings}{''.join(ticks)}
<g class="scan" fill="none" stroke="url(#accent)"><circle cx="292" cy="231" r="198" stroke-width="1.8" stroke-dasharray="50 1194"/><circle cx="292" cy="231" r="198" stroke-width="7" stroke-dasharray="1 1243" opacity=".6" filter="url(#glow)"/></g>
{trail}{''.join(dots)}
<circle cx="292" cy="231" r="48" fill="{p['bg']}" stroke="{p['line']}"/>
<path d="M271 252V210L313 252V210" fill="none" stroke="url(#metal)" stroke-width="8" stroke-linejoin="round"/>
<circle class="shine" cx="292" cy="231" r="54" fill="none" stroke="url(#accent)" stroke-width="1"/>
</g><g font-family="Segoe UI,Arial,sans-serif">
<text x="566" y="112" fill="{p['cyan']}" font-size="11" letter-spacing="4">CONTRIBUTION ORBIT</text>
<text x="562" y="180" fill="url(#metal)" font-size="67" font-weight="650" letter-spacing="4">NELPINE</text>
<path d="M566 202H1038" stroke="{p['line']}"/>
<g fill="{p['text']}" font-size="44" font-family="Consolas,monospace"><text x="566" y="266">{total:02d}</text><text x="750" y="266">{active:02d}</text><text x="938" y="266">{peak:02d}</text></g>
<g fill="{p['muted']}" font-size="12"><text x="568" y="291">Contributions</text><text x="752" y="291">Active days</text><text x="940" y="291">Peak / day</text></g>
<path d="M566 319H1038" stroke="{p['line']}"/>
<text x="566" y="349" fill="{p['muted']}" font-size="12">One dot per day. Active days form the trail.</text>
<text x="566" y="376" fill="{p['muted']}" font-size="11" font-family="Consolas,monospace">{start.strftime('%Y.%m.%d')} — {end.strftime('%Y.%m.%d')}</text>
<path d="M34 418H1066" stroke="{p['line']}"/>
<g fill="{p['muted']}" font-family="Consolas,monospace" font-size="9">{''.join(months)}<text x="34" y="464">MON</text><text x="34" y="491">THU</text><text x="34" y="518">SUN</text></g>
{''.join(matrix)}
<g fill="{p['muted']}" font-family="Consolas,monospace" font-size="9" letter-spacing=".5"><text x="35" y="542">DAILY CONTRIBUTIONS / WEEKLY MATRIX</text><text x="901" y="542">LESS</text>{legend}<text x="1040" y="542">MORE</text></g>
</g></g><rect x=".5" y=".5" width="1099" height="564" rx="22" fill="none" stroke="{p['line']}"/></svg>'''
