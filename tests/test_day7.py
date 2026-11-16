"""Offline regression checks and integration with real cached Day 6 vectors."""
import unittest
from unittest.mock import patch
from src.common import ROOT, load, normalized
from src.agent import run
from src.experiments import CONFIGS

CHUNK={'id':'c1','source_id':'doc','source':'local-source','page':1,'text':'Bằng chứng gốc.','metadata':{},'score':1.0}

class FakeProvider:
    actions=[]
    def __init__(self):self.usage=[];self.pos=0;self.messages=[]
    def chat(self,messages,tools,choice):
        import json
        name,args=self.actions[self.pos];self.pos+=1
        self.messages.append(messages)
        return {'id':'offline-test','choices':[{'message':{'role':'assistant','content':None,
            'tool_calls':[{'id':str(self.pos),'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}}]}

class FakeRetrieval:
    def __init__(self):self.queries=[]
    def search(self,query,method,top_k,filters):self.queries.append(query);return [CHUNK]

class Day7Tests(unittest.TestCase):
    def test_real_day6_schema_and_benchmark(self):
        if not (ROOT/'data/day6/chunks.json').exists():self.skipTest('Import Day 6 first')
        chunks=load(ROOT/'data/day6/chunks.json');cases=load(ROOT/'benchmark/cases.json')
        self.assertEqual(len({c['id'] for c in chunks}),245)
        self.assertEqual(len({q['id'] for q in cases}),24)
        for split,yes,no in [('dev',15,2),('test',5,2)]:
            self.assertEqual(sum(q['split']==split and q['answerable'] for q in cases),yes)
            self.assertEqual(sum(q['split']==split and not q['answerable'] for q in cases),no)
        for q in cases:
            if q['answerable']:
                for g in q['gold']:
                    self.assertTrue(any(c['page']==g['page'] and c['source_id']==g['source_id'] and normalized(g['evidence']) in normalized(c['text']) for c in chunks),q['id'])

    def test_cached_dense_and_rrf_use_real_store(self):
        if not (ROOT/'.day6/starter/results/qdrant').exists():self.skipTest('Import Day 6 first')
        from src.retrieval import Retrieval
        r=Retrieval()
        try:
            q=load(ROOT/'benchmark/cases.json')[0]['question']
            with patch.object(r.provider,'embedding',side_effect=AssertionError('Network forbidden in offline test')):
                dense=r.search(q,'dense',3);hybrid=r.search(q,'hybrid',3);lexical=r.search(q,'tfidf',3)
            self.assertEqual([len(x) for x in (dense,hybrid,lexical)],[3,3,3])
            self.assertEqual(hybrid[0]['page'],4)
            self.assertAlmostEqual(hybrid[0]['score'],sum(1/(60+rank) for rank in hybrid[0]['component_ranks'].values()))
            for rows in (dense,hybrid,lexical):self.assertEqual(len({c['id'] for c in rows}),len(rows))
        finally:r.close()

    @patch('src.agent.Provider',FakeProvider)
    def test_structured_citations_are_rendered_after_membership_check(self):
        FakeProvider.actions=[('search',{'query':'q'}),('finish',{'answer':'Bằng chứng gốc.','citations':['c1'],'abstain':False})]
        r=run('q',FakeRetrieval(),CONFIGS['baseline'])
        self.assertEqual(r['status'],'answered');self.assertEqual(r['answer'],'Bằng chứng gốc. [c1]')
        self.assertNotIn('[c1]',r['events'][-2]['message']['tool_calls'][0]['function']['arguments'])

    @patch('src.agent.Provider',FakeProvider)
    def test_native_tools_force_original_query_and_reject_fabricated_citation(self):
        FakeProvider.actions=[('search',{'query':'model rewrite'}),('finish',{'answer':'Nội dung [fake]','citations':['fake'],'abstain':False})]
        retrieval=FakeRetrieval();r=run('original',retrieval,CONFIGS['baseline'])
        self.assertEqual(retrieval.queries,['original'])
        self.assertEqual(r['status'],'abstain')
        self.assertEqual(r['events'][1]['model_query'],'model rewrite')

    @patch('src.agent.Provider',FakeProvider)
    def test_real_retriever_failure_is_reported(self):
        FakeProvider.actions=[('search',{'query':'q'})]
        with patch.object(FakeRetrieval,'search',side_effect=ConnectionError('offline failure')):
            result=run('q',FakeRetrieval(),CONFIGS['baseline'])
        self.assertEqual(result['status'],'error')
        self.assertEqual(result['error']['type'],'ConnectionError')

if __name__=='__main__':unittest.main()
