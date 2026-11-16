"""Author the predeclared FPT benchmark; never imported by agent/retrieval modules."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.common import load,save,digest

cases=[]
def evidence(page,region,quote,bbox=None):
    return {'source_id':'FPT-annual-report-2025','page':page,'page_id':f'FPT2025:p{page:03}',
            'region':region,'bbox_normalized':bbox or [0.24,0.03,0.98,0.96],
            'evidence':quote,'image_sha256':load(ROOT/'data/bonus/pages.json')[page-1]['image_sha256']}
def add(split,cid,group,question,answer,items,calculation=None):
    row={'id':cid,'split':split,'group':group,'question':question,'answerable':True,
         'expected_answer':answer,'gold':items,'evidence_rule':'All listed evidence components required; equivalent original evidence accepted with explicit reviewer justification.',
         'reason':'Evidence transcribed/checked against original PDF page images, physical pages 1-based.',
         'reviewer_kind':'AI','student_confirmed':False}
    if calculation:row['calculation']=calculation
    cases.append(row)

# DEV: three answerable questions in each of five groups, plus three unanswerable.
add('dev','fd-t1','table','Theo bảng tình hình tài chính giai đoạn 2021–2025, lợi nhuận thuần từ hoạt động kinh doanh năm 2025 và mức tăng so với năm 2024 là bao nhiêu?',
    '12.952 tỷ VNĐ, tăng 17,5%.',[evidence(12,'Bảng tài chính, hàng 4, cột 2025 và +/-','Lợi nhuận thuần từ hoạt động kinh doanh: 12.952; 17,5%.')])
add('dev','fd-t2','table','Trong bảng thông tin cổ phiếu, tỷ lệ sở hữu tối đa của cổ đông nước ngoài là bao nhiêu?',
    '49%.',[evidence(32,'Bảng thông tin cổ phiếu, dòng tỷ lệ sở hữu tối đa cổ đông nước ngoài','Tỷ lệ sở hữu tối đa của cổ đông nước ngoài: 49%.')])
add('dev','fd-t3','table','Bảng thực hiện dự án đầu tư cho biết Khối Viễn thông giải ngân năm 2025 bao nhiêu và đạt bao nhiêu phần trăm kế hoạch?',
    '1.751 tỷ VNĐ, đạt 70,0% kế hoạch.',[evidence(75,'Bảng góc trên trái, hàng Viễn thông, cột Giải ngân 2025 và So với kế hoạch','Viễn thông: kế hoạch 2.500; giải ngân 1.751; 70,0%.')])
add('dev','fd-c1','chart','Trên biểu đồ ROE giai đoạn 2021–2025, năm nào cao nhất và ROE năm 2025 thấp hơn đỉnh bao nhiêu điểm phần trăm?',
    'Năm 2024 cao nhất 28,5%; năm 2025 là 28,1%, thấp hơn 0,4 điểm phần trăm.',
    [evidence(11,'Biểu đồ ROE/ROA, đường ROE, điểm năm 2024 và 2025','ROE 2024=28,5%; 2025=28,1%.')],'28.5 - 28.1 = 0.4 percentage points')
add('dev','fd-c2','chart','Trong biểu đồ doanh thu theo khu vực địa lý toàn Tập đoàn, khu vực nào có tỷ trọng lớn nhất và tỷ trọng đó là bao nhiêu?',
    'Việt Nam, 48,9%.',[evidence(27,'Biểu đồ vành khuyên bên phải, chú giải Việt Nam','Việt Nam 48,9%, lớn nhất.')])
add('dev','fd-c3','chart','Biểu đồ Dịch vụ Chuyển đổi số dùng màu cam cho chỉ tiêu nào và đơn vị trục giá trị là gì?',
    'Màu cam là doanh thu Dịch vụ CNTT cho thị trường nước ngoài; đơn vị tỷ VNĐ.',
    [evidence(63,'Biểu đồ cột bên trái, chú giải màu cam và đơn vị dưới biểu đồ','Cam: Doanh thu dịch vụ CNTT cho thị trường nước ngoài. Đơn vị: Tỷ VNĐ.')])
add('dev','fd-i1','diagram','Trong sơ đồ tổ chức FPT, nút nào nằm trên cùng và đường chính dẫn xuống cấp quản trị nào?',
    'Đại hội đồng cổ đông nằm trên cùng, dẫn xuống Hội đồng quản trị.',
    [evidence(31,'Sơ đồ tổ chức, nút cam trên cùng và nút xanh bên dưới','ĐẠI HỘI ĐỒNG CỔ ĐÔNG → HỘI ĐỒNG QUẢN TRỊ.')])
add('dev','fd-i2','diagram','Trên dòng thời gian hành trình FPT, mốc 1998 ghi nhận triển khai hệ thống gì, cho bao nhiêu cục thuế?',
    'Hệ thống Quản lý đối tượng nộp thuế VAT cho 61 cục Thuế Việt Nam.',
    [evidence(28,'Timeline, mốc 1998 ở hàng trên bên phải','1998: Hệ thống Quản lý đối tượng nộp thuế VAT cho 61 cục Thuế, 61 máy chủ, hơn 500 máy trạm.')])
add('dev','fd-i3','diagram','Vòng ngoài cùng của hình nền tảng FleziPT thể hiện ba lợi ích nào?',
    'Nhanh hơn, Thông minh hơn, Linh hoạt hơn.',
    [evidence(63,'Sơ đồ vòng tròn bên phải, chữ xanh ngoài rìa','NHANH HƠN; THÔNG MINH HƠN; LINH HOẠT HƠN.')])
add('dev','fd-x1','text','Theo thông điệp Chủ tịch HĐQT, ba bài toán sống còn doanh nghiệp phải giải trong kỷ nguyên AI là gì?',
    'Thời gian, chi phí và năng suất lao động.',[evidence(4,'Cột trái, mục Ba yếu tố sống còn trong kỷ nguyên AI','Ba bài toán: thời gian, chi phí, năng suất lao động.')])
add('dev','fd-x2','text','Nguyên tắc 3R trong quản lý chất thải được báo cáo giải thích như thế nào?',
    'Giảm thiểu (Reduce), Tái sử dụng (Reuse), Tái chế (Recycle).',[evidence(150,'Phần quản lý chất thải bên phải','3R – Giảm thiểu (Reduce), Tái sử dụng (Reuse), Tái chế (Recycle).')])
add('dev','fd-x3','text','Năm 2025 có bao nhiêu nhà cung cấp trọng yếu tham gia đánh giá CSR, và tỷ lệ nhà cung cấp đạt yêu cầu theo tiêu chí đánh giá là bao nhiêu?',
    '42% nhà cung cấp trọng yếu tham gia đánh giá CSR; 97% nhà cung cấp đạt yêu cầu.',
    [evidence(128,'Các gạch đầu dòng kết quả mua sắm bền vững','42% nhà cung cấp trọng yếu tham gia đánh giá CSR; 97% nhà cung cấp đạt yêu cầu.')])
add('dev','fd-m1','multi_hop','Nêu hai địa điểm có hệ thống điện mặt trời mái nhà được đưa vào hoạt động năm 2025 và xác định công trình nào được nêu là đầu tiên ở Việt Nam đạt EDGE.',
    'Điện mặt trời tại F-Complex Đà Nẵng và Data Center Tp.Hồ Chí Minh; FPT Complex Đà Nẵng được nêu là công trình đầu tiên ở Việt Nam đạt EDGE.',
    [evidence(147,'Đoạn điện mặt trời mái nhà','Hai hệ thống tại F-Complex Đà Nẵng và Data Center Tp.Hồ Chí Minh.'),
     evidence(153,'Đoạn FPT Complex Đà Nẵng','FPT Complex Đà Nẵng là công trình đầu tiên tại Việt Nam đạt chứng chỉ EDGE.')])
add('dev','fd-m2','multi_hop','Đối chiếu sơ đồ tổ chức với bảng trách nhiệm phát triển bền vững: cấp nào phê duyệt chiến lược, cấp nào triển khai, và hai cấp đó được sắp theo thứ tự nào?',
    'HĐQT phê duyệt chiến lược; Ban Điều hành triển khai. Sơ đồ đặt HĐQT phía trên Tổng Giám đốc và Ban Điều hành.',
    [evidence(31,'Đường dọc chính của sơ đồ','HĐQT phía trên Tổng Giám đốc và Ban Điều hành.'),
     evidence(125,'Bảng vai trò trách nhiệm bên trái','HĐQT: phê duyệt/ban hành chiến lược; Ban Điều hành: đảm bảo triển khai chiến lược.')])
add('dev','fd-m3','multi_hop','Kết hợp thông điệp AI-Native và phần giới thiệu FleziPT: AI được định vị thế nào trong vận hành, và FleziPT giúp FPT tiến tới mô hình đó bằng cách nào?',
    'AI trở thành nền tảng vận hành cốt lõi; FleziPT tái định nghĩa quy trình phát triển/vận hành phần mềm, nâng năng suất nội bộ và làm nền tảng cung cấp giải pháp AI chuyên sâu.',
    [evidence(4,'Cuối mục ba yếu tố sống còn','AI không chỉ là công cụ hỗ trợ, trở thành nền tảng vận hành cốt lõi.'),
     evidence(63,'Đoạn giới thiệu FleziPT','Nâng cao năng suất/hiệu quả nội bộ bằng tái định nghĩa quy trình và cung cấp giải pháp AI chuyên sâu.')])

# TEST: 6 tables, 5 diagrams/maps, 5 charts, 4 multi-hop, 4 text, 6 abstention.
add('test','ft-t1','table','Trong bảng tài chính giai đoạn 2021–2025, tổng tài sản và vốn chủ sở hữu cuối năm 2025 lần lượt là bao nhiêu? Ghi đúng đơn vị.',
    'Tổng tài sản 88.142 tỷ VNĐ; vốn chủ sở hữu 43.748 tỷ VNĐ.',
    [evidence(12,'Bảng, hàng 2 và 1, cột 2025','Tổng tài sản 88.142; Vốn chủ sở hữu 43.748; đơn vị tỷ VNĐ.')])
add('test','ft-t2','table','Theo bảng chỉ tiêu kinh doanh, lãi cơ bản trên cổ phiếu năm 2024 và 2025 là bao nhiêu? Đơn vị của hàng này có giống đơn vị chung của bảng không?',
    '2024: 4.292 VNĐ; 2025: 5.216 VNĐ. Hàng EPS dùng VNĐ, khác đơn vị chung tỷ VNĐ.',
    [evidence(58,'Bảng bên phải, hàng Lãi cơ bản trên cổ phiếu và chú thích (*)','EPS 4.292/5.216; riêng Lãi cơ bản trên cổ phiếu đơn vị VNĐ.')])
add('test','ft-t3','table','Trong kế hoạch đầu tư dự kiến năm 2026, hai khối được phân bổ bao nhiêu vốn, tổng bao nhiêu và Khối Công nghệ chiếm bao nhiêu phần trăm tổng ngân sách?',
    'Công nghệ 4.200 tỷ VNĐ; Giáo dục, Đầu tư và Khác 3.000 tỷ VNĐ; tổng 7.200 tỷ VNĐ; Công nghệ khoảng 58,33%.',
    [evidence(55,'Bảng Kế hoạch đầu tư dự kiến ở cuối trang','4.200; 3.000; Tổng cộng 7.200 tỷ VNĐ.')], '4200 / 7200 * 100 = 58.333333%')
add('test','ft-t4','table','Dựa vào hàng Tổng doanh thu trong bảng 2021–2025, doanh thu tăng thêm bao nhiêu tỷ VNĐ từ năm 2021 đến năm 2025?',
    'Từ 35.657 lên 70.113 tỷ VNĐ, tăng 34.456 tỷ VNĐ.',
    [evidence(12,'Bảng, hàng Tổng doanh thu, cột 2021 và 2025','2021: 35.657; 2025: 70.113 tỷ VNĐ.')],'70113 - 35657 = 34456 tỷ VNĐ')
add('test','ft-t5','table','Theo bảng chỉ tiêu kinh doanh năm 2025, cổ tức tiền mặt trả trong năm là bao nhiêu, tăng bao nhiêu phần trăm so với năm trước?',
    '3.185 tỷ VNĐ, tăng 16,2% so với 2024.',
    [evidence(58,'Bảng, hàng Cổ tức tiền mặt trả trong năm, cột 2025 và Tăng/Giảm','2024=2.741; 2025=3.185 tỷ VNĐ; +16,2%.')])
add('test','ft-t6','table','Trong bảng tổng hợp tiêu thụ điện, điện tiêu thụ năm 2025, điện từ năng lượng tái tạo và tỷ lệ tái tạo lần lượt là bao nhiêu?',
    '187.453.013 kWh; 842.749 kWh; 0,45%.',
    [evidence(147,'Bảng tiêu thụ điện, cột Năm 2025, ba hàng','Tiêu thụ điện 187.453.013; tái tạo 842.749; tỷ lệ 0,45%. Đơn vị kWh.')])
add('test','ft-i1','diagram','Theo sơ đồ tổ chức, hai đơn vị nào nằm trong nhánh Công ty liên kết?',
    'Synnex FPT và FPT Retail.',[evidence(31,'Nhánh Công ty liên kết ở phần phải dưới của sơ đồ','CÔNG TY LIÊN KẾT nối Synnex FPT và FPT Retail.')])
add('test','ft-i2','diagram','Theo các đường nối trong sơ đồ tổ chức, Khối Viễn thông gồm những đơn vị nào?',
    'FPT Online và FPT Telecom.',[evidence(31,'Nhánh Công ty con → Khối Viễn thông, hàng dưới giữa sơ đồ','KHỐI VIỄN THÔNG nối FPT Online và FPT Telecom.')])
add('test','ft-i3','diagram','Đọc sơ đồ tròn FleziPT: ba lớp có tên viết hoa được xếp từ tâm ra ngoài theo thứ tự nào?',
    'FLEZI FOUNDATION → FLEZI CREW → FLEZI VERSE.',
    [evidence(63,'Hình tròn bên phải, tâm xanh, vòng cam, vòng xanh lá','FLEZI FOUNDATION ở tâm; FLEZI CREW bao quanh; FLEZI VERSE ở ngoài.')])
add('test','ft-i4','diagram','Trong hình quy trình xác định vấn đề trọng yếu ESG, ba bước được sắp theo thứ tự nào?',
    'Bước 1 xác định vấn đề chính ảnh hưởng hoạt động kinh doanh và lợi ích các bên liên quan; Bước 2 phân tích/xác định vấn đề được các bên quan tâm; Bước 3 phân tích các vấn đề trong mối quan hệ với các bên liên quan.',
    [evidence(125,'Ba khối Bước 01/02/03 phía phải','Bước 01 xác định ảnh hưởng; Bước 02 các bên quan tâm; Bước 03 mối quan hệ với các bên liên quan.')])
add('test','ft-i5','diagram','Trên bản đồ hiện diện toàn cầu của FPT, Nhật Bản và Úc có được gắn nhãn địa điểm hiện diện không?',
    'Có, cả Nhật Bản và Úc đều được gắn nhãn trên bản đồ.',
    [evidence(27,'Bản đồ thế giới, khu vực Đông Á và châu Đại Dương','Có các nhãn Nhật Bản và Úc trên bản đồ hiện diện.')])
add('test','ft-c1','chart','Trên đường ROA trong biểu đồ 2021–2025, mức cao nhất thuộc năm nào và năm 2025 giảm bao nhiêu điểm phần trăm so với năm 2024?',
    'Cao nhất năm 2024 là 14,4%; năm 2025 là 14,1%, giảm 0,3 điểm phần trăm.',
    [evidence(11,'Đường ROA, điểm 2024 và 2025, chú giải ROA','ROA 2024=14,4%; 2025=14,1%.')],'14.4 - 14.1 = 0.3 percentage points')
add('test','ft-c2','chart','Trong biểu đồ doanh thu Dịch vụ CNTT cho thị trường nước ngoài theo khu vực, thị trường nào lớn nhất năm 2025, giá trị và tỷ trọng bao nhiêu?',
    'Nhật Bản: 15.452 tỷ VNĐ, chiếm 43,7%.',
    [evidence(62,'Biểu đồ vành khuyên bên phải, lát Nhật Bản','Nhật Bản 15.452; 43,7%; tổng 35.382 tỷ VNĐ.')])
add('test','ft-c3','chart','Đọc các cột màu xanh của biểu đồ doanh thu Dịch vụ Chuyển đổi số: giá trị năm 2024 và 2025 là bao nhiêu và tăng thêm bao nhiêu?',
    '2024: 14.340 tỷ VNĐ; 2025: 16.751 tỷ VNĐ; tăng 2.411 tỷ VNĐ.',
    [evidence(63,'Biểu đồ trái, cột xanh 2024 và 2025, chú giải Dịch vụ Chuyển đổi số','Cột xanh 2024=14.340; 2025=16.751 tỷ VNĐ.')],'16751 - 14340 = 2411 tỷ VNĐ')
add('test','ft-c4','chart','Theo biểu đồ họp trực tuyến/trực tiếp 2023–2025, tỷ lệ họp trực tuyến từ năm 2023 đến 2025 tăng bao nhiêu điểm phần trăm?',
    'Từ 67,8% lên 94,0%, tăng 26,2 điểm phần trăm.',
    [evidence(152,'Biểu đồ thanh ngang phía dưới bên phải, Họp trực tuyến 2023/2025','2023 trực tuyến 67,8%; 2025 94,0%.')],'94.0 - 67.8 = 26.2 percentage points')
add('test','ft-c5','chart','Trong biểu đồ số hóa tài liệu 2022–2025, tỷ lệ văn bản cứng cao nhất ở năm nào và tỷ lệ văn bản cứng năm 2025 là bao nhiêu?',
    'Cao nhất năm 2024: 21,1%; năm 2025: 4,58%.',
    [evidence(152,'Biểu đồ cột đôi phía dưới bên trái, chú giải văn bản cứng','Văn bản cứng: 2022 7,1%; 2023 17,6%; 2024 21,1%; 2025 4,58%.')])
add('test','ft-m1','multi_hop','Đối chiếu bảng chỉ tiêu kinh doanh toàn Tập đoàn với biểu đồ doanh thu Chuyển đổi số: năm 2025 hai giá trị LNTT và doanh thu Chuyển đổi số là bao nhiêu, chênh lệch số học bao nhiêu tỷ VNĐ?',
    'LNTT 13.044 tỷ VNĐ; doanh thu Chuyển đổi số 16.751 tỷ VNĐ; doanh thu Chuyển đổi số lớn hơn 3.707 tỷ VNĐ. Đây là hai chỉ tiêu khác nhau, chỉ so chênh lệch số học.',
    [evidence(58,'Bảng chỉ tiêu kinh doanh, hàng LNTT cột 2025','LNTT 13.044 tỷ VNĐ.'),
     evidence(63,'Biểu đồ cột xanh 2025/đoạn mở đầu','Doanh thu Chuyển đổi số 16.751 tỷ VNĐ.')],'16751 - 13044 = 3707 tỷ VNĐ')
add('test','ft-m2','multi_hop','So sánh ngân sách đầu tư Khối Công nghệ trong kế hoạch 2026 với số giải ngân Khối Công nghệ năm 2025: mỗi số là bao nhiêu và chênh lệch bao nhiêu tỷ VNĐ?',
    'Kế hoạch 2026: 4.200 tỷ VNĐ; giải ngân 2025: 2.823 tỷ VNĐ; chênh lệch 1.377 tỷ VNĐ.',
    [evidence(55,'Bảng Kế hoạch đầu tư dự kiến, hàng Khối Công nghệ','Khối Công nghệ 4.200 tỷ VNĐ kế hoạch 2026.'),
     evidence(75,'Bảng dự án đầu tư, Công nghệ, cột Giải ngân 2025','Công nghệ giải ngân 2025: 2.823 tỷ VNĐ.')],'4200 - 2823 = 1377 tỷ VNĐ')
add('test','ft-m3','multi_hop','Kết hợp phần văn phòng không giấy tờ và phần kiểm kê khí nhà kính: tỷ lệ paperless năm 2025 và mốc mục tiêu Net Zero là gì? Tỷ lệ paperless có đồng nghĩa đã đạt Net Zero không?',
    'Paperless năm 2025 đạt 95,42%; mục tiêu Net Zero vào 2040. Không: một chỉ số số hóa tài liệu không chứng minh đã hoàn thành mục tiêu phát thải.',
    [evidence(152,'Đoạn văn phòng không giấy tờ','Tỷ lệ sử dụng paperless đạt 95,42% năm 2025.'),
     evidence(146,'Đoạn lộ trình Net Zero','Mục tiêu Net Zero vào năm 2040.')])
add('test','ft-m4','multi_hop','Tổng hợp đối tượng và quy mô hưởng lợi của Trường Hy Vọng mới và dự án Bếp Xanh – Sống Lành: số nào là học sinh, số nào là người dân?',
    'Trường Hy Vọng mới là ngôi nhà cho hơn 300 học sinh thuộc 13 dân tộc; Bếp Xanh – Sống Lành giúp hơn 1.000 người dân tiếp cận bếp cải tiến.',
    [evidence(156,'Đoạn Trường Hy Vọng','Hơn 300 học sinh thuộc 13 dân tộc.'),
     evidence(158,'Đoạn Bếp Xanh – Sống Lành','Giúp hơn 1.000 người dân tiếp cận bếp cải tiến.')])
add('test','ft-x1','text','Theo thông điệp Chủ tịch, sau một năm các nhà máy AI đã khai thác khoảng bao nhiêu công suất và xử lý bao nhiêu token?',
    'Khoảng 70% công suất, xử lý hơn 1.100 tỷ token.',
    [evidence(5,'Đoạn lợi thế AI Factory','Khoảng 70% công suất, hơn 1.100 tỷ token.')])
add('test','ft-x2','text','Công trình nào được báo cáo nêu là đầu tiên tại Việt Nam đạt EDGE, và những giải pháp nào được nhắc kèm?',
    'FPT Complex Đà Nẵng; tiết kiệm năng lượng, thu hồi nước mưa, xử lý nước thải, điều hòa và chiếu sáng hiệu suất cao.',
    [evidence(153,'Đoạn FPT Complex Đà Nẵng','Đầu tiên tại Việt Nam đạt EDGE nhờ tiết kiệm năng lượng, thu hồi nước mưa, xử lý nước thải, điều hòa/chiếu sáng hiệu suất cao.')])
add('test','ft-x3','text','Theo nguyên tắc an ninh dữ liệu, khi cần tiết lộ thông tin bảo mật ra ngoài vì yêu cầu công việc, phải thực hiện gì trước?',
    'Thực hiện biện pháp bảo vệ phù hợp, ví dụ ký cam kết bảo mật với bên liên quan trước khi tiết lộ.',
    [evidence(129,'Gạch đầu dòng Nguyên tắc an ninh','Trường hợp yêu cầu công việc, thực hiện biện pháp bảo vệ phù hợp như ký cam kết bảo mật trước tiết lộ.')])
add('test','ft-x4','text','Báo cáo liệt kê những nguyên tắc nào cho việc thu thập, xử lý, lưu trữ và sử dụng dữ liệu?',
    'Hợp pháp; mục đích; chất lượng dữ liệu; an ninh; quản trị.',
    [evidence(129,'Danh sách 5 nguyên tắc quản trị dữ liệu','Nguyên tắc hợp pháp, mục đích, chất lượng dữ liệu, an ninh, quản trị.')])

absence=[
 ('dev','fd-u1','Báo cáo cho biết doanh thu thực tế cả năm 2026 của FPT là bao nhiêu?',
  'Báo cáo 2025 có kế hoạch 2026, không có doanh thu thực tế cả năm 2026.',[55]),
 ('dev','fd-u2','Giá thuê niêm yết theo giờ của từng loại GPU tại FPT AI Factory trong năm 2025 là bao nhiêu?',
  'Có mô tả năng lực AI Factory, không có bảng đơn giá giờ GPU theo loại.',[5]),
 ('dev','fd-u3','Dự án Bếp Xanh – Sống Lành ghi số tiền tài trợ cụ thể cho từng hộ gia đình là bao nhiêu?',
  'Chỉ có quy mô người hưởng lợi và mục đích, không có mức tài trợ theo hộ.',[158]),
 ('test','ft-u1','Báo cáo có số doanh thu năm 2025 riêng của từng khách hàng thuộc nhóm FPT Software không? Hãy liệt kê đầy đủ từng khách hàng và doanh thu.',
  'Báo cáo có một số khách hàng/hợp đồng điển hình, không có bảng đầy đủ doanh thu từng khách hàng FPT Software.',[7,62]),
 ('test','ft-u2','Theo báo cáo, nêu chi tiết lượng phát thải CO2 toàn Tập đoàn của từng tháng trong năm 2025.',
  'Bảng kiểm kê cung cấp tổng theo năm/phạm vi, không phân rã đầy đủ từng tháng.',[146]),
 ('test','ft-u3','Từ báo cáo, số serial của từng GPU đang hoạt động tại hai nhà máy AI là gì?',
  'Có năng lực và công suất AI Factory, không có danh mục serial thiết bị.',[5]),
 ('test','ft-u4','Trong báo cáo có tỷ lệ chính xác lỗi suy luận của từng mô hình ngôn ngữ lớn do FPT AI Factory phát triển không? Nêu từng mô hình và tỷ lệ.',
  'Có số lượng mô hình và năng lực, không có benchmark lỗi suy luận theo từng mô hình.',[5]),
 ('test','ft-u5','Hãy đưa số tiền tài trợ của Bếp Xanh – Sống Lành cho từng hộ dân trong một danh sách đầy đủ.',
  'Chỉ có tổng quy mô hưởng lợi, không có danh sách tiền theo hộ. Câu này cùng loại dữ kiện với dev-u3 nên không dùng trong test.',[158]),
 ('test','ft-u6','Báo cáo có lịch sử chính xác từng giao dịch mua cổ phiếu FPT của từng cổ đông cá nhân trong năm 2025 không? Liệt kê toàn bộ.',
  'Có cơ cấu cổ đông/tổng cổ phiếu, không có sổ giao dịch đầy đủ từng cá nhân.',[32])]
# Replace one initially drafted test question before any experiment: avoid dev/test paraphrase.
absence=[(s,cid,('Báo cáo có bảng chi phí điện năm 2025 theo từng máy chủ riêng lẻ ở các Data Center không? Nêu đầy đủ.' if cid=='ft-u5' else q),
 ('Báo cáo có số điện tiêu thụ tổng hợp, không phân bổ chi phí tới từng máy chủ.' if cid=='ft-u5' else reason),
 ([147] if cid=='ft-u5' else pages)) for s,cid,q,reason,pages in absence]
for split,cid,q,reason,pages in absence:
    cases.append({'id':cid,'split':split,'group':'unanswerable','question':q,'answerable':False,
      'expected_behavior':'search_and_abstain','absence_reason':reason,
      'absence_check':{'method':'Whole extracted report/topic review and original related pages; absence is not inferred from retrieval top-k.',
                       'related_original_pages':pages,'total_pages_checked':232,'reviewer_kind':'AI'},
      'reason':reason,'student_confirmed':False})

assert len(cases)==48 and len({q['id'] for q in cases})==48
assert sum(q['split']=='dev' for q in cases)==18
assert sum(q['split']=='test' for q in cases)==30
path=ROOT/'benchmark/bonus_cases.json'
if path.exists() and load(path)!=cases:raise ValueError('Frozen benchmark differs; refusing overwrite')
save(path,cases)
save(ROOT/'benchmark/bonus_protocol.json',{'benchmark_sha256':digest(path),'test_minimums':{'table':6,'diagram':5,'chart':5,'multi_hop':4,'text':4,'unanswerable':6},
 'pass_rule':'Answerable: fully correct, all units/conditions/calculations and necessary original evidence page/region citations. Unanswerable: explicit refusal without unsupported claims. Any system error counts fail; denominator all 30.',
 'split_note':'Created before dev/test agent experiments. Same document, distinct dev/test requested facts; shared pages permitted.',
 'threshold':'27/30, no rounding','review_note':'Original-page semantic review by Codex AI; student confirmation remains false.'})
print('Prepared bonus benchmark: 18 dev, 30 test')
