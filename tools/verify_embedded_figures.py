"""Check archival notebook plots and the 12 portable build-prepared plots."""
import base64,json,re,sys
from io import BytesIO
from pathlib import Path
from PIL import Image,ImageStat
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from report_data import REPORTS
archives=0;prepared=0
for study,items in REPORTS.items():
    notebook=json.loads((ROOT/'research'/f'{study}.executed.ipynb').read_text(encoding='utf-8'))
    for index,cell in enumerate(notebook['cells']):
        for number,output in enumerate(cell.get('outputs',[])):
            encoded=output.get('data',{}).get('image/png')
            if encoded:
                raw=base64.b64decode(''.join(encoded),validate=True)
                assert raw==(ROOT/'public/reports'/study/f'{index}-{number}.png').read_bytes()
                archives+=1
    for index,item in enumerate(items):
        assert 'data-report-asset=' not in item['html']
        for markup in item.get('figures',[]):
            source=re.search(r'src="data:image/png;base64,([^"]+)"',markup)
            assert source,(study,index)
            image=Image.open(BytesIO(base64.b64decode(source[1],validate=True)));image.load()
            assert image.width>100 and image.height>100
            assert max(ImageStat.Stat(image.convert('RGB')).stddev)>3
            prepared+=1
assert archives==48 and prepared==12,(archives,prepared)
print('PASS: 48 original archived PNGs unchanged; 12 branded build-prepared plots decoded and nonblank')
