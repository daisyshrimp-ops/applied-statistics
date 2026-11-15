"""Small offline data tables used by the site's reactive UICrit controls."""
from pathlib import Path
import ast
import re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/'public/uicrit_public.csv')
ratings=df[['rico_id','aesthetics_rating','usability_rating']].copy()
assert ratings.rico_id.notna().all()
assert ratings.aesthetics_rating.between(1,10).all() and ratings.usability_rating.between(1,10).all()
screens=ratings.groupby('rico_id',as_index=False).agg(aesthetics_mean=('aesthetics_rating','mean'),usability_mean=('usability_rating','mean'),n_ratings=('aesthetics_rating','size'))
THEMES={'Цвет и контраст':r'\bcolou?r\w*|\bcontrast\w*','Текст и шрифт':r'\bfont\w*|\btext\s+size\b|\breadab\w*','Кнопки':r'\bbutton\w*','Иконки':r'\bicon\w*'}
LINK_THEMES={**THEMES,'Цвет и контраст':r'\b(?:colou?r|contrast)\b','Текст и шрифт':r'\bfont\w*\b|\btext\s+size\b|\breadab\w*\b','Кнопки':r'\bbutton\w*\b','Иконки':r'\bicon\w*\b'}
pattern=re.compile(r'Bounding\s+Box:\s*\[([^\]]+)\]',re.I)
boxes,comments=[],[]
for _,row in df.iterrows():
    texts,sources=ast.literal_eval(row.comments),ast.literal_eval(row.comments_source)
    if len(texts)!=len(sources):sources=[None]*len(texts)
    for text,source in zip(texts,sources):
        clean=pattern.sub('',text).lower()
        comments.append({'rico_id':row.rico_id,**{k:bool(re.search(p,clean)) for k,p in LINK_THEMES.items()}})
        match=pattern.search(text)
        if not match:continue
        x1,y1,x2,y2=map(float,match[1].split(','))
        assert 0<=x1<x2<=1 and 0<=y1<y2<=1
        boxes.append({'rico_id':row.rico_id,'source':source,'x1':x1,'y1':y1,'x2':x2,'y2':y2,'area':(x2-x1)*(y2-y1),'h':(y1+y2)/2,**{k:int(bool(re.search(p,text.lower()))) for k,p in THEMES.items()}})
pd.DataFrame(boxes).to_csv(ROOT/'public/uicrit_boxes.csv',index=False)
pd.DataFrame(comments).groupby('rico_id')[list(LINK_THEMES)].mean().reset_index().to_csv(ROOT/'public/uicrit_screen_themes.csv',index=False)
screens.to_csv(ROOT/'public/uicrit_screens.csv',index=False)
ratings.to_csv(ROOT/'public/uicrit_ratings.csv',index=False)
print('UICrit prepared:',len(screens),'screens,',len(boxes),'boxes')
