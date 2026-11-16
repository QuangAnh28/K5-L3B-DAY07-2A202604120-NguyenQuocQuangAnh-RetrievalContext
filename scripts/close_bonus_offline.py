"""One-time, offline preservation of the billing-interrupted pilot and gold correction.

Decisions below are explicit AI-assisted source reviews, not automatic grading.
Only byte-identical, successful dev cases can carry over to the corrected benchmark.
"""
from pathlib import Path
from datetime import datetime, timezone
import sys, shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save,digest

def main():
    root=ROOT/'results/bonus';history=root/'history/round2-billing-and-gold-errata'
    if (root/'status.json').exists():
        print('Already preserved; no changes.');return
    assert not (root/'test').exists() and not (root/'selection.json').exists()
    old=load(ROOT/'benchmark/bonus_cases.json');pages={p['page']:p for p in load(ROOT/'data/bonus/pages.json')}
    history.mkdir(parents=True,exist_ok=True)
    for rel in ['src/bonus.py','src/bonus_ingest.py','src/provider.py','benchmark/bonus_cases.json',
                'benchmark/bonus_protocol.json','scripts/prepare_bonus_benchmark.py']:
        dest=history/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
    decisions={
      'fd-c1':'Đúng đỉnh ROE 2024=28,5%, năm 2025=28,1%, chênh 0,4 điểm phần trăm; citation đúng biểu đồ.',
      'fd-c2':'Đúng Việt Nam 48,9%; citation xác định biểu đồ và chú giải.',
      'fd-c3':'Đúng chú giải cam là doanh thu CNTT nước ngoài, đơn vị tỷ VNĐ.',
      'fd-i2':'Đúng mốc 1998, hệ thống quản lý đối tượng nộp thuế VAT và 61 cục Thuế.',
      'fd-m1':'Đủ cả hai địa điểm điện mặt trời ở trang 147 và công trình EDGE ở trang 153; citation đủ hai nguồn.',
      'fd-m3':'Đủ định vị AI trong vận hành và vai trò FleziPT. Trang 50 nêu AI tích hợp xuyên suốt giải pháp/quy trình, chấp nhận thay thế tương đương phần định vị ở trang 4; trang 63 hỗ trợ vai trò nền tảng, trang 51 hỗ trợ ứng dụng FleziPT nếu có dẫn.',
      'fd-t2':'Đúng 49%, citation đúng dòng sở hữu nước ngoài.',
      'fd-t3':'Đúng 1.751 tỷ VNĐ và 70,0%, citation đúng hàng Viễn thông.',
      'fd-u1':'Từ chối; báo cáo có kế hoạch 2026, không có doanh thu thực tế cả năm đó.',
      'fd-u2':'Từ chối; các phần AI Factory không cung cấp bảng giá thuê giờ theo loại GPU.',
      'fd-u3':'Nêu rõ không công bố tiền từng hộ, không đoán từ tổng số người hưởng lợi; trang 158 phù hợp chủ đề.',
      'fd-x1':'Đủ thời gian, chi phí, năng suất lao động và citation thông điệp Chủ tịch.',
      'fd-x2':'Đúng Reduce/Reuse/Recycle và giải thích 3R, citation phần quản lý chất thải.',
      'fd-x3':'Đúng 42% nhà cung cấp trọng yếu tham gia và 97% đạt yêu cầu, citation phần mua sắm bền vững.'}
    failures={
      'fd-m2':'Chỉ trích bảng vai trò trang 125; không dẫn sơ đồ trang 31 và gọi nhầm bảng là sơ đồ. Không đủ hai loại evidence mà câu hỏi yêu cầu đối chiếu.',
      'fd-i1':'Nêu đúng Đại hội đồng cổ đông và HĐQT nhưng thêm/đặt Ban kiểm soát vào đường chính hoặc chuỗi cấp tiếp theo. Ảnh trang 31 cho thấy Ban kiểm soát là nhánh riêng; không đạt tiêu chí toàn bộ câu trả lời được hỗ trợ.',
      'fd-i3':'Câu dev/gold bị lỗi: ảnh gốc có năm nhãn NHANH HƠN, NHÂN RỘNG HƠN, HIỆU QUẢ HƠN, BẢO MẬT HƠN, LINH HOẠT HƠN; không có THÔNG MINH HƠN. Không dùng item lỗi để kết luận đạt. Vision nêu ba nhãn thực có; text thay nhãn bằng diễn giải. Cần sửa câu hỏi/gold trước lựa chọn.'}
    for name in ['text','vision']:
        directory=root/'dev'/name;reviews=[]
        for t in load(directory/'traces.json'):
            q=next(q for q in old if q['id']==t['query_id']);cid=q['id']
            ok=cid in decisions;reason=decisions.get(cid,failures.get(cid,''))
            if cid=='fd-t1':
                ok=name=='vision';reason=('Đúng 12.952 tỷ VNĐ, 17,5%; phép trừ 12.952−11.025=1.927 tỷ VNĐ.' if ok else 'Sai hàng: 15.958 là EBITDA, không phải lợi nhuận thuần hoạt động kinh doanh 12.952; tỷ lệ đúng là 17,5%.')
            if t['status']=='error':ok=False;reason='Không có câu trả lời hoàn chỉnh: '+str(t['error'])+'. Tính không đạt, giữ trong mẫu số; không suy nguyên nhân thanh toán từ mã HTTP.'
            source_pages={g['page'] for g in q.get('gold',[])}|set(q.get('absence_check',{}).get('related_original_pages',[]))
            if cid=='fd-m3':source_pages|={3,50,51}
            reviews.append({'query_id':cid,'passed':ok,'reason':reason,
              'original_page_check':[{'page':p,'region':'Vùng evidence của câu hỏi và citation; xem gold/trace để định vị.',
                                     'image_sha256':pages[p]['image_sha256']} for p in sorted(source_pages)],
              'trace_sha256':digest(directory/'queries'/(cid+'.json')),
              'benchmark_sha256':digest(ROOT/'benchmark/bonus_cases.json'),
              'reviewer_kind':'AI','student_confirmed':False,'reviewed_at':datetime.now(timezone.utc).isoformat()})
        save(directory/'reviews.json',reviews)
    from src.bonus import audit,CONFIGS,fingerprint
    for name in CONFIGS:audit('dev',name)
    # Verify absolute source/target paths before moving the generated result tree.
    source=(root/'dev').resolve();target=(history/'dev').resolve()
    assert source.is_relative_to(ROOT.resolve()) and target.is_relative_to(ROOT.resolve())
    source.rename(target)
    (root/'protocol.json').rename(history/'protocol.json')
    new=load(ROOT/'benchmark/bonus_cases.json');q=next(q for q in new if q['id']=='fd-i3')
    q['question']='Vòng ngoài cùng của hình nền tảng FleziPT thể hiện năm lợi ích nào?'
    q['expected_answer']='Nhanh hơn, Nhân rộng hơn, Hiệu quả hơn, Bảo mật hơn, Linh hoạt hơn.'
    q['gold'][0]['evidence']='NHANH HƠN; NHÂN RỘNG HƠN; HIỆU QUẢ HƠN; BẢO MẬT HƠN; LINH HOẠT HƠN.'
    save(ROOT/'benchmark/bonus_cases.json',new)
    protocol=load(ROOT/'benchmark/bonus_protocol.json');protocol['benchmark_sha256']=digest(ROOT/'benchmark/bonus_cases.json')
    protocol['dev_revision_note']='Corrected fd-i3 against original page 63 before any bonus test. Prior benchmark and pilot preserved. Test cases unchanged.'
    save(ROOT/'benchmark/bonus_protocol.json',protocol)
    current={'fingerprint':fingerprint(),'configs':CONFIGS,'selection_criterion':'Higher dev audited pass count; lower model cost; lower median latency; config name.'}
    save(root/'protocol.json',current);reused={};pending={}
    old_by_id={q['id']:q for q in old}
    for name in CONFIGS:
        directory=root/'dev'/name;save(directory/'run.json',current);rows=[];reviews=[];pending[name]=[];reused[name]=[]
        previous_reviews={r['query_id']:r for r in load(history/'dev'/name/'reviews.json')}
        for q in [q for q in new if q['split']=='dev']:
            src=history/'dev'/name/'queries'/(q['id']+'.json');t=load(src)
            if q!=old_by_id[q['id']] or t['status']=='error':pending[name].append(q['id']);continue
            # Same source/model/config/question: reuse actual output, never generate answers.
            dest=directory/'queries'/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
            r=previous_reviews[q['id']].copy();r['benchmark_sha256']=digest(ROOT/'benchmark/bonus_cases.json')
            r['reused_from']=src.relative_to(ROOT).as_posix();r['reason']+=' Reused unchanged case/source/config from preserved pilot; no new API request.'
            rows.append(t);reviews.append(r);reused[name].append(q['id'])
        save(directory/'traces.json',sorted(rows,key=lambda t:t['query_id']));save(directory/'reviews.json',reviews)
    save(root/'status.json',{'stage':'offline_complete_bonus_dev_pending','network_calls_stopped':True,
      'reason':'User requested offline work after OpenRouter HTTP 402; billing cause unverified.',
      'bonus_test_run':False,'bonus_points_claimed':0,'benchmark_correction':'fd-i3: five actual labels; archived incorrect gold.',
      'reused_successful_unchanged_dev_cases':reused,'pending_dev_queries':pending,
      'pilot':history.relative_to(ROOT).as_posix(),'reviewer_kind':'AI','student_confirmed':False,
      'next':'Resume only missing dev cases; audit their new outputs, then freeze and test. Changing model invalidates reuse for that configuration.'})
    print('Offline preservation and correction complete; pending dev:',pending)

if __name__=='__main__':main()
