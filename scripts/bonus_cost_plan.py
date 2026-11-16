"""Inspect saved usage/cache only. This command never imports an API provider."""
from pathlib import Path
import sys, hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save

def main():
    root=ROOT/'results/bonus';status=load(root/'status.json')
    selection=load(root/'selection.json') if (root/'selection.json').exists() else None
    name=selection['selected'] if selection else 'vision'
    config=(selection['protocol'] if selection else load(root/'protocol.json'))['configs'][name]
    cases=[q for q in load(ROOT/'benchmark/bonus_cases.json') if q['split']=='test']
    completed={}
    directory=root/'test'/name/'queries'
    if directory.exists():
        for path in directory.glob('*.json'):
            trace=load(path);completed[trace['query_id']]=trace['status']
    pending=[q for q in cases if q['id'] not in completed]
    cache=load(ROOT/'.bonus/embedding_cache.json')
    missing=sum(hashlib.sha256(('openai/text-embedding-3-small|1536|'+q['question']).encode()).hexdigest() not in cache for q in pending)
    reference=root/'dev'/name/'traces.json'
    if not load(reference):reference=ROOT/status['pilot']/'dev'/name/'traces.json'
    traces=load(reference)
    usage=[u for t in traces for u in t['usage'] if u.get('endpoint')=='chat/completions' and u.get('id')]
    known=[u for u in usage if 'cost' in u.get('usage',{})]
    measured=sum(u['usage'].get('cost',0) or 0 for u in known)
    prices=load(ROOT/'data/bonus/model_prices.json')
    dev_pending=len(status.get('pending_dev_queries',{}).get(name,[]))
    scenarios={}
    for model,rate in prices['models'].items():
        equivalent_cost=0
        for u in usage:
            tokens=u.get('usage',{});p=tokens.get('prompt_tokens',0);c=tokens.get('completion_tokens',0)
            long=p>rate.get('prompt_threshold',float('inf'))
            equivalent_cost+=(p*rate['long_input']+c*rate['long_output'] if long else p*rate['input']+c*rate['output'])/1e6
        scenarios[model]={'pending_dev_usd':equivalent_cost/len(traces)*dev_pending,
            'test_usd':equivalent_cost/len(traces)*len(pending),
            'dev_plus_test_usd':equivalent_cost/len(traces)*(dev_pending+len(pending))}
    estimate=scenarios.get(config['model'],{}).get('test_usd')
    plan={'api_requests_made_by_this_command':0,'selected':name,'model':config['model'],
      'test_total':len(cases),'saved_test_queries':len(completed),'pending_queries':len(pending),
      'saved_errors_not_automatically_retried':[cid for cid,status in completed.items() if status=='error'],
      'minimum_chat_requests_if_successful':2*len(pending),
      'maximum_successful_chat_requests_without_retries':(config['max_searches']+1)*len(pending),
      'original_query_embeddings_missing':missing,
      'pending_dev_queries':dev_pending,'price_checked_on':prices['checked_on'],
      'usage_reference':reference.relative_to(ROOT).as_posix(),
      'normalized_token_volume_price_scenarios':scenarios,
      'note_embeddings':'Rewrites may add queries. Reuse all existing document captions/vectors; never ingest again to run test.',
      'measured_dev_chat_requests':len(usage),'measured_dev_chat_cost_usd':measured,
      'estimated_test_chat_cost_usd_at_same_mean':estimate,
      'estimate_warning':'Hypothetical same token volume as saved reference dev. Different model tokenizers/image counting, reasoning, rewrites, retries and cache discounts change cost. Not a quote or spending cap. Query embeddings and credit-purchase fees excluded.',
      'zero_additional_api_option':'Run offline unit tests and submit the completed base lab; disclose bonus test pending, no bonus claimed.',
      'cheap_model_option':'New dev experiment required before test; retain original selection and results separately. No quality guarantee.',
      'do_not_repeat':['caption 232 pages','embed document again','completed dev queries','completed test queries'],
      'no_test_sampling_for_bonus':'A full published 30-question test must be evaluated to claim the bonus.'}
    save(root/'cost_plan.json',plan)
    print('OFFLINE: 0 API requests.')
    print('Pending test queries:',len(pending),'model:',config['model'])
    print('Successful chat calls without retry:',2*len(pending),'to',(config['max_searches']+1)*len(pending))
    print('Saved dev chat cost USD:',round(measured,8))
    print('Test extrapolation USD, not a cap:',None if estimate is None else round(estimate,4))

if __name__=='__main__':main()
