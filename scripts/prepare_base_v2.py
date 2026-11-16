"""New test after historical Day 7 test was seen. Never replace old evidence/results."""
import sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save,digest

old=load(ROOT/'results/history/base-v1/benchmark/cases.json')
cases=[q for q in old if q['split']=='dev']
chunks=load(ROOT/'data/day6/chunks.json')
specs=[
 ('23','Trước khi chấm dứt hoạt động tại Việt Nam, thương nhân nước ngoài phải thực hiện nghĩa vụ gì với Nhà nước, tổ chức và cá nhân liên quan?',
  'Thanh toán các khoản nợ và các nghĩa vụ khác với Nhà nước, tổ chức, cá nhân liên quan tại Việt Nam.','Trước khi chấm dứt'),
 ('26','Hai trường hợp nào có thể dẫn tới việc áp dụng biện pháp khẩn cấp đối với hàng hóa đang lưu thông hợp pháp trong nước?',
  'Hàng hóa là nguồn gốc hoặc phương tiện lây truyền dịch bệnh; hoặc xảy ra tình trạng khẩn cấp.','Điều 26.'),
 ('28','Theo tài liệu, đưa hàng hóa từ nội địa Việt Nam vào khu vực hải quan riêng nằm trên lãnh thổ Việt Nam có thuộc định nghĩa xuất khẩu không?',
  'Có. Xuất khẩu bao gồm đưa hàng ra khỏi lãnh thổ Việt Nam hoặc vào khu vực đặc biệt trên lãnh thổ Việt Nam được coi là khu vực hải quan riêng theo pháp luật.','Điều 28.'),
 ('56','Bên mua phải làm gì để nhận hàng và hỗ trợ bên bán giao hàng?',
  'Nhận hàng theo thỏa thuận và thực hiện những công việc hợp lý để giúp bên bán giao hàng.','Điều 56.'),
 ('309','Khi hợp đồng bị tạm ngừng thực hiện thì hiệu lực hợp đồng và quyền yêu cầu bồi thường của bên bị vi phạm ra sao?',
  'Hợp đồng vẫn còn hiệu lực; bên bị vi phạm có quyền yêu cầu bồi thường thiệt hại theo Luật này.','Điều 309.')]
for article,question,answer,anchor in specs:
 compact=lambda x:re.sub(r'\s+','',x).casefold()
 candidates=[c for c in chunks if compact(anchor) in compact(c['text'])]
 if not candidates:raise ValueError(anchor)
 c=max(candidates,key=lambda c:len(c['text']))
 # Store the actual source chunk as evidence, avoiding invented whitespace or inferred metadata.
 cases.append({'id':'b2-t'+article,'split':'test','question':question,'expected_answer':answer,
  'answerable':True,'filter':{},'gold':[{'source_id':c['source_id'],'page':c['page'],'evidence':c['text']}],
  'origin':'Fresh base-v2 test, different questions from all Day 6 and historical Day 7 test'})
for cid,question,reason in [
 ('u1','Theo tài liệu, lệ phí cấp giấy phép thành lập Văn phòng đại diện của thương nhân nước ngoài là bao nhiêu đồng?',
  'Luật quy định quyền/nghĩa vụ, điều kiện hoạt động, không nêu số tiền lệ phí cấp giấy phép; kiểm tra toàn text và quy định liên quan.'),
 ('u2','Theo tài liệu, mức tiền phạt hành chính cụ thể bằng đồng đối với hành vi quảng cáo sai sự thật là bao nhiêu?',
  'Điều 322 trang 83 giao Chính phủ quy định cụ thể xử phạt hành chính; snapshot không có biểu mức tiền cho hành vi này.')]:
 cases.append({'id':'b2-'+cid,'split':'test','question':question,'answerable':False,
 'expected_behavior':'search_and_abstain','absence_reason':reason,'filter':{},
 'absence_check':{'method':'Read related provisions and whole extracted source; no rate schedule/fee amount in this corpus',
                  'pages_checked':84,'reviewer':'Codex AI; not student confirmation'}})
path=ROOT/'benchmark/cases.json'
if [q for q in load(path) if q['split']=='test']!=[q for q in old if q['split']=='test'] and load(path)!=cases:
 raise ValueError('Refusing to replace a different benchmark')
save(path,cases)
manifest=load(ROOT/'data/day6/provenance.json');manifest['benchmark_sha256']=digest(path)
manifest['base_v2_note']='Source/Day 6 index unchanged; new Day 7 held-out questions after base-v1 review. Historical benchmark and source under results/history/base-v1.'
save(ROOT/'data/day6/provenance.json',manifest)
print('Prepared base-v2:',len(cases),'cases')
