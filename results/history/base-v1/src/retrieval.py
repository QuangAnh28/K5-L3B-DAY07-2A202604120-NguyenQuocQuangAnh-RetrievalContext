"""Three retrieval methods over the same, unchanged Day 6 C collection."""
import hashlib
import threading
from collections import defaultdict
from qdrant_client import QdrantClient, models
from starter.baseline import TfidfIndex
from .common import ROOT, load, save
from .provider import Provider

class Retrieval:
    def __init__(self):
        self.chunks = load(ROOT/'data/day6/chunks.json')
        self.lexical = TfidfIndex(self.chunks)
        self.by_id = {c['id']: c for c in self.chunks}
        self.client = QdrantClient(path=str(ROOT/'.day6/starter/results/qdrant'))
        params = self.client.get_collection('C').config.params.vectors
        if params.size != 1536 or params.distance != models.Distance.COSINE:
            raise ValueError('Day 6 collection configuration mismatch')
        if self.client.count('C', exact=True).count != len(self.chunks):
            raise ValueError('Day 6 chunk count mismatch')
        points, _ = self.client.scroll('C', limit=len(self.chunks), with_payload=True)
        if {p.payload['chunk_id']: p.payload['text'] for p in points} != {c['id']:c['text'] for c in self.chunks}:
            raise ValueError('Day 6 Qdrant payloads differ from corpus')
        self.cache_path = ROOT/'.day6/starter/results/embedding_cache.json'
        self.cache = load(self.cache_path)
        self.lock = threading.RLock()
        self.provider = Provider()

    def vector(self, query):
        key = hashlib.sha256(('openai/text-embedding-3-small|1536|'+query).encode()).hexdigest()
        with self.lock:
            if key not in self.cache:
                self.cache[key] = self.provider.embedding(query)
                save(self.cache_path, self.cache)
            return self.cache[key]

    def search(self, query, method, top_k=3, filters=None):
        if not isinstance(query,str) or not query.strip() or top_k < 1:
            raise ValueError('Invalid query/top_k')
        filters = filters or {}
        if set(filters)-{'chapter','year','section'}:
            raise ValueError('Unsupported filter')
        lexical = [c for c in self.lexical.search(query, len(self.chunks))
                   if all(c['metadata'].get(k)==v for k,v in filters.items())]
        if method == 'tfidf':
            return lexical[:top_k]
        if method not in ('dense','hybrid'):
            raise ValueError('Unknown retrieval method')
        vector = self.vector(query)
        filt = models.Filter(must=[models.FieldCondition(key=k,match=models.MatchValue(value=v))
                                   for k,v in filters.items()]) if filters else None
        with self.lock:
            points = self.client.query_points('C', query=vector, query_filter=filt,
                                               limit=max(top_k,20) if method=='hybrid' else top_k).points
        dense = [{**self.by_id[p.payload['chunk_id']], 'score': p.score, 'strategy':'dense'} for p in points]
        if method == 'dense':
            return dense
        scores = defaultdict(float)
        ranks = defaultdict(dict)
        for name, rows in [('dense',dense), ('tfidf',lexical[:20])]:
            for rank,c in enumerate(rows,1):
                scores[c['id']] += 1/(60+rank)
                ranks[c['id']][name] = rank
        ids = sorted(scores,key=lambda cid:(-scores[cid],cid))[:top_k]
        return [{**self.by_id[cid], 'score':scores[cid], 'strategy':'hybrid',
                 'component_ranks':ranks[cid]} for cid in ids]

    def close(self):
        self.client.close()
