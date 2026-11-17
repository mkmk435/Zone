from pathlib import Path
import re, json, hashlib, sys
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
sys.stdout.reconfigure(encoding='utf-8')
root=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
qa=root/'qa_structure_20261116'
qa.mkdir(exist_ok=True)
report={'pdf_sha256':hashlib.sha256((root/'main.pdf').read_bytes()).hexdigest()}
texts=[]
with pdfplumber.open(root/'main.pdf') as pdf:
    report['pages']=len(pdf.pages)
    outside=[]
    for i,page in enumerate(pdf.pages,1):
        t=page.extract_text() or ''
        texts.append(t)
        outside.extend({'page':i,'text':c['text']} for c in page.chars if c['x0'] < -0.5 or c['x1'] > page.width+0.5 or c['top'] < -0.5 or c['bottom'] > page.height+0.5)
        heads=[s for s in t.splitlines() if re.match(r'^\d+(?:\.\d+)?\s+[A-Z]',s) and 'Bistarelli' not in s]
        print(i,' | '.join(heads))
    report['out_of_page_characters']=outside
report['unresolved_markers']=[i+1 for i,t in enumerate(texts) if '??' in t or '\ufffd' in t]
(qa/'main.txt').write_text('\n\n'.join('PAGE '+str(i+1)+'\n'+t for i,t in enumerate(texts)),encoding='utf-8')
log=(root/'main.log').read_text(errors='replace')
report['overfull_boxes']=len(re.findall('Overfull',log))
report['undefined_references']=len(re.findall(r'(?:Reference|Citation).*undefined',log))
report['missing_glyph_warnings']=len(re.findall('Missing character',log))
def expanded(base,name='main.tex'):
    s=(base/name).read_text(encoding='utf-8')
    return re.sub(r'\\input\{([^}]+)\}',lambda m:expanded(base,m[1] if m[1].endswith('.tex') else m[1]+'.tex'),s)
old=expanded(root/'before_structure_revision_20261116')
new=expanded(root)
pattern=r'\\begin\{(tabularx?)\}.*?\\end\{\1\}'
old_tables=[m[0] for m in re.finditer(pattern,old,re.S)]
new_tables=[m[0] for m in re.finditer(pattern,new,re.S)]
report['table_bodies']={'before':len(old_tables),'after':len(new_tables),'all_identical':old_tables==new_tables}
report['retained_objects']={}
for env in ('figure','lstlisting','algorithm'):
    pattern=r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}'
    a=re.findall(pattern,old,re.S);b=re.findall(pattern,new,re.S)
    report['retained_objects'][env]={'before':len(a),'after':len(b),'all_identical':a==b}
    if env=='figure':
        a_unchanged=[x for x in a if r'\label{fig:extended_pipeline}' not in x]
        b_unchanged=[x for x in b if r'\label{fig:extended_pipeline}' not in x]
        assert a_unchanged==b_unchanged and len(a)==len(b),(env,report)
        report['retained_objects'][env]['intentional_revision']='Conceptual pipeline: explicit stop paths and shorter caption only.'
    else:
        assert a==b,(env,report)
assert 'The authors have no competing interests to declare.' in new
assert r'\footnotetext{\raggedright Extended and revised' not in new
assert r'\section{Discussion of the Extensions}' not in new
assert len(texts)<=30,report
assert old_tables==new_tables,report
assert not outside and not report['unresolved_markers'] and not report['overfull_boxes'] and not report['undefined_references'] and not report['missing_glyph_warnings'],report
pdf=pdfium.PdfDocument(root/'main.pdf')
for i in range(len(pdf)):
    page=pdf[i]
    bitmap=page.render(scale=1.6)
    bitmap.to_pil().convert('RGB').save(qa/f'page-{i+1:02d}.png')
    bitmap.close();page.close()
pdf.close()
for offset in range(0,len(texts),6):
    sheet=Image.new('RGB',(1200,1800),'#dddddd')
    draw=ImageDraw.Draw(sheet)
    for j in range(min(6,len(texts)-offset)):
        im=Image.open(qa/f'page-{offset+j+1:02d}.png').convert('RGB')
        im.thumbnail((580,560))
        x=(j%2)*600+(600-im.width)//2
        y=(j//2)*600+30
        sheet.paste(im,(x,y))
        draw.text((x,y-20),f'Page {offset+j+1}',fill='black')
    sheet.save(qa/f'contact-{offset//6+1}.jpg',quality=90)
report['rendered_pages']=len(texts)
(qa/'qa_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))

