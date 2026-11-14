from pathlib import Path
import json, csv, shutil, hashlib, collections, statistics, datetime

ZONE = Path(r'C:\Users\ubu\Desktop\Zone')
CCIS = Path(r'C:\Users\ubu\Desktop\CCIS')
STAGE = ZONE / 'tmp/ccis_rewrite_20261114'
EVID = STAGE / 'evidence/completed_20261114'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def jl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def key(r): return (r['arch'], r['payload'], r['tech'], r['shots'])
def dump(name, obj): (EVID/name).write_text(json.dumps(obj, indent=2), encoding='utf-8')
def csvout(name, rows):
    with (EVID/name).open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

STAGE.mkdir(exist_ok=True)
(STAGE/'sections').mkdir(exist_ok=True)
(STAGE/'qa').mkdir(exist_ok=True)
for name in ['main.tex','bibliography.bib','llncs.cls','splncs04.bst','build.ps1','BASELINE_CHECKS.md']:
    shutil.copy2(CCIS/name,STAGE/name)
for p in (CCIS/'sections').glob('*.tex'): shutil.copy2(p,STAGE/'sections'/p.name)
shutil.copytree(CCIS/'evidence',STAGE/'evidence',dirs_exist_ok=True)
EVID.mkdir(exist_ok=True)
prior={str(p.relative_to(CCIS)):digest(p) for p in [CCIS/'main.tex',CCIS/'bibliography.bib',CCIS/'main.pdf',*(CCIS/'sections').glob('*.tex')]}
paths=['CAMPAIGN_REPORT.md','vt_manifest_campaign.json','tmp/vt_results_campaign.jsonl']
paths += ['tmp/campaign/'+n for n in ['llm_build.jsonl','llm_test.jsonl','llm_summary.csv','build_llm.py','summarize_llm.py','harness.py','baseline_originals.jsonl','wrap_build.jsonl','wrap_test.jsonl','wrap_retest.jsonl','prewarm_xd.jsonl','symbolic_build.jsonl','symbolic_test.jsonl','llm_data_build.jsonl','lldata_test.jsonl','data_compare.csv']]
paths += [str(p.relative_to(ZONE)).replace('\\','/') for p in (ZONE/'tmp/campaign/llm_stats').rglob('*.json')]
paths += ['bench/engines/2026-11-13_block3/'+n for n in ['pobf.py','pobf86.py','asm_wrap.py','llm_payload.py','llm_technique.py','llm_data.py','symbolic_payload_coverage.py'] if (ZONE/'bench/engines/2026-11-13_block3'/n).exists()]
manifest={'frozen_at_berlin':datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=1))).isoformat(timespec='seconds'),'prior_ccis_hashes':prior,'sources':[]}
for name in paths:
    p=ZONE/name; raw=p.read_bytes(); out=EVID/'sources'/name
    out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(raw)
    manifest['sources'].append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
src=EVID/'sources'
build=jl(src/'tmp/campaign/llm_build.jsonl'); tests=jl(src/'tmp/campaign/llm_test.jsonl')
bykey=collections.defaultdict(list)
for r in build: bykey[key(r)].append(r)
assert len(bykey)==816 and len(build)==830
assert all([r['status'] for r in v]==['fail','fail'] for v in bykey.values() if len(v)>1)
testmap={key(r):r for r in tests}; assert len(testmap)==350
# Match the pre-existing summary policy: first record, unless a later build succeeds.
cells=[]
for k,rs in sorted(bykey.items()):
    r=next((r for r in rs if r['status']=='ok'),rs[0]); t=testmap.get(k)
    if t: assert t['sha256']==r['sha256']
    cells.append({**r,'working':bool(t and t['status']=='OK'),'run_records':len(rs),'all_run_cost':sum(x.get('cost_usd') or 0 for x in rs)})
def aggregate(rs):
    return {'cells':len(rs),'built':sum(r['status']=='ok' for r in rs),'working':sum(r['working'] for r in rs),'unique':len({r['sha256'] for r in rs if r['status']=='ok'}),'all_run_cost_usd':sum(r['all_run_cost'] for r in rs)}
