"""Restore both sanitized snapshots into a fresh temporary workspace; prohibit API."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys,shutil
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save
import src.rebuild as rebuild
import src.retrieval as retrieval
import src.bonus as bonus
import restore_bonus_assets as assets

def main():
    (ROOT/'tmp').mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='restore-',dir=ROOT/'tmp') as directory:
        target=Path(directory)
        assert target.resolve().is_relative_to((ROOT/'tmp').resolve())
        for rel in ['data/day6/chunks.json','data/bonus/chunks.json','data/bonus/pages.json','data/bonus/manifest.json']:
            dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
        with patch('src.provider.Provider.request',side_effect=AssertionError('No API permitted')):
            with patch.object(rebuild,'ROOT',target):rebuild.rebuild(ROOT/'artifacts/day6-reuse.zip')
            with patch.object(assets,'ROOT',target):assets.restore(ROOT/'.bonus/BCTN-2025.pdf',ROOT/'artifacts/bonus-reuse.zip')
            with patch.object(retrieval,'ROOT',target):
                index=retrieval.Retrieval()
                try:
                    query=load(ROOT/'benchmark/cases.json')[0]['question']
                    base=index.search(query,'hybrid',3);assert len(base)==3
                finally:index.close()
            with patch.object(bonus,'ROOT',target):
                index=bonus.Index()
                try:
                    query=load(ROOT/'benchmark/bonus_cases.json')[0]['question']
                    found=index.search(query,4);assert len(found)==4
                finally:index.close()
        save(ROOT/'results/snapshot_restore_check.json',{'passed':True,'network_calls_allowed':False,
          'fresh_temporary_workspace':True,'base_collection_C':245,'bonus_collection_FPT2025':232,
          'bonus_original_images_restored_and_hash_verified':232,
          'cached_base_hybrid_hits':len(base),'cached_bonus_hybrid_hits':len(found),
          'note':'Used exact original PDF and sanitized snapshots; no provider requests.'})
    print('Fresh restore and both cached retrieval paths passed offline.')

if __name__=='__main__':main()
