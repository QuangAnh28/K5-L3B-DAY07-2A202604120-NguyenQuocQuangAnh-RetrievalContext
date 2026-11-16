"""Verify existing results and generate the submission report; never assign labels."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.common import load,save,digest

def checks():
    frozen=load(ROOT/'results/selection.json')
    for key,path in [('benchmark_sha256','benchmark/cases.json'),('chunks_sha256','data/day6/chunks.json'),
                     ('agent_sha256','src/agent.py'),('retrieval_sha256','src/retrieval.py'),('experiments_sha256','src/experiments.py')]:
        assert frozen['fingerprint'][key]==digest(ROOT/path),path
    for name,sha in frozen['reviews_sha256'].items():
        assert sha==digest(ROOT/'results/dev'/name/'reviews.json')
    cases={q['id']:q for q in load(ROOT/'benchmark/cases.json')}
    checked=0
    for split in ['dev','test']:
        for directory in (ROOT/'results'/split).iterdir():
            if not directory.is_dir():continue
            traces=load(directory/'traces.json');reviews=load(directory/'reviews.json')
            by_id={r['query_id']:r for r in reviews};config=load(directory/'run.json')['config']
            assert len(traces)==(17 if split=='dev' else 7)
            for t in traces:
                assert t['status']!='error'
                assert t['searches']<=config['max_searches']
                assert len(t['context'])<=config['budget']
                for e in t['events']:
                    if e['event']=='search':
                        assert len(e['context'])<=config['budget']
                        assert len(e['results'])<=config['top_k']
                for cid in t['citations']:assert cid in t['context_ids'] and f'[{cid}]' in t['answer']
                assert by_id[t['query_id']]['trace_sha256']==digest(directory/'queries'/(t['query_id']+'.json'))
                assert by_id[t['query_id']]['benchmark_sha256']==digest(ROOT/'benchmark/cases.json')
                checked+=1
    source_checks=None
    pdf=ROOT/'.day6/starter/data/luat_thuong_mai_2005.pdf'
    if pdf.exists():
        from pypdf import PdfReader
        assert digest(pdf)==load(ROOT/'data/day6/manifest.json')['sha256']
        reader=PdfReader(str(pdf));assert len(reader.pages)==84
        compact=lambda text:re.sub(r'\s+','',text)
        for q in cases.values():
            for g in q.get('gold',[]):
                assert compact(g['evidence']) in compact(reader.pages[g['page']-1].extract_text()),q['id']
        source_checks={'pdf_pages':84,'sha256_matches':True,'all_gold_in_original_pdf':True,
                       'method':'Whitespace-insensitive character containment; semantic audit recorded separately.'}
    test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                        cwd=ROOT,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'})
    assert test.returncode==0,test.stderr
    count=int(re.search(r'Ran (\d+) tests',test.stderr).group(1))
    save(ROOT/'results/verification.json',{'passed':True,'unit_tests':count,'test_output':test.stdout+test.stderr,
         'checked_agent_traces':checked,'source_checks':source_checks,'frozen_hashes_match':True,
         'python':sys.version,'semantic_labels':'AI-assisted; student_confirmed=false'})

def costs():
    requests={}
    for path in (ROOT/'results').rglob('queries/*.json'):
        t=load(path)
        for u in t.get('model_usage',[]):
            if u.get('id'):requests[u['id']]=u
    for path in (ROOT/'results').rglob('embedding_usage.json'):
        for u in load(path):
            if u.get('id'):requests[u['id']]=u
    rows=list(requests.values())
    ledger={'requests':len(rows),'chat_requests':sum(u['endpoint']=='chat/completions' for u in rows),
        'embedding_requests':sum(u['endpoint']=='embeddings' for u in rows),
        'cost_usd':sum(u.get('usage',{}).get('cost',0) or 0 for u in rows),
        'missing_cost':sum('cost' not in u.get('usage',{}) for u in rows),
        'prompt_tokens':sum(u.get('usage',{}).get('prompt_tokens',0) for u in rows),
        'completion_tokens':sum(u.get('usage',{}).get('completion_tokens',0) for u in rows),
        'includes':'All Day 7 dev history, final dev and test, deduplicated by provider request ID. Excludes preexisting Day 6 usage.',
        'model_metadata_GET':'Read-only model availability probe has no token usage ledger.'}
    save(ROOT/'results/cost_summary.json',ledger)
    return ledger

def report(ledger):
    lines=['# Báo cáo Day 7 — Agentic RAG', '',
      'Họ tên: Nguyễn Quốc Quang Anh · MSSV: 2A202604120 · Lớp: L3B.', '',
      'Code, benchmark mới và nhãn được Codex hỗ trợ triển khai/đọc/chấm. Nhãn có `reviewer_kind: AI`, `student_confirmed: false`; không gọi đây là chấm mù, đánh giá độc lập hay xác nhận của học viên. Người triển khai đồng thời thiết kế benchmark và chấm kết quả nên có nguy cơ thiên lệch. Các kết quả dưới đây là số đo thực tế, không phải kết quả mock.', '',
      '## Dữ liệu và benchmark','',
      'Dùng lại ZIP Day 6: snapshot Luật Thương mại 36/2005/QH11 của Cục SHTT, 84 trang vật lý, 83 trang có nội dung được index, 245 chunk theo cấu hình C. Giữ ID/text/source/page/metadata/vector gốc. Nguồn, quyền sử dụng do Day 6 khai báo, ngày truy cập và SHA256 PDF ở `data/day6/manifest.json`; archive hash và chuyển đổi schema ở `data/day6/provenance.json`. PDF gốc đã kiểm tra SHA và evidence từng câu bằng đối chiếu ký tự sau bỏ khoảng trắng; giới hạn kiểm tra này không thay việc đọc ngữ nghĩa.', '',
      'Embedding OpenRouter `openai/text-embedding-3-small`, 1536 chiều; Qdrant local persistent collection C, cosine exact, qdrant-client 1.20.0. Model agent `openai/gpt-4.1-mini`, temperature=0; response lưu tên model/usage, không có revision cố định từ nhà cung cấp. API key được giữ local trong `.env`, không có trong bài nộp. `requirements-lock.txt` ghi môi trường chạy thực tế.', '',
      'Benchmark `benchmark/cases.json`: dev có 15 câu có đáp án từ Day 6 và 2 câu thiếu evidence; test mới có 5 câu có đáp án về các Điều 53, 60, 129, 223, 323 và 2 câu thiếu evidence. Loại toàn bộ q16–q20 của test Day 6 vì đã xem báo cáo/kết quả. Câu test mới dùng điều khác, được tạo trước lượt dev Day 7; vẫn là cùng tài liệu và có thể chung trang với dev, không coi là test ngoài miền hay hoàn toàn độc lập.', '',
      'Gold chứa nguồn, trang và quote; evidence thay thế được tính bằng OR. Khớp nguồn/trang/quote sau chuẩn hóa khoảng trắng; giữ cùng quy tắc giữa các phương pháp. Câu thiếu evidence là thông tin giao dịch/doanh thu/tài khoản/lịch công ty cụ thể không có trong snapshot luật, đã kiểm tra trên toàn text 84 trang và lưu `absence_check`; không kết luận vắng chỉ từ top-k. Nhóm này còn dễ do chứa tên/mốc thời gian không thuộc corpus; cần benchmark khó hơn về sau. Không đưa gold/expected answer/absence_reason vào agent hoặc retrieval.', '',
      '## Retrieval, context và giả thuyết','',
      '| Cấu hình | Phương pháp | top-k | Budget ký tự | Max search | Giả thuyết |',
      '|---|---|---:|---:|---:|---|',
      '| baseline | TF-IDF | 3 | 2400 | 1 | Baseline lexical từ starter |',
      '| dense | Qdrant C | 3 | 2400 | 1 | Ngữ nghĩa giúp câu hỏi khác cách diễn đạt |',
      '| hybrid — cải thiện 1 | Dense + TF-IDF, RRF | 3 | 2400 | 1 | Kết hợp tín hiệu ngữ nghĩa và từ khóa |',
      '| hybrid_context — cải thiện 2 | Cùng hybrid | 6 | 6000 | 3 | Thêm evidence qua k/budget và cho phép tìm tiếp |', '',
      'Hybrid lấy top-20 mỗi nhánh, RRF sum(1/(60+rank)); không cộng score khác thang đo. Cả ba cùng corpus C, metadata và query gốc. Filter chương chỉ dùng input Day 6 được nêu trong câu q05/q13; không lấy từ gold. Query đầu giữ nguyên câu hỏi, ghi riêng `model_query` nếu model đề xuất khác. Các search sau cho phép rewrite nhưng lượt thực tế đều dừng sau một search; chưa có bằng chứng thực nghiệm về lợi ích nhiều lượt hay multi-hop.', '',
      'Context khử trùng ID, ưu tiên kết quả mới, giữ source URL và trang; bỏ nguyên chunk nếu không vừa. Budget gồm ký tự nguồn/ID/separator, không tính system prompt và schema tool; không phải số token. Context tool trước được supersede để tránh nhân budget. Model dùng native function calling `search` rồi `finish`. Server kiểm tra ID có trong context và gắn citation có cấu trúc vào câu trả lời; giữ raw arguments trong events. Membership không bảo đảm semantic grounding.', '',
      '## Kết quả retrieval và context','',
      '| Cấu hình / split | Hit@1 | Evidence Hit@3 | Context Evidence Rate gốc | Context cuối | Median agent ms | Chi phí chat USD |',
      '|---|---|---|---|---|---:|---:|']
    def ratio(x):return f"{x['n']}/{x['N']} ({100*x['n']/x['N']:.1f}%)" if x['N'] else '0/0 (N/A)'
    for split in ['dev','test']:
        names=['baseline','dense','hybrid','hybrid_context'] if split=='dev' else ['baseline','hybrid_context']
        for name in names:
            s=load(ROOT/'results'/split/name/'summary.json')
            lines.append(f"| {name} / {split} | {ratio(s['hit1'])} | {ratio(s['hit3'])} | {ratio(s['original_context_evidence'])} | {ratio(s['final_context_evidence'])} | {s['median_ms']:.1f} | {s['model_cost_usd']:.8f} |")
    lines+=['', 'Hit@3 vẫn dùng cutoff 3 kể cả cấu hình k=6. Mẫu số là câu có đáp án chạy thành công, không gồm câu thiếu evidence; lượt cuối không có lỗi. Context metric dùng quote containment, audit ngữ nghĩa riêng ở bảng sau. Median gồm hai lần gọi chat và search trong agent, không gồm mở index/chạy ranking chẩn đoán trước đó. Query embedding có thể đã cache ở lượt trước, nên là phép đo warm; concurrency=4 và biến thiên API khiến số này không chứng minh tốc độ tuyệt đối. Đổi nhiều tham số trong cải thiện 2 nên không quy lợi ích cho riêng k, budget hay max_searches.', '',
      '## Agent và nhãn đọc đối chiếu','',
      '| Cấu hình / split | Tool use | Grounded 0/1/2 | Mean /2 | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm | Context 0/1/2 |',
      '|---|---|---|---:|---|---|---|---|---|']
    for split in ['dev','test']:
        names=['baseline','dense','hybrid','hybrid_context'] if split=='dev' else ['baseline','hybrid_context']
        for name in names:
            a=load(ROOT/'results'/split/name/'audit_summary.json');g=a['grounded_answer'];c=a['context_grades']
            lines.append(f"| {name} / {split} | {ratio(a['tool_use'])} | {g['0']}/{g['1']}/{g['2']} | {g['mean']:.3f} | {ratio(a['citation_validity'])} | {ratio(a['answer_citation_coverage'])} | {ratio(a['abstention'])} | {ratio(a['false_abstention'])} | {c['0']}/{c['1']}/{c['2']} |")
    frozen=load(ROOT/'results/selection.json')
    lines+=['', 'Đã đọc 17/17 dev mỗi cấu hình và 7/7 test mỗi cấu hình (gồm đủ 5 câu có đáp án và 2 câu thiếu evidence). Mọi lượt cuối gọi search đúng một lần; không có provider/vector-store error. Citation hợp lệ tính từng citation có trong context và hỗ trợ khẳng định; citation thừa/nhầm bị loại dù câu chính đúng. Grounded 0=sai/thiếu evidence, 1=đúng một phần/thiếu điều kiện, 2=đúng và đủ. Context 0=không có evidence cần thiết, 1=liên quan nhưng thiếu điều kiện/nguồn, 2=đủ evidence/nguồn. Mỗi nhãn có lý do và hash trace/benchmark trong `reviews.json`; công cụ audit chỉ tổng hợp nhãn.', '',
      '## Chọn cấu hình và phân tích lỗi dev','',
      f"Chốt `{frozen['selected']}` lúc {frozen['frozen_at']} theo protocol công bố trước: ưu tiên mean grounded answer trên dev, sau đó Context Evidence Rate query gốc, Hit@3, Hit@1, median latency thấp hơn, tên cấu hình. `results/selection.json` giữ hash benchmark/corpus/code và audit dev. Test chạy sau khi chốt; không sửa pipeline theo kết quả test.", '',
      '1. **Lỗi hiển thị citation ở lượt đầu:** model trả ID trong trường citations nhưng không gắn bracket vào answer. Validator cũ từ chối đáp án. Sửa renderer để chỉ gắn ID đã có trong context; giữ trace nguyên gốc. Lượt dev trước sửa lưu đầy đủ tại `results/history/round0-citation-rendering/`; cả 4 cấu hình đều có 15/15 câu answerable bị abstain. Lượt dev chạy lại cho phép đánh giá nội dung thực tế. Chi phí lượt lỗi vẫn được tính.', '',
      '2. **d7-q07 — rơi evidence khi đóng context:** baseline có evidence trong ranking nhưng context 2400 chỉ giữ địa điểm thanh toán/thời hạn giao nên từ chối nhầm. Cấu hình hybrid_context giữ được Điều 35 nên câu trả lời đúng ý, nhưng lại dẫn chunk Điều 42 về chứng từ. Chấm answer=1, citation=false; không tuyên bố vấn đề đã được giải quyết hoàn toàn.', '',
      '3. **d7-q11 — nhầm phạm vi cho thuê/mua bán:** baseline, dense và hybrid lấy Điều 274 trang 71 về cho thuê để nói về bên mua. Chấm 0 và citation=false. Cấu hình context lớn chứa Điều 57 trang 16 và dẫn đúng, nhưng bỏ điều kiện kể cả bên bán giữ chứng từ; chấm 1. Context đủ không đồng nghĩa trả lời đủ.', '',
      '4. **d7-q06/d7-q10 — hybrid chưa luôn tốt:** hybrid context nhỏ áp dụng hình thức chung Điều 24 cho hợp đồng quốc tế thay Điều 27, và trả lời giá hàng thừa/ngừng thanh toán thay thời hạn Điều 55. Context lớn giữ được evidence đúng nên cả hai đạt 2. RRF nhỏ giữ Hit@3 14/15 như TF-IDF và thấp hơn baseline ở một số câu; báo cả kết quả không cải thiện.', '',
      'Trên test, baseline có Hit@3=5/5 nhưng chỉ giữ context đủ 4/5; d7-t223 bị loại do budget nên từ chối nhầm. Cấu hình chọn giữ đủ cả hai khoản Điều 223, trả lời đủ với đúng citation. Test Hit@1 của cấu hình chọn chỉ 3/5, thấp hơn baseline 4/5; không đổi lựa chọn sau khi thấy test.', '',
      '## Ví dụ trình bày','']
    for name,cid in [('hybrid_context','d7-t53'),('hybrid_context','d7-u3'),('baseline','d7-t223')]:
        t=load(ROOT/'results/test'/name/'queries'/(cid+'.json'))
        lines += [f"**{cid} / {name}:** {t['question']}",'',t['answer'],'',f"Trace: `results/test/{name}/queries/{cid}.json`.",'']
    lines+=['## Chi phí, tái lập và giới hạn','',
      f"Tổng Day 7 gồm cả lượt dev lỗi và lượt cuối: {ledger['requests']} request thành công ({ledger['chat_requests']} chat, {ledger['embedding_requests']} embedding), {ledger['prompt_tokens']} prompt tokens, {ledger['completion_tokens']} completion tokens; cost từ provider usage **{ledger['cost_usd']:.8f} USD**, {ledger['missing_cost']} request thiếu trường cost. Không cộng lại chi phí Day 6. GET kiểm tra model không có token ledger. Chi phí có thể thay đổi khi chạy lại.",'',
      'Lệnh setup, nhập ZIP/khôi phục snapshot, unit tests, dev, audit, freeze, test và hỏi tự do ở `LAB_RUN.md`. Dữ liệu vector công khai được đóng gói tại `artifacts/day6-reuse.zip`, chỉ có collection C và cache cần thiết, không có API key. Code tái tạo bằng embedding thật ở `src/rebuild.py`; giữ vector Day 6 nếu dùng snapshot. Unit/integration checks, nguồn PDF và fingerprint ở `results/verification.json`; trace/review/summary từng cấu hình ở `results/`.', '',
      'Giới hạn: corpus một văn bản, lỗi khoảng trắng font PDF được giữ nguyên; chưa sửa extraction, chưa có đánh giá đa tài liệu, multi-hop, reranker hoặc prompt-injection red-team. Các nhãn do AI hỗ trợ cần học viên đọc đối chiếu trước khi nộp; chưa có xác nhận của học viên và không gọi là human audit. Tái chạy API có thể khác dù temperature=0; dependency/native ABI cần đúng môi trường. Không thực hiện bonus vì tài liệu chỉ 84 trang và không có benchmark bảng/ảnh/biểu đồ đáp ứng ADVANCED.md.', '',
      'Bài làm hiện ở repo local; chưa tạo remote cá nhân hay push/nộp link cho giảng viên. Học viên cần kiểm tra nhãn/nội dung, cấp quyền repo và nộp theo SUBMISSION.md. Không tự ước lượng điểm rubric.', '',
      'Tham khảo giao thức function calling: [OpenRouter official documentation](https://openrouter.ai/docs/guides/features/tool-calling). Yêu cầu bài học lấy từ GUIDE.md, BENCHMARK.md, RUBRIC.md và RULES.md trong repo.']
    path=ROOT/'report/individual/2A202604120_NguyenQuocQuangAnh.md'
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def vectors():
    meta=load(ROOT/'.day6/starter/results/qdrant/meta.json')
    meta['collections']={k:v for k,v in meta['collections'].items() if k=='C'}
    cache=load(ROOT/'.day6/starter/results/embedding_cache.json')
    texts=[c['text'] for c in load(ROOT/'data/day6/chunks.json')]+[q['question'] for q in load(ROOT/'benchmark/cases.json')]
    keys={hashlib.sha256(('openai/text-embedding-3-small|1536|'+text).encode()).hexdigest() for text in texts}
    selected={k:v for k,v in cache.items() if k in keys}
    target=ROOT/'artifacts/day6-reuse.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('starter/results/qdrant/meta.json',json.dumps(meta))
        z.write(ROOT/'.day6/starter/results/qdrant/collection/C/storage.sqlite','starter/results/qdrant/collection/C/storage.sqlite')
        z.writestr('starter/results/embedding_cache.json',json.dumps(selected))
    save(ROOT/'artifacts/day6-reuse-manifest.json',{'sha256':digest(target),'collection':'C',
        'chunk_vectors':245,'cached_texts':len(selected),'source':'Original Day 6 C persistent database and real embedding cache',
        'credentials_included':False})

if __name__=='__main__':
    checks();ledger=costs();vectors();report(ledger)
    print('Verified results, packaged original vectors and wrote report. Cost USD:',ledger['cost_usd'])
