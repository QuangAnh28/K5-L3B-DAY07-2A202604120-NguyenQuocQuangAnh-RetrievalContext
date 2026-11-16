"""Dev comparison, immutable selection, and held-out test execution."""
import argparse
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from .common import ROOT, load, save, digest, evidence_hit
from .retrieval import Retrieval
from .agent import run

CONFIGS = {
 'baseline':{'method':'tfidf','top_k':3,'budget':2400,'max_searches':1,
             'hypothesis':'Lexical baseline with one search.'},
 'dense':{'method':'dense','top_k':3,'budget':2400,'max_searches':1,
          'hypothesis':'Semantic retrieval can match wording variants; compare with lexical.'},
 'hybrid':{'method':'hybrid','top_k':3,'budget':2400,'max_searches':1,
           'hypothesis':'Improvement 1: RRF combines semantic and lexical rankings (20 candidates each, k=60).'},
 'hybrid_context':{'method':'hybrid','top_k':6,'budget':6000,'max_searches':3,
          'hypothesis':'Improvement 2: larger context/top-k and multiple searches may recover missing evidence; bundled change, no attribution to one factor.'}}
CRITERION = ['dev audited grounded answer mean', 'dev original-query Context Evidence Rate', 'dev Evidence Hit@3', 'dev Hit@1',
             'lower median agent latency', 'config name']

def summarize(rows):
    good=[r for r in rows if r['status']!='error']
    answerable=[r for r in good if r['answerable']]
    def ratio(n,N): return {'n':n,'N':N,'rate':n/N if N else None}
    costs=[u.get('usage',{}).get('cost') for r in rows for u in r.get('model_usage',[]) if 'error' not in u]
    return {'cases':len(rows),'errors':len(rows)-len(good),
      'hit1':ratio(sum(r['original_hit1'] for r in answerable),len(answerable)),
      'hit3':ratio(sum(r['original_hit3'] for r in answerable),len(answerable)),
      'original_context_evidence':ratio(sum(r['original_context_hit'] for r in answerable),len(answerable)),
      'final_context_evidence':ratio(sum(r['final_context_hit'] for r in answerable),len(answerable)),
      'tool_use':ratio(sum(r['searches']>0 for r in good),len(good)),
      'searches_distribution':{str(k):sum(r['searches']==k for r in good) for k in range(4)},
      'median_ms':statistics.median(r['elapsed_ms'] for r in good) if good else None,
      'model_cost_usd':sum(c for c in costs if c is not None), 'cost_missing_requests':sum(c is None for c in costs),
      'note':'Grounding/citation/abstention correctness require reading reviews; not inferred from IDs.'}

