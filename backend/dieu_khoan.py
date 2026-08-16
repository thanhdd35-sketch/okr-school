"""
DIEU KHOAN BAO VE DU LIEU CA NHAN — v2.6

LUU Y: Day la BAN NHAP KY THUAT, soan theo cau truc yeu cau cua
Luat Bao ve du lieu ca nhan so 91/2025/QH15. Cau chu phap ly CAN DUOC
BAN GIAM HIEU / BO PHAN PHAP CHE NHA TRUONG DUYET truoc khi ap dung that.

Khi sua noi dung -> PHAI tang PHIEN_BAN. He thong se yeu cau nguoi dung
dong y lai ban moi (bang chung tuan thu duoc luu theo tung phien ban).
"""

PHIEN_BAN = "1.1"   # 1.1: go bo hoan toan tinh nang AI khoi he thong

NOI_DUNG = {
    "phien_ban": PHIEN_BAN,
    "tieu_de": "Điều khoản bảo vệ dữ liệu cá nhân",
    "cap_nhat": "2026",
    "muc": [
        {
            "tieu_de": "1. Bên kiểm soát dữ liệu",
            "noi_dung": "Nhà trường là bên kiểm soát dữ liệu cá nhân được xử lý trên hệ thống "
                        "quản lý mục tiêu (OKR) này. Hệ thống chỉ phục vụ mục đích giáo dục nội bộ."
        },
        {
            "tieu_de": "2. Dữ liệu được thu thập",
            "noi_dung": "Hệ thống chỉ thu thập dữ liệu tối thiểu cần thiết: họ tên, email, lớp học, "
                        "vai trò, mục tiêu và kết quả học tập do chính người dùng nhập, nhận xét của "
                        "giáo viên và ý kiến của phụ huynh. Hệ thống KHÔNG thu thập số điện thoại, "
                        "địa chỉ, dữ liệu sức khỏe hay bất kỳ dữ liệu nhạy cảm nào khác."
        },
        {
            "tieu_de": "3. Mục đích xử lý",
            "noi_dung": "Dữ liệu được sử dụng để: theo dõi tiến độ mục tiêu của học sinh; hỗ trợ giáo viên "
                        "chủ nhiệm đánh giá và tư vấn; giúp phụ huynh nắm được tình hình của con; "
                        "tổng hợp báo cáo phục vụ quản lý của nhà trường."
        },
        {
            "tieu_de": "4. Nguyên tắc đánh giá học sinh",
            "noi_dung": "Hệ thống không xếp hạng, không so sánh học sinh với học sinh khác. "
                        "Hệ thống KHÔNG sử dụng trí tuệ nhân tạo (AI) để nhận xét, chấm điểm hay "
                        "xếp loại học sinh. Toàn bộ nhận xét và đánh giá do giáo viên trực tiếp thực hiện "
                        "và chịu trách nhiệm. Dữ liệu học sinh không được gửi tới bất kỳ dịch vụ AI nào."
        },
        {
            "tieu_de": "5. Bên thứ ba tham gia xử lý",
            "noi_dung": "Hệ thống chỉ sử dụng dịch vụ lưu trữ và vận hành của nhà cung cấp hạ tầng "
                        "điện toán đám mây. Các bên này chỉ được xử lý dữ liệu theo yêu cầu của nhà trường, "
                        "bị ràng buộc bởi thỏa thuận xử lý dữ liệu và không được sử dụng dữ liệu "
                        "cho mục đích riêng."
        },
        {
            "tieu_de": "6. Thời gian lưu trữ",
            "noi_dung": "Dữ liệu được lưu trong thời gian học sinh còn theo học tại trường. "
                        "Sau khi học sinh ra trường hoặc chuyển trường, dữ liệu sẽ được ẩn danh hóa "
                        "theo chính sách lưu trữ của nhà trường. Nhật ký truy cập hệ thống được lưu "
                        "tối thiểu 12 tháng phục vụ mục đích an toàn thông tin."
        },
        {
            "tieu_de": "7. Bảo mật",
            "noi_dung": "Mật khẩu được mã hóa một chiều, hệ thống không lưu và không thể xem được mật khẩu gốc. "
                        "Dữ liệu được mã hóa khi truyền và khi lưu trữ. Mọi truy cập vào dữ liệu nhạy cảm "
                        "đều được ghi nhật ký. Mỗi người dùng chỉ truy cập được dữ liệu trong phạm vi "
                        "vai trò của mình; phụ huynh chỉ xem được dữ liệu của con mình."
        },
        {
            "tieu_de": "8. Quyền của người dùng",
            "noi_dung": "Người dùng (hoặc cha mẹ, người giám hộ đối với học sinh chưa thành niên) có quyền: "
                        "được biết dữ liệu nào đang được xử lý; yêu cầu chỉnh sửa dữ liệu không chính xác; "
                        "yêu cầu xóa dữ liệu; rút lại sự đồng ý. Liên hệ giáo viên chủ nhiệm hoặc bộ phận "
                        "quản trị hệ thống của nhà trường để thực hiện các quyền này."
        },
        {
            "tieu_de": "9. Trách nhiệm của người dùng",
            "noi_dung": "Người dùng có trách nhiệm giữ bí mật mật khẩu, không chia sẻ tài khoản cho người khác, "
                        "và thông báo ngay cho nhà trường khi phát hiện tài khoản bị sử dụng trái phép."
        },
    ],
    "ghi_chu": "Bằng việc bấm Đồng ý, bạn xác nhận đã đọc và hiểu các nội dung trên.",
}
