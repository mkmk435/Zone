from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from pypdf import PdfReader
import pdfplumber
import json
root=Path(__file__).resolve().parent.parent
qa=root/'qa'
reader=PdfReader(root/'main.pdf')
texts=[p.extract_text() or '' for p in reader.pages]
(qa/'extracted_text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(texts)),encoding='utf-8')
report={'pages':len(reader.pages),'unresolved_markers':[], 'page_summaries':[], 'out_of_page_characters':[]}
with pdfplumber.open(root/'main.pdf') as pdf:
    for i,p in enumerate(pdf.pages):
        chars=[c for c in p.chars if c.get('text','').strip()]
        outside=[c for c in chars if c['x0'] < 0 or c['x1'] > p.width+0.5 or c['top'] < 0 or c['bottom']>p.height+0.5]
        report['out_of_page_characters'].append(len(outside))
        t=texts[i]
        report['page_summaries'].append({'page':i+1,'characters':len(t),'first_lines':t.splitlines()[:4]})
        if '??' in t:report['unresolved_markers'].append(i+1)
paths=sorted(qa.glob('page-*.png'))
for batch in range(0,len(paths),6):
    sheet=Image.new('RGB',(1320,1218),'#e5e7eb')
    draw=ImageDraw.Draw(sheet)
    for j,path in enumerate(paths[batch:batch+6]):
        im=Image.open(path).convert('RGB')
        im.thumbnail((420,565))
        x=(j%3)*440+10;y=(j//3)*609+27
        sheet.paste(im,(x+(420-im.width)//2,y))
        draw.text((x,y-20),f'Page {batch+j+1}',fill='black')
    sheet.save(qa/f'contact-{batch//6+1}.png')
(qa/'qa_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