def execute(split, configs, workers=4):
    out=ROOT/'results'/split
    cases=[q for q in load(ROOT/'benchmark/cases.json') if q['split']==split]
    selection_path=ROOT/'results/selection.json'
    fingerprint={'benchmark_sha256':digest(ROOT/'benchmark/cases.json'),
                 'chunks_sha256':digest(ROOT/'data/day6/chunks.json'),
                 'agent_sha256':digest(ROOT/'src/agent.py'),'retrieval_sha256':digest(ROOT/'src/retrieval.py'),
                 'provider_sha256':digest(ROOT/'src/provider.py'),
                 'experiments_sha256':digest(ROOT/'src/experiments.py'),
                 'agent_model':os.getenv('AGENT_MODEL','openai/gpt-4.1-mini')}
    if split=='test':
        frozen=load(selection_path)
        if frozen['fingerprint']!=fingerprint or frozen['configs']!=CONFIGS:
            raise RuntimeError('Frozen configuration/code/corpus/benchmark changed; create a new test before tuning')
        configs=list(dict.fromkeys(['baseline',frozen['selected']]))
    else:
        protocol=ROOT/'results/protocol.json'
        value={'fingerprint':fingerprint,'configs':CONFIGS,'selection_criteria':CRITERION,
               'quality_selection':'Read and audit dev answers first; use disclosed AI-assisted grades, then context/retrieval metrics and latency.'}
        if protocol.exists() and load(protocol)!=value:
            raise RuntimeError('Protocol changed; archive run and explicitly establish a new experiment')
        save(protocol,value)
    retrieval=Retrieval()
    existing_usage=load(ROOT/'results/embedding_usage.json') if (ROOT/'results/embedding_usage.json').exists() else []
    try:
        for name in configs:
            config=CONFIGS[name]
            directory=out/name
            run_path=directory/'run.json'
            identity={'fingerprint':fingerprint,'config':config}
            if run_path.exists() and load(run_path)!=identity:
                raise RuntimeError('Output belongs to a different experiment')
            save(run_path,identity)
            rows=[]
            def one(q):
                path=directory/'queries'/(q['id']+'.json')
                if path.exists(): return load(path)
                diagnostic_started=time.perf_counter()
                try:
                    original=retrieval.search(q['question'],config['method'], max(3,config['top_k']),q.get('filter'))
                except Exception as exc:
                    result={'query_id':q['id'],'question':q['question'],'split':split,'config':name,
                        'answerable':q['answerable'],'status':'error','answer':'','citations':[],
                        'events':[{'event':'error','stage':'original_retrieval','type':type(exc).__name__}],
                        'context':'','context_ids':[],'searches':0,'model_usage':[],
                        'error':{'stage':'original_retrieval','type':type(exc).__name__,'message':str(exc)},
                        'elapsed_ms':(time.perf_counter()-diagnostic_started)*1000}
                    save(path,result)
                    return result
                from starter.baseline import pack_context
                oc,oi=pack_context(original[:config['top_k']],config['budget'])
                result=run(q['question'],retrieval,config,q.get('filter'))
                # Gold is accessed only after model execution, by the evaluator.
                gold=q.get('gold',[])
                result.update(query_id=q['id'],question=q['question'],split=split,config=name,answerable=q['answerable'],
                    original_results=original,original_context=oc,original_context_ids=oi,
                    original_hit1=bool(original and evidence_hit(original[0],gold)),
                    original_hit3=any(evidence_hit(c,gold) for c in original[:3]),
                    original_context_hit=any(c['id'] in oi and evidence_hit(c,gold) for c in original),
                    final_context_hit=any(evidence_hit(retrieval.by_id[cid],gold) for cid in result['context_ids']))
                save(path,result)
                return result
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures={pool.submit(one,q):q['id'] for q in cases}
                for f in as_completed(futures):
                    row=f.result();rows.append(row)
                    print(split,name,row['query_id'],row['status'],flush=True)
            rows.sort(key=lambda r:r['query_id'])
            save(directory/'traces.json',rows);save(directory/'summary.json',summarize(rows))
    finally:
        save(ROOT/'results/embedding_usage.json',existing_usage+retrieval.provider.usage)
        retrieval.close()

def freeze():
    protocol=load(ROOT/'results/protocol.json')
    if (ROOT/'results/test').exists(): raise RuntimeError('Test already started; selection cannot be changed')
    summaries={name:load(ROOT/'results/dev'/name/'summary.json') for name in CONFIGS}
    if any(s['errors'] or s['cases']<17 for s in summaries.values()):
        raise RuntimeError('Dev incomplete/errors: investigate before selection')
    audits={name:load(ROOT/'results/dev'/name/'audit_summary.json') for name in CONFIGS}
    selected=sorted(CONFIGS,key=lambda n:(-audits[n]['grounded_answer']['mean'],-summaries[n]['original_context_evidence']['rate'],
        -summaries[n]['hit3']['rate'],-summaries[n]['hit1']['rate'],summaries[n]['median_ms'],n))[0]
    path=ROOT/'results/selection.json'
    if path.exists(): raise RuntimeError('Selection already frozen')
    save(path,{'selected':selected,'frozen_at':datetime.now(timezone.utc).isoformat(),
        'fingerprint':protocol['fingerprint'],'configs':CONFIGS,'criteria':CRITERION,'dev_summaries':summaries,
        'dev_audits':audits,'reviews_sha256':{n:digest(ROOT/'results/dev'/n/'reviews.json') for n in CONFIGS}})
    print('Frozen:',selected)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run');r.add_argument('--split',choices=['dev','test'],required=True)
    r.add_argument('--config',choices=['all',*CONFIGS],default='all');r.add_argument('--workers',type=int,default=4)
    sub.add_parser('freeze')
    a=p.parse_args()
    if a.command=='freeze':freeze()
    else:execute(a.split,list(CONFIGS) if a.config=='all' else [a.config],a.workers)

if __name__=='__main__':main()
