"""Offline checks for benchmark coverage and all-page multimodal indexing."""
import unittest
from collections import Counter
from unittest.mock import patch
from src.common import ROOT,load
from src.bonus import run_agent,CONFIGS,chat_payload

class BonusTests(unittest.TestCase):
    def test_haiku_request_disables_thinking_and_omits_rejected_sampling_fields(self):
        payload=chat_payload(CONFIGS['vision'],[{'role':'user','content':'q','kind':'internal'}],'required')
        self.assertEqual(payload['model'],'anthropic/claude-haiku-5.5')
        self.assertEqual(payload['reasoning'],{'enabled':False})
        self.assertNotIn('temperature',payload)
        self.assertNotIn('kind',payload['messages'][0])
        text=chat_payload(CONFIGS['text'],[{'role':'user','content':'q'}],'required')
        self.assertEqual(text['temperature'],0)
        self.assertNotIn('reasoning',text)

    def test_benchmark_minimums_and_evidence_locations(self):
        cases=load(ROOT/'benchmark/bonus_cases.json')
        self.assertEqual(len({c['id'] for c in cases}),48)
        test=Counter(c['group'] for c in cases if c['split']=='test')
        self.assertEqual(test,{'table':6,'diagram':5,'chart':5,'multi_hop':4,'text':4,'unanswerable':6})
        self.assertEqual(sum(c['split']=='dev' and c['answerable'] for c in cases),15)
        for c in cases:
            if c['answerable']:
                for g in c['gold']:
                    self.assertTrue(1<=g['page']<=232 and g['region'] and g['evidence'])
                    self.assertEqual(len(g['bbox_normalized']),4)
                if c['group']=='multi_hop':self.assertGreaterEqual(len({g['page'] for g in c['gold']}),2)

    def test_entire_document_indexed_including_nonbenchmark_pages(self):
        chunks=load(ROOT/'data/bonus/chunks.json')
        self.assertEqual({c['page'] for c in chunks},set(range(1,233)))
        self.assertEqual(load(ROOT/'data/bonus/coverage.json')['unprocessed_pages'],[])
        self.assertTrue(all(c['image_sha256'] and c['image'] for c in chunks))

    def test_bonus_retrieval_errors_return_error_not_fake_answer(self):
        class P:
            def __init__(self):self.usage=[]
            def request(self,*args):
                return {'choices':[{'message':{'tool_calls':[{'id':'s','function':{
                    'name':'search','arguments':'{"queries":["q"]}'}}]}}]}
        class Broken:
            def search(self,*args):raise ConnectionError('offline test')
        with patch('src.bonus.Provider',P):result=run_agent('q',Broken(),CONFIGS['text'])
        self.assertEqual(result['status'],'error')
        self.assertEqual(result['citations'],[])

    def test_bonus_requires_tool_output_and_normalizes_abstain(self):
        class P:
            choices=[]
            def __init__(self):self.usage=[];self.i=0
            def request(self,endpoint,payload):
                import json
                self.choices.append(payload['tool_choice']);self.i+=1
                for m in payload['messages']:assert 'kind' not in m
                name,args=('search',{'queries':['q']}) if self.i==1 else ('finish',{
                    'answer':'An unsupported assertion.','citations':[],'abstain':True})
                return {'choices':[{'message':{'tool_calls':[{'id':str(self.i),'function':{
                    'name':name,'arguments':json.dumps(args)}}]}}]}
        class I:
            def search(self,*args):return [{'id':'FPT2025:p001','page':1,'source':'source','text':'Evidence',
                'visuals':[],'score':1,'component_ranks':{},'image':'not-read','image_sha256':'test-hash'}]
        with patch('src.bonus.Provider',P):r=run_agent('q',I(),CONFIGS['text'])
        self.assertEqual(P.choices[1],'required')
        self.assertEqual(r['status'],'abstain')
        self.assertEqual(r['answer'],'Không đủ bằng chứng để trả lời.')

if __name__=='__main__':unittest.main()
