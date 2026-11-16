"""Validate and summarize explicitly recorded review labels; never generate grades."""
import argparse
import sys
from collections import Counter
from .common import ROOT, load, save, digest
sys.path.insert(0,str(ROOT/'starter'))
from agent_metrics import aggregate

def summarize(split, name):
    directory=ROOT/'results'/split/name
    cases=[c for c in load(ROOT/'benchmark/cases.json') if c['split']==split]
    traces=load(directory/'traces.json')
    reviews=load(directory/'reviews.json')
    by_id={t['query_id']:t for t in traces}
    for review in reviews:
        cid=review['query_id'];trace=by_id[cid]
        if not review.get('reason') or review.get('reviewer_kind') not in ('AI','human'):
            raise ValueError('Missing review provenance/reason')
        if review['trace_sha256']!=digest(directory/'queries'/(cid+'.json')):
            raise ValueError('Trace changed after review: '+cid)
        if review['benchmark_sha256']!=digest(ROOT/'benchmark/cases.json'):
            raise ValueError('Benchmark changed after review')
        if trace['answerable'] and review.get('context_grade') not in (0,1,2):
            raise ValueError('Missing context grade')
        for cid,supported in zip(trace['citations'],review['citation_support']):
            if supported and cid not in trace['context_ids']:
                raise ValueError('Supported citation is outside final context')
    report=aggregate(cases,traces,reviews)
    context=Counter(str(r['context_grade']) for r in reviews if 'context_grade' in r)
    report.update(context_grades={str(i):context[str(i)] for i in (0,1,2)},
                  review_note='AI-assisted semantic audit; not an independent human judgment or student confirmation.')
    save(directory/'audit_summary.json',report)
    print(split,name,report['grounded_answer'],report['abstention'])

def packet(split,name):
    directory=ROOT/'results'/split/name
    cases={c['id']:c for c in load(ROOT/'benchmark/cases.json')}
    for t in load(directory/'traces.json'):
        q=cases[t['query_id']]
        print('\nQUERY',q['id'],q['question'])
        print('EXPECTED',q.get('expected_answer',q.get('absence_reason')))
        print('STATUS',t['status'],'CONTEXT HIT',t['final_context_hit'],'ANSWER',t['answer'])
        print('FINAL CONTEXT',t['context'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--split',required=True,choices=['dev','test'])
    p.add_argument('--config',required=True);p.add_argument('--packet',action='store_true')
    a=p.parse_args()
    if a.packet:packet(a.split,a.config)
    else:summarize(a.split,a.config)
