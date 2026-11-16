"""Run a small resumable batch with the unchanged experiment protocol.

Cost stop is checked between questions, not a hard cap on the current request.
Existing query files, including failures, are never retried automatically.
"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save,digest
from src.bonus import CONFIGS,Index,run_agent,fingerprint

def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['dev','test'],default='dev')
    p.add_argument('--config',choices=list(CONFIGS),default='vision')
    p.add_argument('--count',type=int,default=3);p.add_argument('--ids',nargs='+')
    p.add_argument('--stop-after-usd',type=float,default=0.10)
    a=p.parse_args()
    if a.count<1 or a.stop_after_usd<=0:p.error('Positive batch count and cost stop required')
    root=ROOT/'results/bonus';protocol=load(root/'protocol.json')
    if protocol['fingerprint']!=fingerprint() or protocol['configs']!=CONFIGS:raise ValueError('Protocol changed')
    if a.split=='test':
        selection=load(root/'selection.json')
        if selection['protocol']!=protocol:raise ValueError('Selection protocol mismatch')
        if a.config!=selection['selected']:raise ValueError('Only the frozen selected configuration may run test')
    cases=[q for q in load(ROOT/'benchmark/bonus_cases.json') if q['split']==a.split]
    directory=root/a.split/a.config
    pending=[q for q in cases if not (directory/'queries'/(q['id']+'.json')).exists()]
    if a.ids:
        if len(set(a.ids))!=len(a.ids) or set(a.ids)-{q['id'] for q in cases}:p.error('Invalid/duplicate IDs')
        pending=[q for cid in a.ids for q in pending if q['id']==cid]
    else:pending=pending[:a.count]
    if not pending:print('No pending queries in this batch; no API requests.');return
    save(directory/'run.json',protocol)
    index=Index();prior=load(root/'query_embedding_usage.json') if (root/'query_embedding_usage.json').exists() else []
    rows=[];chat_cost=0;failed=False;start=datetime.now(timezone.utc).isoformat()
    try:
        for q in pending:
            # Agent receives only the question, corpus index and frozen config. Never gold.
            result=run_agent(q['question'],index,CONFIGS[a.config])
            result.update(query_id=q['id'],question=q['question'],split=a.split,config=a.config)
            save(directory/'queries'/(q['id']+'.json'),result);rows.append(result)
            chat_cost+=sum(u.get('usage',{}).get('cost',0) or 0 for u in result['usage'] if u.get('id'))
            embed_cost=sum(u.get('usage',{}).get('cost',0) or 0 for u in index.provider.usage if u.get('id'))
            print(q['id'],result['status'],'batch cost USD',round(chat_cost+embed_cost,8),flush=True)
            if result['status']=='error':failed=True;break
            if chat_cost+embed_cost>=a.stop_after_usd:break
    finally:
        save(root/'query_embedding_usage.json',prior+index.provider.usage);index.close()
        completed=[load(path) for path in (directory/'queries').glob('*.json')]
        save(directory/'traces.json',sorted(completed,key=lambda t:t['query_id']))
        status=load(root/'status.json');status['network_calls_stopped']=True
        if a.split=='dev':
            status['pending_dev_queries'][a.config]=[q['id'] for q in cases if not (directory/'queries'/(q['id']+'.json')).exists()]
            status['reason']='New model dev batch attempted; inspect raw outputs and usage before proceeding.'
        else:
            status.update(stage='test_in_progress',bonus_test_run=True,
                test_completed_queries=len(completed),test_total_queries=len(cases),
                reason='Frozen test batch saved; individual source reviews and full audit pending.')
        save(root/'status.json',status)
        requests=[u for t in rows for u in t['usage'] if u.get('id')]+[u for u in index.provider.usage if u.get('id')]
        batch={'started_at':start,'finished_at':datetime.now(timezone.utc).isoformat(),'split':a.split,
          'config':a.config,'model':CONFIGS[a.config]['model'],'query_ids':[r['query_id'] for r in rows],
          'statuses':{r['query_id']:r['status'] for r in rows},'provider_reported_cost_usd':sum(u.get('usage',{}).get('cost',0) or 0 for u in requests),
          'successful_request_ids':[u['id'] for u in requests],
          'trace_hashes':{r['query_id']:digest(directory/'queries'/(r['query_id']+'.json')) for r in rows},
          'unknown_failure_cost':any(u.get('error') for t in rows for u in t['usage']),
          'stopped_on_error':failed,'between_question_cost_stop_usd':a.stop_after_usd,
          'cost_stop_note':'Checked after each question; current question can exceed this amount.'}
        folder=root/'batches';number=len(list(folder.glob('*.json')))+1
        save(folder/f'{number:04}.json',batch)
        print('BATCH',number,'queries',len(rows),'USD',batch['provider_reported_cost_usd'],flush=True)
    if failed:raise SystemExit(2)

if __name__=='__main__':main()
