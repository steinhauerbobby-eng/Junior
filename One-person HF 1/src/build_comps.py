import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime
import numpy as np

data = {
    'CRWD': {
        'name': 'CrowdStrike', 'mkt_cap': 132.43, 'ev': 123.89,
        'rev_ttm': 4.81, 'rev_growth': 23.3, 'gross_mgn': 74.7,
        'ebitda_mgn': 3.8, 'ni_mgn': -3.4,
        'pe_ttm': None, 'pe_fwd': 84.4, 'ev_ebitda': None,
        'ev_sales': 25.7, 'p_fcf': 106.7, 'nd_ebitda': None, 'roe': -4.1,
    },
    'PANW': {
        'name': 'Palo Alto Networks', 'mkt_cap': 166.52, 'ev': 156.29,
        'rev_ttm': 9.89, 'rev_growth': 14.9, 'gross_mgn': 73.5,
        'ebitda_mgn': 22.4, 'ni_mgn': 13.0,
        'pe_ttm': 113.4, 'pe_fwd': 51.7, 'ev_ebitda': 101.7,
        'ev_sales': 15.8, 'p_fcf': 46.7, 'nd_ebitda': -0.9, 'roe': 16.3,
    },
    'FTNT': {
        'name': 'Fortinet', 'mkt_cap': 83.39, 'ev': 76.97,
        'rev_ttm': 6.80, 'rev_growth': 20.1, 'gross_mgn': 80.5,
        'ebitda_mgn': 36.1, 'ni_mgn': 27.3,
        'pe_ttm': 47.1, 'pe_fwd': 33.4, 'ev_ebitda': 32.6,
        'ev_sales': 10.8, 'p_fcf': 37.5, 'nd_ebitda': -0.6, 'roe': 132.4,
    },
    'S': {
        'name': 'SentinelOne', 'mkt_cap': 5.46, 'ev': 4.80,
        'rev_ttm': 1.00, 'rev_growth': 20.2, 'gross_mgn': 74.1,
        'ebitda_mgn': -25.4, 'ni_mgn': -45.0,
        'pe_ttm': None, 'pe_fwd': 33.7, 'ev_ebitda': None,
        'ev_sales': 4.8, 'p_fcf': 105.7, 'nd_ebitda': None, 'roe': -29.0,
    },
}

tickers = ['CRWD', 'PANW', 'FTNT', 'S']
subject = 'CRWD'

metric_keys = ['mkt_cap', 'ev', 'rev_ttm', 'rev_growth', 'gross_mgn',
               'ebitda_mgn', 'ni_mgn', 'pe_ttm', 'pe_fwd', 'ev_ebitda',
               'ev_sales', 'p_fcf', 'nd_ebitda', 'roe']

def med_avg(metric):
    vals = [data[t][metric] for t in tickers if data[t][metric] is not None]
    if not vals:
        return None, None
    return round(float(np.median(vals)), 2), round(float(np.mean(vals)), 2)

median_row = {m: med_avg(m)[0] for m in metric_keys}
average_row = {m: med_avg(m)[1] for m in metric_keys}

def fmt(val, metric):
    if val is None:
        return 'NM'
    if metric in ['mkt_cap', 'ev']:
        return f'${val:.1f}B'
    if metric == 'rev_ttm':
        return f'${val:.2f}B'
    if metric in ['rev_growth', 'gross_mgn', 'ebitda_mgn', 'ni_mgn', 'roe']:
        return f'{val:.1f}%'
    if metric in ['pe_ttm', 'pe_fwd', 'ev_ebitda', 'ev_sales', 'p_fcf', 'nd_ebitda']:
        return f'{val:.1f}x'
    return str(val)

wb = openpyxl.Workbook()
ws1 = wb.active
ws1.title = 'Comps'

blue_fill = PatternFill('solid', fgColor='1F4E79')
green_fill = PatternFill('solid', fgColor='E2EFDA')
yellow_fill = PatternFill('solid', fgColor='FFFACD')
header_fill = PatternFill('solid', fgColor='2E75B6')
alt_fill = PatternFill('solid', fgColor='F2F2F2')
white_bold = Font(color='FFFFFF', bold=True)
header_font = Font(color='FFFFFF', bold=True, size=10)
bold = Font(bold=True)

headers = ['Ticker', 'Name', 'Mkt Cap', 'EV', 'Rev (TTM)', 'Rev Growth',
           'Gross Mgn', 'EBITDA Mgn', 'Net Mgn', 'P/E TTM', 'P/E Fwd',
           'EV/EBITDA', 'EV/Sales', 'P/FCF', 'ND/EBITDA', 'ROE']

