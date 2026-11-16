"""Import only named Day 6 inputs. No code from the archive is executed."""
import argparse
import re
import zipfile
from pathlib import Path
from .common import ROOT, load, save, digest, normalized

def prepare(archive):
    with zipfile.ZipFile(archive) as z:
        prefix = z.namelist()[0].split('/')[0]+'/'
        names = ['benchmark/questions.json','data/manifest.json','starter/results/chunks_C.json',
                 'starter/results/pages.json','starter/results/embedding_cache.json',
                 'starter/data/luat_thuong_mai_2005.pdf','starter/results/run_dev.json',
                 'starter/results/selection.json','starter/results/qdrant/meta.json',
                 'starter/results/qdrant/collection/C/storage.sqlite']
        for name in names:
            target = ROOT/'.day6'/name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(prefix+name))
    raw = load(ROOT/'.day6/starter/results/chunks_C.json')
    chunks = [{'id':c['chunk_id'],'source_id':c['document_id'],**{k:c[k] for k in ('source','page','text','metadata')}} for c in raw]
    save(ROOT/'data/day6/chunks.json',chunks)
    save(ROOT/'data/day6/manifest.json',load(ROOT/'.day6/data/manifest.json'))
    save(ROOT/'data/day6/pages.json',load(ROOT/'.day6/starter/results/pages.json'))
    old = load(ROOT/'.day6/benchmark/questions.json')
    cases = [{'id':'d7-'+q['id'],'split':'dev','question':q['question'], 'expected_answer':q['expected_answer'],
              'answerable':True,'filter':q.get('filter',{}), 'gold':[{'source_id':q['gold_source_id'],
              'page':q['gold_page'],'evidence':q['evidence_quote']}], 'origin':'Day 6 dev'} for q in old if q['split']=='dev']
    specs = [
        (53,'Nếu không có thỏa thuận khác, giá hàng hóa tính theo trọng lượng dùng trọng lượng nào?','Trọng lượng tịnh.'),
        (60,'Không có thỏa thuận khác, rủi ro của hàng đang trên đường vận chuyển chuyển cho bên mua từ lúc nào?','Từ thời điểm giao kết hợp đồng.'),
        (129,'Hội chợ, triển lãm thương mại được tổ chức để thương nhân làm gì và nhằm mục đích gì?','Trưng bày, giới thiệu hàng hóa, dịch vụ nhằm thúc đẩy, tìm kiếm cơ hội giao kết hợp đồng mua bán hàng hóa, hợp đồng dịch vụ.'),
        (223,'Bên mời thầu và người liên quan phải bảo mật những thông tin nào trong đấu thầu?','Bên mời thầu bảo mật hồ sơ dự thầu; tổ chức, cá nhân liên quan tổ chức đấu thầu và xét chọn thầu phải giữ bí mật thông tin liên quan đấu thầu.'),
        (323,'Theo bản tài liệu, Luật Thương mại 2005 có hiệu lực từ ngày nào và thay thế luật nào?','Từ ngày 01/01/2006, thay thế Luật thương mại ngày 10/05/1997.')]
    for article,question,answer in specs:
        pattern = re.compile(r'Điều\s+'+str(article)+r'\.\s')
        found = [(c,pattern.search(c['text'])) for c in chunks if pattern.search(c['text'])]
        c,m = found[0]
        tail = c['text'][m.start():]
        evidence = re.split(r'\n\nĐiều\s+\d+\.',tail)[0].strip()
        cases.append({'id':f'd7-t{article}','split':'test','question':question,'expected_answer':answer,
            'answerable':True, 'filter':{}, 'gold':[{'source_id':c['source_id'],'page':c['page'],'evidence':evidence}],
            'origin':'New Day 7 test; different articles from Day 6 benchmark'})
    absence = [
        ('dev','u1','Cửa hàng Sao Mai đã hoàn tiền cho khách Nguyễn Văn Bình vào ngày nào?', ['Sao Mai','Nguyễn Văn Bình'],'Corpus không có hồ sơ giao dịch của cửa hàng và khách hàng này.'),
        ('dev','u2','Doanh thu bán hàng năm 2025 của Công ty Ánh Dương trong tài liệu là bao nhiêu?', ['Ánh Dương','2025'],'Corpus là snapshot luật 2005, không có báo cáo doanh thu công ty năm 2025.'),
        ('test','u3','Số tài khoản ngân hàng để thanh toán hợp đồng số HD-2026-071 là gì?', ['HD-2026-071'],'Không có hợp đồng cụ thể HD-2026-071 hoặc thông tin tài khoản của hợp đồng.'),
        ('test','u4','Hội chợ thương mại của Công ty Sao Biển năm 2026 diễn ra tại địa chỉ nào?', ['Sao Biển','2026'],'Không có lịch sự kiện hay địa chỉ hội chợ công ty năm 2026.')]
    pages = load(ROOT/'data/day6/pages.json')
    for split,cid,question,terms,reason in absence:
        matches={term:[p['page'] for p in pages if term.casefold() in p['text'].casefold()] for term in terms}
        if any(matches.values()):
            raise ValueError('Absence keywords unexpectedly present')
        cases.append({'id':'d7-'+cid,'split':split,'question':question,'answerable':False,
            'expected_behavior':'search_and_abstain','absence_reason':reason,
            'absence_check':{'pages_checked':len(pages),'terms':matches,
                'reviewer':'Codex AI; full extracted text topic checked, no transaction/company records'},'filter':{}})
    for q in cases:
        if q['answerable'] and not any(c['page']==g['page'] and c['source_id']==g['source_id'] and normalized(g['evidence']) in normalized(c['text']) for c in chunks for g in q['gold']):
            raise ValueError('Gold does not resolve: '+q['id'])
    path = ROOT/'benchmark/cases.json'
    if path.exists() and load(path)!=cases:
        print('Imported Day 6 corpus; preserved existing revised benchmark and provenance. Initial generator describes v1 only.')
        return
    save(path,cases)
    save(ROOT/'data/day6/provenance.json',{'archive_name':Path(archive).name,'archive_sha256':digest(archive),
        'chunks':len(chunks),'content_pages':83,'physical_pages':84,'collection':'C','dimensions':1536,
        'embedding_model':'openai/text-embedding-3-small','reused':'Unchanged Day 6 C chunks/vectors/IDs',
        'excluded_test_ids':[q['id'] for q in old if q['split']=='test'],
        'test_note':'Day 6 test/report already seen; new questions use different articles. Same-corpus test, AI-authored, not blind independent evaluation.',
        'benchmark_sha256':digest(path),'chunks_sha256':digest(ROOT/'data/day6/chunks.json')})
    print('Prepared',len(chunks),'chunks and',len(cases),'cases (17 dev, 7 test).')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--zip',required=True,type=Path)
    prepare(parser.parse_args().zip)