conditions=[]
for a in ['x64','x86']:
    for f in ['eq','nop','bcf','ibp']:
        for s in [0,2]:
            rs=[r for r in cells if (r['arch'],r['tech'],r['shots'])==(a,f,s)]
            conditions.append({'arch':a,'family':f,'shots':s,**aggregate(rs)})
csvout('llm_by_condition.csv',conditions)
summary={'llm':aggregate(cells),'llm_by_arch':{a:aggregate([r for r in cells if r['arch']==a]) for a in ['x64','x86']},'llm_by_shots':{s:aggregate([r for r in cells if r['shots']==s]) for s in [0,2]},'run_records':len(build),'restarted_cells':sum(len(rs)>1 for rs in bykey.values()),'recorded_api_calls':sum(r.get('api_calls') or 0 for r in build),'missing_usage_records':sum(r.get('api_calls') is None for r in build),'multi_generation_records':sum((r.get('attempts') or 0)>1 for r in build),'all_run_cost_usd':sum(r.get('cost_usd') or 0 for r in build),'retained_cell_cost_usd':sum(r.get('cost_usd') or 0 for r in cells)}
csvout('llm_cells.csv',[{k:r.get(k) for k in ['arch','payload','tech','shots','status','working','sha256','attempts','run_records','all_run_cost']} for r in cells])
def failure(error):
    if 'truncated' in error or 'finish_reason=length' in error:return 'length'
    if 'not fully disassembled' in error or 'instruction boundary' in error:return 'disassembly'
    if 'IncompleteRead' in error or 'timed out' in error or 'HTTP' in error:return 'network'
    if 'did not produce a valid' in error or 'rejected' in error:return 'validation'
    if 'data' in error and ('extract' in error or 'xref' in error):return 'data'
    return 'other'
summary['failure_labels']=dict(collections.Counter(failure(r.get('error','')) for r in cells if r['status']=='fail'))
summary['accepted_similarity_mean']=statistics.mean(r['similarity'] for r in cells if r['status']=='ok')
summary['retained_run_median_seconds']=statistics.median(r['elapsed_s'] for r in cells)
scans={r['sha256']:r for r in jl(src/'tmp/vt_results_campaign.jsonl') if r['status']=='completed'}
m=json.loads((src/'vt_manifest_campaign.json').read_text()); hashes={r['sha256'] for r in m}
assert set(scans)==hashes and len(hashes)==549 and len(m)==612
def scanagg(hs):
    recorded=[scans[h] for h in hs]
    valid=[r for r in recorded if sum(r['stats'].values())>0]
    return {'hashes':len(hs),'completed_records':len(recorded),'evaluable':len(valid),'empty_reports':len(recorded)-len(valid),'detected':sum(r['malicious']>0 for r in valid),'mean_malicious':statistics.mean(r['malicious'] for r in valid),'mean_fraction_all_responses':statistics.mean(r['malicious']/sum(r['stats'].values()) for r in valid),'stats':dict(sum((collections.Counter(r['stats']) for r in valid),collections.Counter()))}
groups=[]
for g in sorted({r['technique'] for r in m}):
    s=scanagg({r['sha256'] for r in m if r['technique']==g})
    groups.append({'group':g,**{k:v for k,v in s.items() if k!='stats'}})
csvout('vt_by_membership.csv',groups)
summary['scans_all']=scanagg(hashes)
summary['scans_groups']={g:scanagg({r['sha256'] for r in m if (r['technique'].startswith('llm_') if g=='llm' else r['technique']==g)}) for g in ['wrap','llm','lldata']}
summary['last_scan_record']=max(r['date'] for r in scans.values())
summary['scan_functional_split']={}
for ok in [True,False]:
    hs={r['sha256'] for r in cells if r['status']=='ok' and r['working']==ok}
    summary['scan_functional_split'][str(ok)]={'files':sum(r['status']=='ok' and r['working']==ok for r in cells),**scanagg(hs)}
assert not ({r['sha256'] for r in cells if r['status']=='ok' and r['working']} & {r['sha256'] for r in cells if r['status']=='ok' and not r['working']})
summary['empty_scan_hashes']=[h for h,r in scans.items() if not sum(r['stats'].values())]
dump('SOURCES.json',manifest);dump('SUMMARY.json',summary)
print(json.dumps(summary,indent=2))
print('STAGE',STAGE)