ws1.merge_cells('A1:P1')
ws1['A1'] = f'COMPS — {subject} vs. Peers — {datetime.today().strftime("%Y-%m-%d")}'
ws1['A1'].font = Font(bold=True, size=13)
ws1['A1'].alignment = Alignment(horizontal='center')

for col, h in enumerate(headers, 1):
    cell = ws1.cell(row=3, column=col, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal='center')

for i, tk in enumerate(tickers):
    r = i + 4
    d = data[tk]
    ws1.cell(r, 1, tk)
    ws1.cell(r, 2, d['name'])
    for col, m in enumerate(metric_keys, 3):
        ws1.cell(r, col, fmt(d[m], m))
    for col in range(1, 17):
        cell = ws1.cell(r, col)
        cell.alignment = Alignment(horizontal='center' if col > 2 else 'left')
        if tk == subject:
            cell.fill = blue_fill
            cell.font = white_bold
        elif i % 2 == 1:
            cell.fill = alt_fill

med_r = len(tickers) + 4
ws1.cell(med_r, 1, 'Median')
for col, m in enumerate(metric_keys, 3):
    ws1.cell(med_r, col, fmt(median_row[m], m))
for col in range(1, 17):
    c = ws1.cell(med_r, col)
    c.fill = green_fill
    c.font = bold
    c.alignment = Alignment(horizontal='center' if col > 2 else 'left')

avg_r = med_r + 1
ws1.cell(avg_r, 1, 'Average')
for col, m in enumerate(metric_keys, 3):
    ws1.cell(avg_r, col, fmt(average_row[m], m))
for col in range(1, 17):
    c = ws1.cell(avg_r, col)
    c.fill = yellow_fill
    c.font = bold
    c.alignment = Alignment(horizontal='center' if col > 2 else 'left')

col_widths = [8, 20, 10, 10, 11, 11, 10, 11, 9, 9, 9, 11, 9, 8, 11, 8]
for i, w in enumerate(col_widths, 1):
    ws1.column_dimensions[get_column_letter(i)].width = w

ev_sales_med = median_row['ev_sales']
pe_fwd_med = median_row['pe_fwd']
ev_sales_prem = round((data[subject]['ev_sales'] - ev_sales_med) / ev_sales_med * 100, 1) if ev_sales_med else None
pe_fwd_prem = round((data[subject]['pe_fwd'] - pe_fwd_med) / pe_fwd_med * 100, 1) if pe_fwd_med else None

note_r = avg_r + 2
ws1.merge_cells(f'A{note_r}:P{note_r}')
note1 = f'CRWD vs. Median: EV/Sales +{ev_sales_prem}% premium | P/E Fwd +{pe_fwd_prem}% premium | EV/EBITDA NM (near breakeven GAAP EBITDA)'
ws1.cell(note_r, 1, note1).font = Font(italic=True, size=9)

ws1.merge_cells(f'A{note_r+1}:P{note_r+1}')
note2 = ('Assessment: CRWD trades at a steep premium on EV/Sales (25.7x vs. 13.3x median) and P/E Fwd (84x vs. 43x median), '
         'pricing in its leading revenue growth (23.3%) and platform consolidation positioning. '
         'FTNT is the clear value play at 33x fwd PE with 36% EBITDA margins — the profitability benchmark the group is measured against.')
c = ws1.cell(note_r + 1, 1, note2)
c.font = Font(size=9)
c.alignment = Alignment(wrap_text=True)
ws1.row_dimensions[note_r + 1].height = 32

ws2 = wb.create_sheet('Raw Data')
ws2.cell(1, 1, 'Timestamp')
ws2.cell(1, 2, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
raw_metrics = ['name', 'mkt_cap', 'ev', 'rev_ttm', 'rev_growth', 'gross_mgn',
               'ebitda_mgn', 'ni_mgn', 'pe_ttm', 'pe_fwd', 'ev_ebitda',
               'ev_sales', 'p_fcf', 'nd_ebitda', 'roe']
ws2.cell(2, 1, 'Ticker')
for ci, m in enumerate(raw_metrics, 2):
    ws2.cell(2, ci, m)
for ri, tk in enumerate(tickers, 3):
    ws2.cell(ri, 1, tk)
    for ci, m in enumerate(raw_metrics, 2):
        v = data[tk].get(m)
        ws2.cell(ri, ci, v if v is not None else 'NM')

fpath = 'reports/comps-CRWD-2026-05-08.xlsx'
wb.save(fpath)
print(f'Saved: {fpath}')
