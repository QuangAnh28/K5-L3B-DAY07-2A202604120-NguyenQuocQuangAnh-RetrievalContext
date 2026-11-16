"""Restore shared vector artifacts offline, or recreate C using real embeddings."""
import argparse
import hashlib
import uuid
import zipfile
from qdrant_client import QdrantClient, models
from .common import ROOT, load, save
from .provider import Provider

def rebuild(snapshot=None):
    if snapshot:
        allowed=['starter/results/qdrant/meta.json',
                 'starter/results/qdrant/collection/C/storage.sqlite',
                 'starter/results/embedding_cache.json']
        with zipfile.ZipFile(snapshot) as z:
            if set(z.namelist())!=set(allowed):raise ValueError('Unexpected snapshot entries')
            for name in allowed:
                p=ROOT/'.day6'/name
                if p.exists():raise RuntimeError('Local store/cache already exists; use a fresh checkout to restore')
            for name in allowed:
                p=ROOT/'.day6'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        print('Restored original Day 6 C vector store and compatible embedding cache offline.')
        return
    chunks=load(ROOT/'data/day6/chunks.json'); provider=Provider()
    cache_path=ROOT/'.day6/starter/results/embedding_cache.json'
    cache=load(cache_path) if cache_path.exists() else {}
    def key(text):return hashlib.sha256(('openai/text-embedding-3-small|1536|'+text).encode()).hexdigest()
    missing=[c['text'] for c in chunks if key(c['text']) not in cache]
    for start in range(0,len(missing),64):
        batch=missing[start:start+64]
        result=provider.request('embeddings',{'model':'openai/text-embedding-3-small','dimensions':1536,'input':batch})
        rows=sorted(result['data'],key=lambda r:r['index'])
        if len(rows)!=len(batch) or any(len(r['embedding'])!=1536 for r in rows):raise ValueError('Invalid embedding response')
        cache.update({key(text):r['embedding'] for text,r in zip(batch,rows)})
        save(cache_path,cache);save(ROOT/'results/rebuild_embedding_usage.json',provider.usage)
        print('Embedded',min(start+64,len(missing)),'/',len(missing),flush=True)
    client=QdrantClient(path=str(ROOT/'.day6/starter/results/qdrant'))
    try:
        if client.collection_exists('C'):raise RuntimeError('C exists; refusing to overwrite')
        client.create_collection('C',vectors_config=models.VectorParams(size=1536,distance=models.Distance.COSINE))
        points=[models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL,c['id'])),vector=cache[key(c['text'])],
                  payload={**c['metadata'],'chunk_id':c['id'],'document_id':c['source_id'],
                           'source':c['source'],'page':c['page'],'text':c['text']}) for c in chunks]
        client.upsert('C',points=points,wait=True)
        print('Recreated C:',client.count('C',exact=True).count)
    finally:client.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',type=str)
    a=p.parse_args();rebuild(a.snapshot)
