"""Interactive single-question execution; no benchmark gold is loaded."""
import argparse
from .common import ROOT, load, save
from .experiments import CONFIGS
from .retrieval import Retrieval
from .agent import run

def main():
    p=argparse.ArgumentParser();p.add_argument('question')
    p.add_argument('--config',choices=list(CONFIGS),default='hybrid_context')
    p.add_argument('--output',default='results/interactive/last.json')
    a=p.parse_args();retrieval=Retrieval()
    try:
        result=run(a.question,retrieval,CONFIGS[a.config])
        result['embedding_usage']=retrieval.provider.usage
        save(ROOT/a.output,result)
        print(result['answer'] if result['status']!='error' else result['error'])
        print('Trace:',a.output)
    finally:retrieval.close()

if __name__=='__main__':main()
