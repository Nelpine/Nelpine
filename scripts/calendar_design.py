"""A personal activity orbit: identity first, recent activity without a scoreboard."""
from datetime import date
from html import escape
import math


def activity_status(days):
    end = date.fromisoformat(days[-1]['date'])
    last = next((date.fromisoformat(d['date']) for d in reversed(days) if d['count']), None)
    if last is None:
        return 'No recent public activity', None, False
    return ('Recently active' if (end-last).days < 30 else 'Last public activity'), last, (end-last).days < 30


def render_calendar(days, mode):
    dark = mode == 'dark'
    p = dict(bg='#090F20', end='#141E38', text='#EDF3FF', muted='#889BBB', line='#293858', cyan='#78F3DD', violet='#ADAAFF', colors=['#293956','#5368A8','#7C88D9','#8BBEEB','#78F3DD']) if dark else dict(bg='#F0F4FC', end='#DEE7F7', text='#243859', muted='#607498', line='#C3CEE3', cyan='#148F85', violet='#706BC7', colors=['#C4CFE3','#A3B6DB','#8494CF','#549DB5','#148F85'])
    start, end = date.fromisoformat(days[0]['date']), date.fromisoformat(days[-1]['date'])
    status, last_active, recently_active = activity_status(days)
    dots, activity, route = [], [], []
    recent = days[-60:]
    last_label = last_active.strftime('%Y.%m.%d') if last_active else 'None in the available period'
    status_color = p['cyan'] if recently_active else p['muted']
    for i, d in enumerate(days):
        t = i/max(len(days)-1,1)
        a, radius = -math.pi/2+t*6*math.pi, 64+t*122
        x,y = 292+radius*math.cos(a), 231+radius*math.sin(a)
        count, level = d['count'], d['level']
        c, r = (p['cyan'] if count else p['colors'][0]), (4.3 if count else 1.45)
        title = escape(f'{d["date"]}: ' + ('Public activity' if count else 'No public activity'))
        halo = f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r*2}" fill="{c}" opacity=".6" filter="url(#glow)"/>' if count else ''
        pulse = f'<circle class="pulse" cx="{x:.2f}" cy="{y:.2f}" r="{r+5}" fill="none" stroke="{c}" opacity=".4"/>' if count else ''
        dots.append(f'<g data-date="{d["date"]}" data-count="{count}"><title>{title}</title>{halo}<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{c}"/>{pulse}</g>')
        if count:
            route.append(f'{x:.2f},{y:.2f}')
    # Binary activity uses the same mark for every active day, regardless of volume.
    for i, d in enumerate(recent):
        x = 567+i*7.8
        c = p['cyan'] if d['count'] else p['line']
        label = escape(d['date'] + (': Public activity' if d['count'] else ': No public activity'))
        activity.append(f'<rect data-activity-date="{d["date"]}" data-active="{str(bool(d["count"])).lower()}" x="{x:.2f}" y="324" width="4.3" height="17" rx="2.15" fill="{c}"><title>{label}</title></rect>')
    rings=''.join(f'<circle cx="292" cy="231" r="{r}" fill="none" stroke="{p["line"]}" stroke-width=".7"/>' for r in (84,130,177,204))
    ticks=[]
    for i in range(60):
        a=i*math.tau/60
        r=215 if i%5==0 else 211
        ticks.append(f'<path d="M{292+208*math.cos(a):.2f} {231+208*math.sin(a):.2f}L{292+r*math.cos(a):.2f} {231+r*math.sin(a):.2f}" stroke="{p["muted"]}" opacity=".4"/>')
    trail=f'<polyline points="{" ".join(route)}" fill="none" stroke="url(#accent)" stroke-width="1.2" opacity=".5"/>' if len(route)>1 else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="450" viewBox="0 0 1100 450" role="img" aria-labelledby="title desc">
<title id="title">Nelpine activity orbit</title>
<desc id="desc">Nelpine. {status}. Latest public activity: {last_label}. Each illuminated orbit point marks a date with public GitHub activity. The small activity strip shows the most recent 60 available days, without comparing contribution counts.</desc>
<defs>
<linearGradient id="bg" x2="1" y2="1"><stop stop-color="{p['bg']}"/><stop offset="1" stop-color="{p['end']}"/></linearGradient>
<linearGradient id="accent"><stop stop-color="{p['violet']}"/><stop offset="1" stop-color="{p['cyan']}"/></linearGradient>
<linearGradient id="metal" x2=".7" y2="1"><stop stop-color="{p['text']}"/><stop offset=".5" stop-color="{p['violet']}"/><stop offset="1" stop-color="{p['cyan']}"/></linearGradient>
<radialGradient id="aura"><stop stop-color="{p['violet']}" stop-opacity=".14"/><stop offset="1" stop-color="{p['violet']}" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
<pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="{p['line']}" stroke-width=".5" opacity=".18"/></pattern>
<clipPath id="clip"><rect x=".5" y=".5" width="1099" height="449" rx="22"/></clipPath>
</defs>
<style>.scan{{transform-origin:292px 231px;animation:orbit 35s linear infinite}}.pulse{{animation:pulse 5s ease-in-out infinite}}.shine{{stroke-dasharray:42 126;animation:trace 8s linear infinite}}@keyframes orbit{{to{{transform:rotate(360deg)}}}}@keyframes pulse{{50%{{opacity:.08;stroke-width:3}}}}@keyframes trace{{to{{stroke-dashoffset:-168}}}}@media(prefers-reduced-motion:reduce){{.scan,.pulse,.shine{{animation:none}}}}</style>
<g clip-path="url(#clip)"><rect width="1100" height="450" fill="url(#bg)"/><rect width="1100" height="450" fill="url(#grid)"/>
<ellipse cx="310" cy="230" rx="310" ry="250" fill="url(#aura)"/>
<g font-family="Consolas,monospace" fill="{p['muted']}" font-size="10" letter-spacing="1.5"><text x="34" y="31">NELPINE / GITHUB</text><text x="1066" y="31" text-anchor="end">ACTIVITY / DAILY REFRESH</text></g>
<g transform="translate(30 16) scale(.89)">{rings}{''.join(ticks)}
<g class="scan" fill="none" stroke="url(#accent)"><circle cx="292" cy="231" r="198" stroke-width="1.8" stroke-dasharray="50 1194"/><circle cx="292" cy="231" r="198" stroke-width="7" stroke-dasharray="1 1243" opacity=".6" filter="url(#glow)"/></g>
{trail}{''.join(dots)}
<circle cx="292" cy="231" r="48" fill="{p['bg']}" stroke="{p['line']}"/>
<path d="M271 252V210L313 252V210" fill="none" stroke="url(#metal)" stroke-width="8" stroke-linejoin="round"/>
<circle class="shine" cx="292" cy="231" r="54" fill="none" stroke="url(#accent)" stroke-width="1"/>
</g><g font-family="Segoe UI,Arial,sans-serif">
<text x="566" y="112" fill="{p['muted']}" font-size="11" letter-spacing="4">DEVELOPER / ACTIVITY</text>
<text x="562" y="180" fill="url(#metal)" font-size="67" font-weight="650" letter-spacing="4">NELPINE</text>
<text x="566" y="211" fill="{p['muted']}" font-size="15">Java Backend · Web Development</text>
<g transform="translate(566 238)">
<rect width="185" height="34" rx="17" fill="{p['bg']}" stroke="{p['line']}"/>
<circle cx="17" cy="17" r="3.5" fill="{status_color}"/>
<text x="30" y="21" fill="{status_color}" font-size="12">{status}</text>
</g>
<g fill="{p['muted']}" font-size="10" font-family="Consolas,monospace" letter-spacing="1.2"><text x="566" y="308">RECENT ACTIVITY</text><text x="1038" y="308" text-anchor="end">LAST {len(recent)} DAYS</text></g>
{''.join(activity)}
<text x="566" y="369" fill="{p['muted']}" font-size="11">Latest public activity · {last_label}</text>
<path d="M566 394H1038" stroke="{p['line']}"/>
<text x="566" y="419" fill="{p['muted']}" font-size="10" font-family="Consolas,monospace" letter-spacing=".7">JAVA / SPRING / VUE / TYPESCRIPT</text>
</g></g><rect x=".5" y=".5" width="1099" height="449" rx="22" fill="none" stroke="{p['line']}"/></svg>'''
