"""Verify original chart bytes are portable, decodable and independent of paths."""
import base64
from io import BytesIO
from pathlib import Path
import re
import sys
from PIL import Image,ImageStat
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from report_data import REPORTS
found=[]
for study,items in REPORTS.items():
    for index,item in enumerate(items):
        assert not re.search(r'src="\./public/reports/',item['html']),(study,index)
        for attrs in re.findall(r'<img\b([^>]+)>',item['html']):
            source=re.search(r'src="([^"]+)"',attrs)
            asset=re.search(r'data-report-asset="([^"]+)"',attrs)
            if not asset:continue
            assert source and source[1].startswith('data:image/png;base64,'),(study,index)
            raw=base64.b64decode(source[1].split(',',1)[1],validate=True)
            assert raw==(ROOT/asset[1].removeprefix('./')).read_bytes(),(study,index,'Changed PNG')
            image=Image.open(BytesIO(raw));image.load()
            assert image.width>100 and image.height>100
            assert max(ImageStat.Stat(image.convert('RGB')).stddev)>3,(study,index,'Blank PNG')
            found.append((study,index,asset[1]))
assert len(found)==48,len(found)
assert {('sprint2',i) for i in [18,25,52,56]}<={(s,i) for s,i,_ in found}
print('PASS: all 48 exact original PNGs embedded, decoded and checked for visible content')
print('PASS: screenshot cases sprint2 cells 18, 25, 52 and 56 do not request external images')
