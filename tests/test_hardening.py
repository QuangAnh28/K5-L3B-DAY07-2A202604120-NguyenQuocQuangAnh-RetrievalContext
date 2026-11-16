"""Regression tests for issues reproduced during the rubric review."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.common import ROOT,load,save
from src.provider import Provider
from src import agent,experiments

class HardeningTests(unittest.TestCase):
    def test_missing_key_is_required_only_at_request_time(self):
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':''}):
            provider=Provider()
            self.assertEqual(provider.usage,[])
            with self.assertRaisesRegex(RuntimeError,'OPENROUTER_API_KEY'):
                provider.request('chat/completions',{})

    def test_abstain_cannot_return_unverified_assertion(self):
        from test_day7 import FakeProvider,FakeRetrieval
        FakeProvider.actions=[('search',{'query':'q'}),('finish',{
            'answer':'Khách hàng đã được hoàn 100 triệu đồng.','citations':[],'abstain':True})]
        with patch.object(agent,'Provider',FakeProvider):result=agent.run('q',FakeRetrieval(),experiments.CONFIGS['baseline'])
        self.assertEqual(result['status'],'abstain')
        self.assertEqual(result['answer'],'Không đủ bằng chứng để trả lời.')
        self.assertIn('100',result['events'][-2]['message']['tool_calls'][0]['function']['arguments'])

    def test_initial_retrieval_errors_are_persisted_for_each_query(self):
        class Broken:
            def __init__(self):self.provider=type('Usage',(),{'usage':[]})()
            def search(self,*args):raise ConnectionError('offline failure')
            def close(self):pass
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for rel in ['src/agent.py','src/retrieval.py','src/provider.py','src/experiments.py','data/day6/chunks.json']:
                dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
            cases=[{'id':'e1','split':'dev','question':'q1','answerable':True},
                   {'id':'e2','split':'dev','question':'q2','answerable':False}]
            save(root/'benchmark/cases.json',cases)
            with patch.object(experiments,'ROOT',root),patch.object(experiments,'Retrieval',Broken):
                experiments.execute('dev',['baseline'],workers=1)
            traces=load(root/'results/dev/baseline/traces.json')
            self.assertEqual(len(traces),2)
            self.assertTrue(all(t['status']=='error' and t['error']['stage']=='original_retrieval' for t in traces))
            self.assertEqual(load(root/'results/dev/baseline/summary.json')['errors'],2)

    def test_real_cached_store_needs_no_provider_credential(self):
        if not (ROOT/'.day6/starter/results/qdrant').exists():self.skipTest('Restore snapshot first')
        from src.retrieval import Retrieval
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':''}):
            r=Retrieval()
            try:
                with patch.object(r.provider,'request',side_effect=AssertionError('Network forbidden')):
                    rows=r.search(load(ROOT/'benchmark/cases.json')[0]['question'],'dense',3)
                self.assertEqual(len(rows),3)
            finally:r.close()

if __name__=='__main__':unittest.main()
