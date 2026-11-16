"""OpenRouter HTTP client; never log credentials or provider error bodies."""
import os
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
from dotenv import load_dotenv
from .common import ROOT

load_dotenv(ROOT / '.env')

class Provider:
    def __init__(self):
        self.key = os.getenv('OPENROUTER_API_KEY', '').strip()
        self.usage = []

    def request(self, endpoint, payload):
        if not self.key:
            raise RuntimeError('Thiếu OPENROUTER_API_KEY trong .env; chỉ cần key khi thực sự gọi API')
        request = Request('https://openrouter.ai/api/v1/' + endpoint,
            data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + self.key,
            'Content-Type': 'application/json'}, method='POST')
        for attempt in range(3):
            started = time.perf_counter()
            try:
                with urlopen(request, timeout=90) as response:
                    result = json.load(response)
                if 'error' in result:
                    raise RuntimeError('Provider response contains an error')
                self.usage.append({'id': result.get('id'), 'model': result.get('model'),
                    'endpoint': endpoint, 'usage': result.get('usage', {}),
                    'elapsed_ms': (time.perf_counter()-started)*1000, 'attempt': attempt+1})
                return result
            except HTTPError as exc:
                self.usage.append({'endpoint': endpoint, 'error': 'HTTP', 'status': exc.code,
                                   'attempt': attempt+1})
                if exc.code < 500 and exc.code != 429 or attempt == 2:
                    raise RuntimeError(f'OpenRouter HTTP {exc.code}') from None
            except (URLError, TimeoutError):
                self.usage.append({'endpoint': endpoint, 'error': 'network', 'attempt': attempt+1})
                if attempt == 2:
                    raise RuntimeError('OpenRouter network/timeout error') from None
            time.sleep(2**attempt)

    def embedding(self, text):
        model = os.getenv('EMBEDDING_MODEL', 'openai/text-embedding-3-small')
        if model != 'openai/text-embedding-3-small':
            raise ValueError('Day 6 index requires openai/text-embedding-3-small, 1536 dimensions')
        rows = self.request('embeddings', {'model': model, 'input': [text], 'dimensions': 1536})['data']
        vector = rows[0]['embedding']
        if len(vector) != 1536:
            raise ValueError('Embedding dimension mismatch')
        return vector

    def chat(self, messages, tools, choice):
        return self.request('chat/completions', {'model': os.getenv('AGENT_MODEL','openai/gpt-4.1-mini'),
            'messages': messages, 'tools': tools, 'tool_choice': choice,
            'temperature': 0, 'max_tokens': 1300, 'parallel_tool_calls': False})
