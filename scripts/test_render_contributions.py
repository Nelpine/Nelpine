import unittest
import xml.etree.ElementTree as ET
from render_contributions import parse_calendar, render, summary

def fixture(items):
    return ''.join(f'<td data-date="{d}" data-level="{level}" id="d{i}"></td><tool-tip for="d{i}">{label}</tool-tip>'
                   for i,(d,level,label) in enumerate(items))

class CalendarTests(unittest.TestCase):
    def test_orbit_retains_every_date_and_count_across_year_boundary(self):
        from datetime import date, timedelta
        start, end = date(2025, 10, 31), date(2026, 1, 2)
        days = []
        while start <= end:
            count = 100 if start.month == 10 else 1 if start == end else 0
            days.append({'date': start.isoformat(), 'count': count, 'level': 1 if count else 0})
            start += timedelta(days=1)
        svg = render(days, 'dark')
        root = ET.fromstring(svg)
        dots = [e for e in root.iter() if 'data-date' in e.attrib]
        self.assertEqual([(e.attrib['data-date'],int(e.attrib['data-count'])) for e in dots],
                         [(d['date'],d['count']) for d in days])
        self.assertIn('101 public contributions on 2 active days from 2025-10-31 to 2026-01-02', svg)
        self.assertIn('2025-10-31: 100 contributions', svg)
        self.assertNotIn('2026-01-03: 0 contributions', svg)

    def test_date_mapping_and_counts(self):
        html=fixture([('2026-01-01',0,'No contributions on January 1st.'),
                      ('2026-01-02',2,'1,234 contributions on January 2nd.')])
        days=parse_calendar(html,minimum_days=2)
        self.assertEqual(summary(days)['total'],1234)
        self.assertEqual(summary(days)['active_days'],1)
        for mode in ('dark','light'):
            svg=render(days,mode)
            ET.fromstring(svg)
            self.assertIn('2026-01-02: 1234 contributions',svg)

    def test_rejects_missing_tooltip(self):
        with self.assertRaises(ValueError):
            parse_calendar('<td data-date="2026-01-01" data-level="2" id="x"></td>',minimum_days=1)

    def test_rejects_missing_day(self):
        html=fixture([('2026-01-01',0,'No contributions on January 1st.'),
                      ('2026-01-03',1,'1 contribution on January 3rd.')])
        with self.assertRaises(ValueError):
            parse_calendar(html,minimum_days=2)

    def test_rejects_inconsistent_intensity(self):
        html=fixture([('2026-01-01',3,'No contributions on January 1st.')])
        with self.assertRaises(ValueError):
            parse_calendar(html,minimum_days=1)

    def test_rejects_partial_response(self):
        html=fixture([('2026-01-01',0,'No contributions on January 1st.')])
        with self.assertRaises(ValueError):
            parse_calendar(html)

if __name__=='__main__':
    unittest.main()
