"""Compile checked notebook results into portable report assets (no Colab widgets)."""
import base64
import html
import json
import re
from pathlib import Path
import marimo as mo
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPORTS = {}
for name in ['sprint1', 'sprint2', 'uicrit']:
    original = json.loads((ROOT / 'research' / f'{name}.ipynb').read_text(encoding="utf-8"))
    executed = json.loads((ROOT / 'research' / f'{name}.executed.ipynb').read_text(encoding="utf-8"))
    if len(original['cells']) != len(executed['cells']):
        raise RuntimeError(f'{name}: rerun the notebook after changing its cell structure')
    items = []
    cell_ids = {str(c.get('id',c.get('metadata',{}).get('id',''))): i for i,c in enumerate(original['cells'])}
    output_dir = ROOT / 'public/reports' / name
    output_dir.mkdir(parents=True, exist_ok=True)
    heading_counts = [0, 0, 0, 0, 0, 0]
    current_main = None
    for i, (source, result) in enumerate(zip(original['cells'], executed['cells'])):
        raw_text = ''.join(source['source'])
        text = raw_text
        if source['cell_type'] == 'markdown':
            text = re.sub(r'<a[^>]+colab[^>]*>.*?</a>', '', text, flags=re.S)
            text = re.sub(r'(?m)^(\s*#{1,6})(?!#)(?=\S)', r'\1 ', text)
            # Keep markdown tables/lists valid even when the source omits a blank line.
            lines = []
            for line in text.splitlines():
                if line.startswith('|') and lines and lines[-1].strip() and not lines[-1].startswith('|'):
                    lines.append('')
                if line.startswith('|'):
                    line = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', lambda m: '$'+m[1].replace('|',r'\vert ')+'$', line)
                lines.append(line)
            text = '\n'.join(lines)
            text = re.sub(r'\$\$(.*?)\$\$', lambda m: '\n\n$$\n'+m[1].strip()+'\n$$\n\n', text, flags=re.S)
            text = re.sub(r'#scrollTo=([A-Za-z0-9_-]+)', lambda m: '#cell-'+str(cell_ids[m[1]]) if m[1] in cell_ids else '#cell-'+str(i), text)
            if name == 'sprint1':
                main=0 if i<19 else 1 if i<64 else 2 if i<102 else 3 if i<138 else 4 if i<143 else 5 if i<149 else 7 if i<151 or i>=153 else 6
            elif name == 'sprint2':
                main=1 if i<39 else 2 if i<76 else 3 if i<111 else 4
            else: main=0
            if main!=current_main:
                heading_counts=[0,0,0,0,0,0]
                current_main=main
            rendered = mo.md(text).text
            heading = [0]
            def heading_id(m):
                heading[0] += 1
                level=int(m[1][1])
                heading_counts[level-1]+=1
                for deeper in range(level,6): heading_counts[deeper]=0
                ident=name+'-heading-'+str(i)+'-'+str(heading[0])
                badge=''
                if name in ('sprint1','sprint2') and level>=3:
                    numbers=[str(current_main)]+[str(n or 1) for n in heading_counts[2:level]]
                    badge='<span class="notebook-index">'+'.'.join(numbers)+'</span>'
                return '<'+m[1]+' id="'+ident+'">'+badge
            rendered = re.sub(r'<(h[1-6])(?:\s[^>]*)?>', heading_id, rendered)
            rendered = re.sub(r'(id|href)="(#?)([^"#]+)"', lambda m: m[0] if (m[1]=='href' and not m[2]) or m[3].startswith(name+'-') else m[1]+'="'+m[2]+name+'-'+m[3]+'"', rendered)
            items.append({'kind': 'markdown', 'html': rendered, 'source': raw_text})
            continue
        parts = []
        for j, output in enumerate(result.get('outputs', [])):
            if output['output_type'] == 'error':
                raise RuntimeError(f'{name} cell {i}: execution error')
            data = output.get('data', {})
            if 'image/png' in data:
                filename = f'{i}-{j}.png'
                image_data=''.join(data['image/png']).strip()
                image_bytes=base64.b64decode(image_data,validate=True)
                (output_dir / filename).write_bytes(image_bytes)
                width, height = Image.open(output_dir / filename).size
                kind='plot-wide' if width/height>=1.6 else 'plot-portrait' if width/height<.85 else 'plot-square'
                # Relative public URLs depend on the marimo mount location and
                # previously produced large broken-image slots on Windows.
                # Preserve the exact notebook PNG bytes inside the report.
                parts.append(f'<figure class="plot {kind}"><img width="{width}" height="{height}" decoding="async" data-report-asset="./public/reports/{name}/{filename}" src="data:image/png;base64,{image_data}" alt="График исследования" /></figure>')
            elif 'text/html' in data:
                parts.append('<div class="tbl-wrap">' + ''.join(data['text/html']) + '</div>')
            elif output['output_type'] == 'stream':
                value = ''.join(output.get('text', ''))
                if output.get('name') == 'stderr':
                    continue
                value = re.sub(r'\x1b\[[0-9;]*m', '', value)
                value = re.sub(r'Out\[\d+\]: ', '', value)
                if 'pytest' in text and re.search(r'\d+ passed', value):
                    value = re.search(r'\d+ passed[^\n\r]*', value)[0] + '\nПроверенный запуск тестов генераторов.'
                if value.strip():
                    parts.append('<pre class="numeric-result">' + html.escape(value) + '</pre>')
            elif 'text/plain' in data and not any(k.startswith('application/') for k in data):
                value = ''.join(data['text/plain'])
                if not value.startswith(('<Figure', '<Axes', 'None')):
                    parts.append('<pre class="numeric-result">' + html.escape(value) + '</pre>')
        result_html = ''.join(parts)
        items.append({'kind': 'code', 'html': result_html, 'source': raw_text})
    REPORTS[name] = items

from prepare_performance import prepare_performance
prepare_performance(REPORTS)

(ROOT / 'report_data.py').write_text('# Generated from research/*.executed.ipynb; regenerate with tools/prepare_reports.py\nREPORTS = ' + repr(REPORTS) + '\n',encoding='utf-8')
print('Compiled', {k: len(v) for k,v in REPORTS.items()})

# The saved Colab run is authoritative for the bootstrap intervals in 6.2.
# Transfer its table, rather than replacing confidence intervals with bars.
from html.parser import HTMLParser
import csv
class _ReportTable(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=[];self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ('th','td'):self.cell=''
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag in ('th','td') and self.cell is not None:
            self.row.append(self.cell.strip());self.cell=None
        if tag=='tr' and self.row:self.rows.append(self.row)
_theme_table=_ReportTable();_theme_table.feed(REPORTS['uicrit'][87]['html'])
with (ROOT/'public/uicrit_theme_intervals.csv').open('w',encoding='utf-8',newline='') as _file:
    _writer=csv.writer(_file)
    for _row in _theme_table.rows:_writer.writerow(_row[1:])
