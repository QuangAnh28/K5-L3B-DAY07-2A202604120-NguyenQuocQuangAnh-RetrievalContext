import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def normalized(text):
    return ' '.join(text.split())

def evidence_hit(chunk, gold):
    return any(chunk['source_id'] == g['source_id'] and chunk['page'] == g['page']
               and normalized(g['evidence']) in normalized(chunk['text']) for g in gold)
