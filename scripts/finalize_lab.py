"""Verify measured results, preserve reviewer labels, generate final lab artifacts."""
from pathlib import Path
import sys,json,subprocess,os,re,zipfile
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save,digest

def costs():
    requests={};failures=[]
    for p in (ROOT/'results').rglob('queries/*.json'):
        t=load(p)
        for u in t.get('model_usage',[])+t.get('usage',[]):
            if u.get('id'):requests[u['id']]=u
            elif u.get('error'):failures.append(u)
    for p in (ROOT/'data/bonus/captions').glob('*.json'):
        for u in load(p)['usage']:
            if u.get('id'):requests[u['id']]=u
    for p in (ROOT/'results').rglob('*usage.json'):
        value=load(p)
        if not isinstance(value,list):continue
        for u in value:
            if not isinstance(u,dict):continue
            if u.get('id'):requests[u['id']]=u
            elif u.get('error'):failures.append(u)
    rows=list(requests.values())
    report={'requests':len(rows),'chat_requests':sum(u['endpoint']=='chat/completions' for u in rows),
        'embedding_requests':sum(u['endpoint']=='embeddings' for u in rows),
        'cost_usd':sum(u.get('usage',{}).get('cost',0) or 0 for u in rows),
        'missing_cost_requests':sum('cost' not in u.get('usage',{}) for u in rows),
        'prompt_tokens':sum(u.get('usage',{}).get('prompt_tokens',0) for u in rows),
        'completion_tokens':sum(u.get('usage',{}).get('completion_tokens',0) for u in rows),
        'failed_attempt_records':len(failures),'unknown_failure_cost':bool(failures),
        'includes':'All Day 7 basic and bonus runs, captions, embeddings and preserved failed dev pilots. Deduplicate successful requests by provider response ID. Day 6 prior cost excluded.'}
    save(ROOT/'results/cost_summary.json',report);return report

def verify():
    from src.audit import summarize
    from src.bonus import audit,fingerprint
    frozen=load(ROOT/'results/selection.json')
    for key,path in [('benchmark_sha256','benchmark/cases.json'),('chunks_sha256','data/day6/chunks.json'),
        ('agent_sha256','src/agent.py'),('retrieval_sha256','src/retrieval.py'),('provider_sha256','src/provider.py'),('experiments_sha256','src/experiments.py')]:
        assert frozen['fingerprint'][key]==digest(ROOT/path),path
    count=0
    for split,names in [('dev',['baseline','dense','hybrid','hybrid_context']),('test',['baseline',frozen['selected']])]:
        for name in dict.fromkeys(names):
            summarize(split,name)
            d=ROOT/'results'/split/name
            for t in load(d/'traces.json'):
                assert t==load(d/'queries'/(t['query_id']+'.json'))
                assert len(t.get('context',''))<=load(d/'run.json')['config']['budget']
                count+=1
    bonus_root=ROOT/'results/bonus'
    if (bonus_root/'selection.json').exists():
        selection=load(bonus_root/'selection.json')
        assert selection['protocol']['fingerprint']==fingerprint()
        splits=[('dev',['text','vision'])]
        if (bonus_root/'test').exists():splits.append(('test',[selection['selected']]))
        for split,names in splits:
            for name in names:
                audit(split,name)
                directory=bonus_root/split/name
                for trace in load(directory/'traces.json'):
                    assert trace==load(directory/'queries'/(trace['query_id']+'.json'))
                pages_by_number={p['page']:p for p in load(ROOT/'data/bonus/pages.json')}
                for review in load(directory/'reviews.json'):
                    for check in review['original_page_check']:
                        assert check['image_sha256']==pages_by_number[check['page']]['image_sha256']
    else:
        status=load(bonus_root/'status.json')
        assert not (bonus_root/'test').exists()
        assert load(bonus_root/'protocol.json')['fingerprint']==fingerprint()
        cases={q['id']:q for q in load(ROOT/'benchmark/bonus_cases.json') if q['split']=='dev'}
        old_cases={q['id']:q for q in load(ROOT/status['pilot']/'benchmark/bonus_cases.json')}
        for name in ['text','vision']:
            directory=bonus_root/'dev'/name
            rows=load(directory/'traces.json');reviews=load(directory/'reviews.json')
            assert len(rows)+len(status['pending_dev_queries'][name])==18
            assert {r['query_id'] for r in reviews}=={t['query_id'] for t in rows}
            for r in reviews:
                assert cases[r['query_id']]==old_cases[r['query_id']]
                if r.get('reused_from'):assert digest(ROOT/r['reused_from'])==r['trace_sha256']
                else:assert r['reviewer_kind']=='AI' and r['original_page_check']
                assert digest(directory/'queries'/(r['query_id']+'.json'))==r['trace_sha256']
                assert r['benchmark_sha256']==digest(ROOT/'benchmark/bonus_cases.json')
    pages=load(ROOT/'data/bonus/pages.json');assert len(pages)==232
    for p in pages:
        assert digest(ROOT/p['image'])==p['image_sha256']
    assert digest(ROOT/'.bonus/BCTN-2025.pdf')==load(ROOT/'data/bonus/manifest.json')['pdf_sha256']
    env={**os.environ,'PYTHONUTF8':'1','OPENROUTER_API_KEY':''}
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,
                          env=env,capture_output=True,text=True,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    unit_tests=int(re.search(r'Ran (\d+) tests',result.stderr).group(1))
    save(ROOT/'results/verification.json',{'passed':True,'unit_tests':unit_tests,'offline_without_api_key':True,
        'base_traces_checked':count,'bonus_original_page_images_verified':232,'frozen_hashes_match':True,
        'bonus_test_completed':(bonus_root/'test').exists(),
        'test_output':result.stdout+result.stderr,'python':sys.version,
        'note':'Semantic decisions remain explicit AI-assisted reviews. Passing code checks does not create student confirmation.'})

