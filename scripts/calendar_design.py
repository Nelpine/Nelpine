"""A readable three-month contribution calendar, rendered as a self-contained SVG."""
import calendar
from datetime import date
from html import escape


def recent_months(end):
    index = end.year * 12 + end.month - 1
    return [divmod(index - offset, 12) for offset in (2, 1, 0)]


def render_calendar(days, mode):
    end = date.fromisoformat(days[-1]['date'])
    months = [(year, month + 1) for year, month in recent_months(end)]
    beginning = date(months[0][0], months[0][1], 1)
    recent = [d for d in days if beginning.isoformat() <= d['date'] <= end.isoformat()]
    total = sum(d['count'] for d in recent)
    active = sum(d['count'] > 0 for d in recent)
    data = {d['date']: d for d in days}
    dark = mode == 'dark'
    p = dict(bg='#101722', card='#151F2D', border='#29364A', text='#E8EFF9',
             muted='#899AB2', date='#62758F', zero='#1E2A3B', grid='#263549',
             colors=['#1E2A3B', '#315C97', '#3C7FC0', '#43B4CD', '#88E2DB'],
             active='#F3FCFF', today='#B9CDE8') if dark else dict(
             bg='#F4F7FB', card='#FFFFFF', border='#DCE4EE', text='#24354B',
             muted='#718297', date='#8E9BAB', zero='#EDF1F7', grid='#E4EAF2',
             colors=['#EDF1F7', '#BAD1EC', '#82B4DE', '#479ABA', '#247E92'],
             active='#153750', today='#3C6D9F')
    panels = []
    weekdays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    cal = calendar.Calendar(firstweekday=0)
    for panel, (year, month) in enumerate(months):
        left = 31 + panel * 350
        month_total = sum(d['count'] for d in recent if d['date'].startswith(f'{year}-{month:02d}'))
        panels.append(f'<rect x="{left}" y="92" width="338" height="299" rx="16" fill="{p["card"]}" stroke="{p["border"]}"/>')
        panels.append(f'<text x="{left+22}" y="127" font-size="19" font-weight="600" fill="{p["text"]}">{calendar.month_name[month]}</text>')
        panels.append(f'<text x="{left+315}" y="126" text-anchor="end" font-size="12" fill="{p["muted"]}">{month_total} contributions</text>')
        for col, label in enumerate(weekdays):
            panels.append(f'<text x="{left+37+col*44}" y="157" text-anchor="middle" font-size="10" fill="{p["muted"]}">{label}</text>')
        for row, week in enumerate(cal.monthdatescalendar(year, month)):
            for col, day in enumerate(week):
                if day.month != month:
                    continue
                x, y = left + 19 + col*44, 172 + row*33
                d = data.get(day.isoformat())
                future = day > end
                available = d is not None and not future
                level = d['level'] if available else 0
                count = d['count'] if available else None
                color = p['colors'][level]
                is_today = day == end
                title = escape(f'{day.isoformat()}: {count} contributions' if available else
                               f'{day.isoformat()}: future date' if future else
                               f'{day.isoformat()}: outside available data')
                if not available:
                    rect = f'<rect x="{x}" y="{y}" width="36" height="25" rx="6" fill="none" stroke="{p["grid"]}" stroke-dasharray="2 3"/>'
                else:
                    rect = f'<rect x="{x}" y="{y}" width="36" height="25" rx="6" fill="{color}"/>'
                    if level >= 3:
                        rect += f'<rect class="halo" x="{x+2}" y="{y+2}" width="32" height="21" rx="5" fill="{color}" filter="url(#glow)" style="animation-delay:{-(day.day%7)}s"/>'
                    if is_today:
                        rect += f'<rect x="{x-2}" y="{y-2}" width="40" height="29" rx="8" fill="none" stroke="{p["today"]}" stroke-width="1"/>'
                text_color = p['active'] if level > 0 else p['date']
                opacity = '.4' if future else '1'
                panels.append(f'<g opacity="{opacity}"><title>{title}</title>{rect}<text x="{x+18}" y="{y+17}" text-anchor="middle" fill="{text_color}" font-size="11" font-weight="{600 if level else 400}">{day.day}</text></g>')
    legend = ''.join(f'<rect x="{873+i*21}" y="423" width="15" height="12" rx="3" fill="{c}"/>' for i,c in enumerate(p['colors']))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="465" viewBox="0 0 1100 465" role="img" aria-labelledby="title desc">
<title id="title">Nelpine GitHub contribution calendar</title>
<desc id="desc">{total} public contributions on {active} active days from {beginning} to {end}. Three month detail view. Color indicates daily intensity; future dates are outlined.</desc>
<defs><filter id="glow" x="-40%" y="-60%" width="180%" height="220%"><feGaussianBlur stdDeviation="3"/></filter></defs>
<style>.halo{{opacity:.2;animation:breathe 7s ease-in-out infinite}}@keyframes breathe{{50%{{opacity:.5}}}}@media(prefers-reduced-motion:reduce){{.halo{{animation:none;opacity:.18}}}}</style>
<rect x=".5" y=".5" width="1099" height="464" rx="20" fill="{p['bg']}" stroke="{p['border']}"/>
<g font-family="Segoe UI,Arial,sans-serif">
<g transform="translate(32 30)" fill="none" stroke="{p['muted']}" stroke-width="1.5"><rect x="0" y="3" width="20" height="18" rx="4"/><path d="M5 0V6M15 0V6M0 9H20"/></g>
<text x="65" y="47" fill="{p['text']}" font-size="20" font-weight="600">GitHub activity</text>
<text x="33" y="72" fill="{p['muted']}" font-size="11">{beginning.strftime('%Y.%m')} — {end.strftime('%Y.%m.%d')} / PUBLIC CONTRIBUTIONS</text>
<text x="1066" y="47" text-anchor="end" fill="{p['text']}" font-size="14"><tspan font-weight="600">{total}</tspan> contributions <tspan fill="{p['muted']}"> / </tspan><tspan font-weight="600">{active}</tspan> active days</text>
<text x="1066" y="71" text-anchor="end" fill="{p['muted']}" font-size="11">Recent 3 months · Updated daily</text>
{''.join(panels)}
<text x="33" y="433" fill="{p['muted']}" font-size="11">Nelpine <tspan fill="{p['border']}"> / </tspan> One square per day</text>
<text x="839" y="433" fill="{p['muted']}" font-size="10">Less</text>{legend}<text x="990" y="433" fill="{p['muted']}" font-size="10">More</text>
</g></svg>'''
