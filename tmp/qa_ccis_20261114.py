from pathlib import Path
import re,json,hashlib
import pdfplumber
from PIL import Image,ImageDraw
root=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
qa=root/'qa'
report={'pdf_sha256':hashlib.sha256((root/'main.pdf').read_bytes()).hexdigest()}
with pdfplumber.open(root/'main.pdf') as pdf:
    report['pages']=len(pdf.pages)
    texts=[]; outside=[]; replacements=[]
    for i,p in enumerate(pdf.pages,1):
        text=p.extract_text() or '';texts.append(text)
        outside += [{'page':i,'text':c['text'],'bbox':[c['x0'],c['top'],c['x1'],c['bottom']]} for c in p.chars if c['x0'] < -0.5 or c['x1']>p.width+0.5 or c['top']< -0.5 or c['bottom']>p.height+0.5]
        if '\ufffd' in text:replacements.append(i)
        headings=[line for line in text.splitlines() if re.match(r'^\d+(?:\.\d+)?\s+[A-Z]',line)]
        print(i,' | '.join(headings))
    report['out_of_page_characters']=outside
    report['replacement_character_pages']=replacements
    report['unresolved_markers']=[i+1 for i,t in enumerate(texts) if '??' in t]
    (qa/'main.txt').write_text('\n\n'.join('PAGE '+str(i+1)+'\n'+t for i,t in enumerate(texts)),encoding='utf-8')
log=(root/'main.log').read_text(errors='replace')
report['overfull_boxes']=len(re.findall('Overfull',log))
report['undefined_references']=len(re.findall(r'(?:Reference|Citation).*undefined',log))
report['missing_glyph_warnings']=len(re.findall('Missing character',log))
old=Path(r'C:\Users\ubu\Desktop\CCIS\main.tex').read_text(); new=(root/'main.tex').read_text()
report['retained_baseline_objects']={}
for env in ['figure','table','lstlisting','algorithm']:
    pattern=r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}'
    a=re.findall(pattern,old,re.S);b=re.findall(pattern,new,re.S)
    report['retained_baseline_objects'][env]={'count':len(a),'unchanged':all(x in b for x in a)}
files=sorted(qa.glob('page-*.png'))
report['rendered_pages']=len(files)
for offset in range(0,len(files),6):
    sheet=Image.new('RGB',(1200,3*810),'#dddddd'); draw=ImageDraw.Draw(sheet)
    for j,p in enumerate(files[offset:offset+6]):
        im=Image.open(p).convert('RGB');im.thumbnail((590,770))
        x=(j%2)*600+(600-im.width)//2;y=(j//2)*810+30
        sheet.paste(im,(x,y));draw.text((x,y-22),p.stem,fill='black')
    sheet.save(qa/f'contact-{offset//6+1}.jpg',quality=90)
(qa/'qa_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