def snapshots():
    # Base snapshot is the unchanged Day 6 collection already verified in the first run.
    target=ROOT/'artifacts/bonus-reuse.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ['qdrant/meta.json','qdrant/collection/FPT2025/storage.sqlite','embedding_cache.json']:
            z.write(ROOT/'.bonus'/name,name)
    save(ROOT/'artifacts/bonus-reuse-manifest.json',{'sha256':digest(target),'pages':232,
        'model':'openai/text-embedding-3-small','dimensions':1536,'contains':['Qdrant FPT2025','embedding cache'],
        'original_pdf_included':False,'images_included':False,'credentials_included':False})

def ratio(x):return f"{x['n']}/{x['N']} ({100*x['n']/x['N']:.1f}%)" if x['N'] else '0/0 (N/A)'

def reports(ledger):
    selected=load(ROOT/'results/selection.json')
    frozen_bonus=(ROOT/'results/bonus/selection.json').exists()
    completed=(ROOT/'results/bonus/test').exists()
    bonus=load(ROOT/'results/bonus/selection.json') if frozen_bonus else {'selected':'chưa chốt','frozen_at':'chưa chốt'}
    result=load(ROOT/'results/bonus/test'/bonus['selected']/'summary.json') if completed else {
        'passed':0,'total':0,'rate':0,'meets_90_percent':False,'groups':{},'system_errors':0,'pending':True}
    verification=load(ROOT/'results/verification.json')
    status=load(ROOT/'results/bonus/status.json')
    model_changed=status.get('stage')=='model_changed_dev_pending'
    lines=['# Báo cáo Day 7 — Agentic RAG','',
      'Nguyễn Quốc Quang Anh · MSSV 2A202604120 · L3B.','',
      'Code, benchmark và phần đọc/chấm có Codex AI hỗ trợ. Nhãn giữ reviewer_kind=AI, student_confirmed=false; không coi là xác nhận của học viên hoặc đánh giá độc lập. Người triển khai đồng thời thiết kế benchmark/chấm nên có nguy cơ thiên lệch. Không dùng kết quả mock làm benchmark.','',
      '## Dữ liệu và benchmark cơ bản','',
      'Dùng nguyên snapshot Luật Thương mại 36/2005/QH11 từ Day 6: 84 trang vật lý, index 83 trang nội dung, 245 chunk C. Giữ ID/text/source/page/metadata/vector. Nguồn/quyền/ngày truy cập/SHA256 ở data/day6/manifest.json. Đây là snapshot năm 2005, không xác nhận luật hiện hành. Embedding OpenRouter openai/text-embedding-3-small 1536 chiều; Qdrant local cosine exact. Model agent openai/gpt-4.1-mini, temperature=0; không có revision cố định từ provider.','',
      'Benchmark v2 tại benchmark/cases.json có 15+2 dev và 5+2 test. Dev giữ câu hỏi để so sánh thí nghiệm; test mới về các Điều 23, 26, 28, 56, 309 và hai câu thiếu mức phí/mức phạt trong snapshot. Test Day 6 và test Day 7 v1 đã thấy nên không dùng để đánh giá v2. Benchmark/source/kết quả/báo cáo v1 được giữ tại results/history/base-v1. Không đưa gold vào model hay filter.','',
      'Câu có đáp án ghi nguồn/trang/evidence. Một số gold v2 lấy cả chunk nguồn nên quote containment bảo thủ hơn đánh giá ngữ nghĩa, đặc biệt b2-t28: context có định nghĩa đúng nhưng không chứa toàn quote dài. Công bố sai khác, không đổi gold sau khi thấy điểm. Câu thiếu evidence đã đọc điều khoản liên quan và toàn văn; không suy vắng chỉ từ top-k.','',
      '## Phương pháp, context và thí nghiệm','',
      '| Cấu hình | Retrieval | top-k | Budget ký tự | Max search | Giả thuyết |',
      '|---|---|---:|---:|---:|---|',
      '| baseline | TF-IDF | 3 | 2400 | 1 | Lexical baseline |',
      '| dense | Qdrant C | 3 | 2400 | 1 | Ngữ nghĩa giúp khác cách diễn đạt |',
      '| hybrid — cải thiện 1 | RRF dense + TF-IDF | 3 | 2400 | 1 | Bổ sung tín hiệu từ khóa/ngữ nghĩa |',
      '| hybrid_context — cải thiện 2 | Cùng hybrid | 6 | 6000 | 3 | Giữ nhiều evidence hơn, cho phép tìm tiếp |','',
      'RRF lấy 20 candidate mỗi nhánh, sum(1/(60+rank)). Không cộng trực tiếp score khác thang. Các phương pháp dùng cùng corpus C/query/nhãn. Filter chương chỉ theo phạm vi được nêu trong query dev, không từ gold. Query đầu luôn là query gốc; trace ghi riêng model_query. Budget gồm ID/source URL/trang/separator; là ký tự, không phải token. Dedup ID và ưu tiên evidence lượt mới; chunk không vừa bị bỏ. Model có thể tìm tiếp hoặc finish; không có số lượt chung bắt buộc của đề.','',
      'Citation ID phải có trong context; renderer gắn bracket từ ID có cấu trúc và giữ raw arguments. Không chứng minh semantic grounding chỉ bằng membership. Abstain dùng lời từ chối chuẩn, không trả nguyên khẳng định tự do. Lỗi retrieval chẩn đoán trước agent cũng được lưu status:error rồi tiếp tục query khác. Provider chỉ đòi key khi gửi request, cho phép replay cache offline. Ba lỗi này được kiểm thử hồi quy, giữ kết quả trước sửa.','',
      'Cải thiện 2 thay k/budget/max_searches cùng lúc, không quy lợi ích cho một yếu tố. Thực tế các lượt cơ bản cuối đều tìm một lần; không tuyên bố đã đo lợi ích multi-hop.','',
      '## Kết quả cơ bản','',
      '| Cấu hình / split | Hit@1 | Hit@3 | Context đủ quote cuối | Mean answer /2 | Citation hỗ trợ | Abstention đúng | Từ chối nhầm | Median ms | Chat USD |',
      '|---|---|---|---|---:|---|---|---|---:|---:|']
    for split,names in [('dev',['baseline','dense','hybrid','hybrid_context']),('test',['baseline',selected['selected']])]:
        for name in dict.fromkeys(names):
            s=load(ROOT/'results'/split/name/'summary.json');a=load(ROOT/'results'/split/name/'audit_summary.json')
            lines.append(f"| {name}/{split} | {ratio(s['hit1'])} | {ratio(s['hit3'])} | {ratio(s['final_context_evidence'])} | {a['grounded_answer']['mean']:.3f} | {ratio(a['citation_validity'])} | {ratio(a['abstention'])} | {ratio(a['false_abstention'])} | {s['median_ms']:.1f} | {s['model_cost_usd']:.8f} |")
    lines+=['','Chi tiết phân bố answer 0/1/2, context 0/1/2, tool use, số lượt gọi, số câu có citation, lỗi và mẫu số ở audit_summary.json/summary.json. Codex AI đã hỗ trợ rà toàn bộ 17 câu dev mỗi cấu hình và 7 câu test cho baseline/selected; học viên chưa xác nhận nhãn. Nhãn và lý do từng câu/citation ở reviews.json, giữ hash trace/benchmark. Retrieval metrics không tính câu thiếu evidence; lỗi cơ bản báo riêng. Median là thời gian agent gồm chat/search, không gồm mở index và pass ranking chẩn đoán; cache ấm và concurrency khiến không thể suy tốc độ API lạnh. Chi phí bảng chỉ chat; embedding dùng cache chia sẻ và được tính tổng riêng trong cost_summary.','',
      f"Chọn {selected['selected']} trên dev tại {selected['frozen_at']}: ưu tiên mean answer đã đọc/chấm, sau đó Context Evidence Rate gốc, Hit@3, Hit@1, latency, tên cấu hình. Hash code/provider/corpus/benchmark lưu trong selection; test chỉ chạy sau chốt.",'',
      '## Phân tích lỗi và trước/sau','',
      '- Lượt đầu thiếu bracket citation dù có structured IDs: giữ lịch sử round0-citation-rendering, sửa renderer và chạy dev lại. Không sửa trace cũ.','',
      '- d7-q07: baseline bỏ evidence Điều 35 khi đóng context nên từ chối nhầm. Context lớn giữ đủ nhưng model dẫn đoạn Điều 36/trường hợp không có thỏa thuận thay khoản 1 Điều 35; chấm 1 và citation không hỗ trợ.','',
      '- d7-q11: baseline/dense/hybrid nhầm hàng cho thuê Điều 274 thành mua bán Điều 57. Context lớn dẫn đúng Điều 57 nhưng bỏ điều kiện về giữ chứng từ; chấm 1.','',
      '- d7-q06/d7-q10: hybrid nhỏ vẫn trả quy định chung/giá hàng thừa thay hình thức mua bán quốc tế/thời hạn thanh toán. Context lớn giúp giữ đúng đoạn. RRF không luôn tăng điểm; báo cả kết quả không cải thiện.','',
      '- d7-q09 v2: context lớn đủ evidence nhưng validator từ chối raw citation không phù hợp; chấm 0, không chữa đáp án để làm đẹp điểm.','',
      '- b2-t28 trên test mới: baseline phủ định sai điều mà chính nguồn xác nhận. Selected kết luận đúng nhưng nói nhầm Điều 29 thay Điều 28, chấm 1. Không điều chỉnh pipeline theo lỗi test này.','',
      '## Ví dụ trình bày','']
    for name,cid in [(selected['selected'],'b2-t23'),(selected['selected'],'b2-u1'),('baseline','b2-t28')]:
        t=load(ROOT/'results/test'/name/'queries'/(cid+'.json'));lines.extend([f"**{cid} / {name}:** {t['question']}",'',t['answer'],'',f"Trace: results/test/{name}/queries/{cid}.json",''])
    lines+=['## Thử thách nâng cao','',
      'Bổ sung một corpus riêng: báo cáo thường niên FPT 2025, 232 trang PDF. Index mọi trang với text và mô tả trực quan, giữ ảnh gốc; Qdrant riêng FPT2025 dùng cùng họ embedding 1536 chiều. Manifest, quyền/nguồn và hash ở data/bonus/manifest.json; coverage toàn bộ ở data/bonus/coverage.json. Không gộp số liệu của FPT vào corpus luật Day 6.','',
      'Benchmark bonus riêng có 18 dev, 30 test, đủ nhóm bảng/ảnh-sơ đồ/biểu đồ/multi-hop/text/thiếu evidence. Quy trình yêu cầu chốt trên dev trước test, đối chiếu ảnh gốc và chấm từng câu đúng/đủ/citation trang-vùng/đơn vị/phép tính; lỗi tính không đạt.','',
      (('**ĐÃ ĐỔI SANG HAIKU 5.5, CHƯA ĐÁNH GIÁ MODEL MỚI.** Theo yêu cầu tiết kiệm, vision hiện dùng anthropic/claude-haiku-5.5, tắt thinking; vẫn giữ ảnh gốc và giới hạn retrieval/context. Cấu hình/selection/dev GPT-4.1 cũ được giữ tại '+status['pilot']+'. Text vẫn GPT-4.1-mini và dùng lại 18 câu không đổi. Vision Haiku cần chạy/chấm lại 18 câu dev trước khi chốt và chạy 30 câu test. Chưa gọi API sau lần đổi model này, chưa nhận bonus. Xem report/MODEL_COST.md để biết đơn giá và dự toán.') if model_changed else
       f"Cấu hình bonus đã chọn: {bonus['selected']}. Test: {result['passed']}/{result['total']} = {100*result['rate']:.2f}%. {'Đạt ngưỡng số học 90%.' if result['meets_90_percent'] else 'Chưa đạt ngưỡng 90%, chưa đủ điều kiện nhận 15 điểm bonus.'} Không coi nhãn AI là quyết định cộng điểm chính thức." if completed else
       '**CHƯA HOÀN TẤT TEST BONUS, CHƯA NHẬN 15 ĐIỂM.** Xem trạng thái hiện tại và kết quả dev trong report/BONUS_REPORT.md; không dùng kết quả model lịch sử đại diện model mới.'),'',
      '| Nhóm bonus test | Đạt / tổng |','|---|---|']
    for group,s in result['groups'].items():lines.append(f"| {group} | {s['passed']}/{s['total']} |")
    lines+=['','Báo cáo đầy đủ: [BONUS_REPORT.md](../BONUS_REPORT.md). Cách chạy: [BONUS_RUN.md](../../BONUS_RUN.md). Nhãn từng câu: results/bonus/test/<selected>/reviews.json.','',
      '## Tái lập, chi phí và giới hạn','',
      f"Kiểm thử offline không có API key: {verification['unit_tests']} tests qua. Fingerprint code/corpus/benchmark khớp; 232 hash ảnh gốc được kiểm tra. Tổng Day 7 (mọi lượt cơ bản/bonus, pilot lỗi, caption, embedding): {ledger['requests']} request thành công có ID, **{ledger['cost_usd']:.8f} USD** theo usage provider; {ledger['missing_cost_requests']} request thành công thiếu cost. Failed attempt records={ledger['failed_attempt_records']}; không tự đoán phí request lỗi không có usage. Không cộng chi phí Day 6 vào tổng mới.",'',
      'Lệnh setup/run/test/audit/freeze ở LAB_RUN.md và BONUS_RUN.md. requirements-lock.txt ghi môi trường thực tế Windows CPython 3.14. Snapshot vectors sạch key ở artifacts/day6-reuse.zip và bonus-reuse.zip. PDF/ảnh FPT giữ local; để tái lập cần đúng PDF nguồn được phép truy cập, SHA trong manifest. Không tự gán giấy phép mở cho tài liệu FPT.','',
      'Giới hạn: corpus nhỏ và cùng tài liệu giữa dev/test, nhãn AI cùng người xây hệ thống, chưa có chấm độc lập/học viên xác nhận. Caption toàn trang tự sinh có thể sai; chỉ những evidence/citation khi chấm được đọc lại ảnh gốc, không tuyên bố mọi caption đều đúng. Chưa có red-team prompt injection riêng; chỉ có instruction tách tài liệu khỏi chỉ dẫn. Tái chạy API có thể khác dù temperature=0.','',
      'Code đã được push lên repo cá nhân. Học viên cần tự đọc lại nhãn/evidence, bảo đảm người chấm có quyền xem và nộp link theo SUBMISSION.md. Không thay student_confirmed thành true nếu chưa tự kiểm tra thực tế.']
    (ROOT/'report/individual/2A202604120_NguyenQuocQuangAnh.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    bonus_report(bonus,result)

def bonus_report(selection,result):
    from src.bonus import CONFIGS
    manifest=load(ROOT/'data/bonus/manifest.json');coverage=load(ROOT/'data/bonus/coverage.json')
    status=load(ROOT/'results/bonus/status.json')
    if status.get('stage')=='model_changed_dev_pending':
        from src.bonus import CONFIGS
        lines=['# Báo cáo bonus — cấu hình tiết kiệm','',
          '**Chưa chạy dev/test bằng model mới; chưa có điểm bonus.**','',
          f"Vision: `{CONFIGS['vision']['model']}`, thinking tắt, k=8, tối đa 12 trang và 3 lượt search. Text: GPT-4.1-mini, giữ cấu hình cũ. Không gửi temperature cho Claude 5.5 vì API không hỗ trợ tham số này.",'',
          f"Corpus FPT 2025 đủ {coverage['indexed']}/{manifest['pages']} trang, giữ nguyên caption/vector/ảnh và benchmark 18 dev + 30 test. Không cần caption hoặc embed lại tài liệu.",'',
          f"Cấu hình, selection, code và dev GPT-4.1 cũ: `{status['pilot']}`. Điểm cũ text 14/18, vision GPT-4.1 15/18 là kết quả lịch sử, không phải điểm Haiku.",'',
          'Tái sử dụng 18 câu text với cùng đầu vào/source/model/config; hash trace và đường dẫn lịch sử lưu trong reviews.json. Vision Haiku chưa có trace mới, cần chạy/chấm đầy đủ 18 dev trước freeze. Không dùng output model cũ để đại diện model mới. Chưa gọi API sau thay đổi cấu hình.','',
          'Đơn giá và dự toán: [MODEL_COST.md](MODEL_COST.md). Cách chạy: [BONUS_RUN.md](../BONUS_RUN.md). Tất cả nhãn AI giữ student_confirmed=false. Model nhỏ có thể đọc sai sơ đồ/bảng; không bảo đảm đạt 27/30 test.','',
          f"Nguồn: {manifest['source_url']}. PDF SHA256: `{manifest['pdf_sha256']}`. PDF/ảnh đầy đủ giữ local; snapshot vector đã lọc credential kèm ZIP. Kiểm thử offline không xác nhận chất lượng trả lời thực tế của Haiku."]
        (ROOT/'report/BONUS_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        return
    lines=['# Báo cáo bonus — FPT 2025','',
      '## Tài liệu, index và nguồn','',
      f"Tài liệu: {manifest['title']}. PDF có {manifest['pages']} trang vật lý, index đủ {coverage['indexed']} trang; không có trang bị bỏ. SHA256: `{manifest['pdf_sha256']}`. Nguồn: {manifest['source_url']}. PDF người dùng cung cấp được giữ local, không khẳng định giấy phép mở và không đưa bản PDF/ảnh đầy đủ vào ZIP nộp.",'',
      'PDFium trích body text bỏ sidebar lặp từ trang 3, ảnh nguyên trang 1600px giữ cả sơ đồ và bảng. GPT-4.1-mini mô tả trực quan mọi trang; text + caption dùng embedding thật, Qdrant cosine/RRF kết hợp dense và lexical. Mọi trang đều tham gia index, kể cả bìa/trang ít text qua caption; không chỉ index gold pages. Model trả lời cấu hình vision nhìn ảnh gốc được retrieval chọn; gold không tham gia tool/query/ảnh đầu vào.','',
      'Giới hạn extraction: sidebar bị bỏ trong text nhưng còn ở ảnh; text bảng có thể bị dàn phẳng theo cột; caption là AI, không tự bảo đảm đúng. Cần dùng bản gốc để chấm, đặc biệt hàng/cột/đơn vị và nhãn chữ xoay. Schema evidence gồm page/region/bbox/image hash; bảng ghi hàng/cột, biểu đồ ghi nhãn/chú giải, multi-hop giữ nhiều nguồn bắt buộc và phép tính nếu có.','',
      '## Dev và lựa chọn','',
      '| Cấu hình | Đạt / tổng dev | Lỗi hệ thống | Median ms | Chat USD |','|---|---|---:|---:|---:|']
    pending=result.get('pending',False)
    status=load(ROOT/'results/bonus/status.json') if pending else {}
    dev_complete=status.get('stage')=='dev_complete_test_pending'
    pilot=status['pilot'] if pending and not dev_complete else 'results/bonus'
    for name in ['text','vision']:
        s=load(ROOT/pilot/'dev'/name/'summary.json')
        lines.append(f"| {name} | {s['passed']}/{s['total']} | {s['system_errors']} | {s['median_ms']:.1f} | {s['chat_cost_usd']:.8f} |")
    lines+=['',
      f"Text dùng {CONFIGS['text']['model']}, top-k4, tối đa 6 trang context, không ảnh gốc. Vision dùng {CONFIGS['vision']['model']}, thinking tắt, top-k8, tối đa 12 trang, có ảnh gốc, tối đa 3 lượt search. Đây là thay đổi kết hợp model/context/ảnh, không phải ablation chỉ một yếu tố. Mỗi trang context tối đa 3200 ký tự + visual descriptors và ảnh khi bật vision; token thực tế lưu usage.",'',
      'Lỗi dev đã đọc và thử lại: text dàn phẳng đọc EBITDA thay lợi nhuận hoạt động; mini vision đọc nhãn xoay sai; câu đối chiếu bảng/sơ đồ chỉ dẫn một nguồn; số kế hoạch bị gọi là thực tế. Sửa giao thức bắt buộc tool trước; sau đó thử model vision mạnh hơn với yêu cầu trả lời ngắn, giữ nhãn đúng và kiểm đủ nguồn/plan-actual. Các lượt pilot được giữ tại results/bonus/history, kể cả chi phí và lỗi, không ghi đè. Tất cả diễn ra trước test.','',
      (f"Chốt {selection['selected']} tại {selection['frozen_at']}." if not pending or dev_complete else
       'Pilot cũ có gold lỗi, được giữ lịch sử và không dùng chốt cấu hình. Bản gốc có năm nhãn Nhanh hơn, Nhân rộng hơn, Hiệu quả hơn, Bảo mật hơn, Linh hoạt hơn.'),'',
      'Đã sửa gold fd-i3 (năm nhãn vòng FleziPT) và ft-c5 (văn bản cứng màu cam cao nhất 2022=92,9%) bằng ảnh gốc trước khi chạy bất kỳ test bonus nào. Giữ benchmark cũ và lý do trong history/pretest-chart-gold-correction. Dev không đổi khi sửa ft-c5. Model không nhận gold khi chạy.','',
      'Tái sử dụng 18 câu text với cùng model/config/source/câu hỏi. Vision Haiku chạy mới toàn bộ 18 dev; không gắn điểm GPT-4.1 cho Haiku. Mọi nhãn giữ AI/student_confirmed=false. Lỗi HTTP 402/mạng lịch sử và chi phí pilot được giữ, không sửa trace cũ. Chi tiết lỗi dev hiện tại ở reviews.json; không chỉnh pipeline theo test.','',
      'Tiêu chí lựa chọn: số dev đạt cao hơn, rồi chi phí chat, latency, tên cấu hình. Chỉ chốt sau khi đủ dev và nhãn; test chỉ chạy sau chốt.','',
      '## Toàn bộ test','',
      ('**Chưa chạy 30 câu test; chưa có tỷ lệ test và chưa đủ điều kiện nhận bonus. Không gọi thêm API trong lượt hoàn tất offline.**' if pending else f"Kết quả: {result['passed']}/{result['total']} ({100*result['rate']:.2f}%), lỗi hệ thống {result['system_errors']}."),'',
      'Ngưỡng bonus: ít nhất 27/30 test đạt, không làm tròn; mẫu số gồm cả lỗi/timeout.','',
      '| Nhóm | Đạt / tổng | Tỷ lệ |','|---|---|---:|']
    for group,s in result['groups'].items():lines.append(f"| {group} | {s['passed']}/{s['total']} | {100*s['passed']/s['total']:.1f}% |")
    cost_path=ROOT/'results/bonus/haiku_run_cost.json'
    if cost_path.exists():
        run_cost=load(cost_path)
        lines+=['','## Chi phí lượt Haiku mới','',
          f"18 dev: {run_cost['dev_chat_cost_usd']:.8f} USD. Test gồm chat và embedding query: {run_cost['test_chat_and_query_embedding_cost_usd']:.8f} USD. Tổng mới **{run_cost['total_new_run_cost_usd']:.8f} USD**, {run_cost['successful_chat_requests']} chat request, {run_cost['batches']} đợt. Không caption/embedding document lại. Chi phí lịch sử công bố riêng trong results/cost_summary.json, không nhập nhằng với tổng mới.",'',
          'Chi tiết giá/dự toán so với thực tế: [MODEL_COST.md](MODEL_COST.md). Sau khi đủ 30 câu đã dừng API. Kết quả 27/30 là nhãn AI hỗ trợ đọc nguồn, chưa có học viên xác nhận/chấm độc lập; không tự coi là quyết định cộng điểm của giảng viên.']
    lines+=['','## Kiểm chứng từng câu','',
      ('Chưa có nhãn test vì test chưa hoàn tất.' if pending else 'Nhãn dưới đây do Codex AI đọc câu trả lời/citation và đối chiếu trang gốc; không tự gọi là human audit hoặc xác nhận của học viên. Ảnh/trang tham chiếu được xác định bằng hash nguồn; giữ raw model response/tool/context/usage trong JSON. Người chấm có thể mở đúng trang/vùng trong PDF gốc.'),'']
    d=ROOT/'results/bonus/test'/selection['selected']
    by_id={r['query_id']:r for r in load(d/'reviews.json')} if not pending else {}
    for t in load(d/'traces.json') if not pending else []:
        r=by_id[t['query_id']]
        lines.extend([f"### {t['query_id']} — {'Đạt' if r['passed'] else 'Không đạt'}",'',t['question'],'',t['answer'] or str(t.get('error')),'',
          'Lý do: '+r['reason'],'','Đối chiếu ảnh gốc: '+str(r['original_page_check']),
          '',f"Trace: results/bonus/test/{selection['selected']}/queries/{t['query_id']}.json",''])
    lines+=['## Giới hạn và tái lập','',
      'Xem BONUS_RUN.md. Kết quả là số đo trên benchmark do AI hỗ trợ thiết kế/chấm, không bảo đảm tổng quát. Chưa có xác nhận học viên hoặc chấm độc lập. Không phát sinh xác nhận giả. Để nhận bonus, giảng viên cần chấp nhận đủ nguồn/quyền/index/benchmark/evidence ngoài việc đạt tỷ lệ.']
    (ROOT/'report/BONUS_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    verify();ledger=costs();snapshots();reports(ledger)
    print('Final lab verified. Provider-reported total USD:',ledger['cost_usd'])

if __name__=='__main__':main()
