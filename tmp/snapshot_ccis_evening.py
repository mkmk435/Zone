from pathlib import Path
import json,csv,hashlib,collections,statistics,shutil,datetime,re

ZONE=Path(r'C:\Users\ubu\Desktop\Zone')
CCIS=Path(r'C:\Users\ubu\Desktop\CCIS')
ROOT=ZONE/'tmp/ccis_update_20261113'
ROOT.mkdir(exist_ok=True)
(ROOT/'sections').mkdir(exist_ok=True)
(ROOT/'qa').mkdir(exist_ok=True)
EVID=ROOT/'evidence'
(EVID/'sources').mkdir(parents=True,exist_ok=True)
for n in ['main.tex','bibliography.bib','llncs.cls','splncs04.bst','build.ps1','README_REVISIONE.md','EDITOR_DIFFERENCES.txt','BASELINE_CHECKS.md']:
    shutil.copy2(CCIS/n,ROOT/n)
for p in (CCIS/'sections').glob('*.tex'):shutil.copy2(p,ROOT/'sections'/p.name)

stamp=datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=1)))
manifest={'cutoff_berlin':stamp.isoformat(timespec='seconds'),'timezone':'Europe/Berlin (UTC+01:00 on 13 November 2026)','sources':[],
 'prior_ccis_hashes':{str(p.relative_to(CCIS)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [CCIS/'main.tex',CCIS/'bibliography.bib',*(CCIS/'sections').glob('*.tex')]}}
sources={}
paths=['bench/results/native_attempts.jsonl','bench/results/native_wrap86.jsonl','bench/results/llm_attempts.jsonl','bench/results/llm_attempts_x86.jsonl','bench/results/llm_data_attempts.jsonl','bench/results/classifier_compare.jsonl','bench/fixtures/cases.json','bench/fixtures/classifier_cases.json','bench/engines/2026-11-13_block1/VERSION.json','bench/engines/2026-11-13_block2/VERSION.json','bench/results/vt_audit.json','tmp/campaign/baseline_originals.jsonl','tmp/campaign/prewarm_xd.jsonl','tmp/campaign/wrap_build.jsonl','tmp/campaign/wrap_test.jsonl','tmp/campaign/wrap_retest.jsonl','tmp/campaign/llm_build.jsonl','tmp/campaign/llm_data_build.jsonl','tmp/campaign/lldata_test.jsonl','tmp/campaign/symbolic_build.jsonl','tmp/campaign/symbolic_test.jsonl','tmp/campaign/data_compare.csv','vt_manifest.json','tmp/vt_results.jsonl','vt_originals.json','tmp/vt_results_original.jsonl','vt_manifest_campaign.json','tmp/vt_results_campaign.jsonl']
for name in paths:
    p=ZONE/name
    if not p.exists():continue
    raw=p.read_bytes()
    target=EVID/'sources'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    manifest['sources'].append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    text=raw.decode('utf-8-sig')
    if name.endswith('.jsonl'):
        records=[]
        for line in text.splitlines():
            if line.strip():
                try:records.append(json.loads(line))
                except json.JSONDecodeError:pass
        sources[name]=records
    elif name.endswith('.json'):sources[name]=json.loads(text)
    else:sources[name]=list(csv.DictReader(text.splitlines()))

def rows(n):return sources[n]
def groups(data,keys):
    out=collections.defaultdict(list)
    for r in data:out[tuple(r.get(k) for k in keys)].append(r)
    return out
def mean(xs):return statistics.mean(xs) if xs else None
def writecsv(name,data):
    if not data:return
    with (EVID/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)

summary={'cutoff_berlin':manifest['cutoff_berlin']}
native=rows('bench/results/native_attempts.jsonl')+rows('bench/results/native_wrap86.jsonl')
native=[r for r in native if r['technique']!='xd']
native_summary=[]
for (arch,tech),rs in sorted(groups(native,['arch','technique']).items()):
    built=[r for r in rs if r['build_ok']]
    native_summary.append({'arch':arch,'technique':tech,'block':2 if arch=='x86' and tech=='wrap' else 1,'n':len(rs),'built':len(built),'working':sum(r['match'] for r in rs),'unique':len({r['sha256'] for r in built})})
summary['native']=native_summary;writecsv('native.csv',native_summary)

llm=rows('bench/results/llm_attempts.jsonl')+rows('bench/results/llm_attempts_x86.jsonl')
stat_sources=[]
for r in llm:
    r['similarity']=None
    if r.get('stats'):
        p=ZONE/r['stats']
        if p.exists():
            raw=p.read_bytes();d=json.loads(raw)
            r['model']=d.get('model');r['similarity']=(d.get('payload') or {}).get('similarity') if r['build_ok'] else None
            stat_sources.append({'path':r['stats'],'sha256':hashlib.sha256(raw).hexdigest()})
            dest=EVID/'sources'/r['stats'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
llm_summary=[]
for (arch,tech,shot),rs in sorted(groups(llm,['arch','technique','shots']).items()):
    bs=[r for r in rs if r['build_ok']]
    llm_summary.append({'arch':arch,'technique':tech,'shots':shot,'block':1 if arch=='x64' else 2,'n':len(rs),'built':len(bs),'working':sum(r['match'] for r in rs),'unique':len({r['sha256'] for r in bs}),'similarity':mean([r['similarity'] for r in bs if r['similarity'] is not None]),'cost_usd':sum(r.get('cost_usd') or 0 for r in rs),'mean_seconds':mean([r['elapsed'] for r in rs])})
summary['llm']=llm_summary;writecsv('llm_benign.csv',llm_summary)
summary['llm_by_arch']={a:{'n':len(rs),'built':sum(r['build_ok'] for r in rs),'working':sum(r['match'] for r in rs),'unique':len({r['sha256'] for r in rs if r['build_ok']}),'cost_usd':sum(r.get('cost_usd') or 0 for r in rs)} for (a,),rs in groups(llm,['arch']).items()}
manifest['stats_sources']=stat_sources

cls=rows('bench/results/classifier_compare.jsonl')
cls_summary=[]
for (arch,case,method),rs in sorted(groups(cls,['arch','case','method']).items()):
    cls_summary.append({'arch':arch,'case':case,'method':method,'n':len(rs),'exact':sum(r['evaluation']['exact'] for r in rs),'false_positive_bytes':sum(r['evaluation']['code_false_positive_bytes'] for r in rs),'data_bytes':rs[0]['evaluation']['data_total_bytes'],'working':sum(r['match'] for r in rs),'mean_seconds':mean([r['elapsed'] for r in rs]),'cost_usd':sum(r.get('cost_usd') or 0 for r in rs)})
summary['classifier']=cls_summary;writecsv('classifier.csv',cls_summary)

wb=rows('tmp/campaign/wrap_build.jsonl');wt=rows('tmp/campaign/wrap_test.jsonl')
tests={r['path'].replace('\\','/'):r for r in wt}
wrap_summary=[]
for (arch,),rs in sorted(groups(wb,['arch']).items()):
    bs=[r for r in rs if r['status']=='ok']
    wrap_summary.append({'arch':arch,'inputs':len({r['payload'] for r in rs}),'n':len(rs),'built':len(bs),'tested':sum(r['out'].replace('\\','/') in tests for r in bs),'working':sum(tests.get(r['out'].replace('\\','/'),{}).get('status')=='OK' for r in bs),'unique':len({r['sha256'] for r in bs})})
summary['wrap_full']=wrap_summary;writecsv('wrap_full_corpus.csv',wrap_summary)

data_rows=rows('tmp/campaign/data_compare.csv')
summary['data_payloads']={'n':len(data_rows),'symbolic_built':sum(int(r['symbolic_built']) for r in data_rows),'symbolic_working':sum(int(r['symbolic_working']) for r in data_rows),'llm_built':sum(int(r['llm_built']) for r in data_rows),'llm_working':sum(int(r['llm_working']) for r in data_rows),'raw_range_agreement':sum(int(r['exact_sections']) for r in data_rows),'identical_outputs':sum(int(r['final_identical']) for r in data_rows),'symbolic_median_seconds':statistics.median(float(r['symbolic_time_s']) for r in data_rows),'llm_median_seconds':statistics.median(float(r['llm_time_s']) for r in data_rows),'cost_usd':sum(float(r['llm_cost_usd']) for r in data_rows),'archs':dict(collections.Counter(r['arch'] for r in data_rows))}

live=rows('tmp/campaign/llm_build.jsonl')
summary['llm_full_progress']={'records':len(live),'unique_cells':len({(r['arch'],r['payload'],r['tech'],r['shots']) for r in live}),'success':sum(r['status']=='ok' for r in live),'fail':sum(r['status']=='fail' for r in live),'api_calls_recorded':sum(r.get('api_calls') or 0 for r in live),'cost_recorded':sum(r.get('cost_usd') or 0 for r in live),'planned_cells':816}
vc={r['sha256']:r for r in rows('tmp/vt_results_campaign.jsonl')}
summary['live_scans']={'manifest_hashes':len({r['sha256'] for r in rows('vt_manifest_campaign.json')}),'recorded_hashes':len(vc),'status':dict(collections.Counter(r['status'] for r in vc.values()))}

vt_latest={r['sha256']:r for r in rows('tmp/vt_results.jsonl')}
vt_summary=[]
for (tech,),rs in sorted(groups(rows('vt_manifest.json'),['technique']).items()):
    hashes={r['sha256'] for r in rs};complete=[vt_latest[h] for h in hashes if vt_latest.get(h,{}).get('status')=='completed']
    def total(r):return r.get('total') or sum((r.get('stats') or {}).values())
    vt_summary.append({'technique':tech,'files':len(rs),'unique':len(hashes),'completed':len(complete),'detected':sum(r['malicious']>0 for r in complete),'mean_malicious':mean([r['malicious'] for r in complete]),'mean_fraction_all_reported':mean([r['malicious']/total(r) for r in complete]),'engines_total':sum(total(r) for r in complete),'unsupported':sum((r.get('stats') or {}).get('type-unsupported',0) for r in complete)})
summary['vt_previous']=vt_summary;writecsv('vt_previous_by_membership.csv',vt_summary)
summary['model_identifiers']=sorted({r.get('model') for r in llm if r.get('model')})
summary['classifier_fixtures']=sources['bench/fixtures/classifier_cases.json']

engine_hashes={}
for block in ['block1','block2','block3']:
    engine_hashes[block]={n:hashlib.sha256((ZONE/'bench/engines'/('2026-11-13_'+block)/n).read_bytes()).hexdigest() for n in ['pobf.py','pobf86.py','asm_wrap.py','llm_technique.py','llm_data.py','llm_payload.py']}
manifest['engine_hashes']=engine_hashes
(EVID/'SOURCES.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(EVID/'SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['classifier_fixtures','classifier','llm','native']},indent=2))
