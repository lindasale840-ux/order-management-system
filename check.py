import os
import sys
import warnings

# Khóa cảnh báo Pandas
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.note_repository import NoteRepository

def run_note_test():
    print("🚀 Bắt đầu quá trình kiểm tra độc lập NoteRepository...")
    
    # Giả định kiểm thử với user_id nhận diện mẫu (Ví dụ: id = 1)
    test_user_id = 1
    
    # 1. Đo lường số lượng note ban đầu
    try:
        notes_init = NoteRepository.get_notes(test_user_id, is_admin=False)
        print(f"✅ Lấy danh sách thành công! User {test_user_id} đang có {len(notes_init)} ghi chú.")
    except Exception as e:
        print(f"❌ Lỗi kết nối hoặc cấu trúc bảng 'notes' có vấn đề: {e}")
        return

    # 2. Thực hiện tạo mới một Note mẫu
    print("\n📝 Đang tiến hành tạo ghi chú thử nghiệm...")
    note_payload = {
        "user_id": test_user_id,
        "title": "Họp triển khai hệ thống ERP 2026",
        "content": "Kiểm tra toàn bộ các repository sau khi chuyển sang Postgres",
        "category": "Work",
        "priority": "critical",
        "layer": 1,
        "status": "pending",
        "due_date": "2026-07-15"
    }
    
    new_note_id = 0
    try:
        new_note_id = NoteRepository.create_note(note_payload)
        if new_note_id > 0:
            print(f"✅ Tạo Note thành công! ID sinh ra từ Postgres: {new_note_id}")
        else:
            print("❌ Lỗi: Hàm không trả về ID hợp lệ.")
            return
    except Exception as e:
        print(f"❌ Thất bại khi tạo Note: {e}")
        print("💡 Gợi ý: Hãy kiểm tra xem bộ đếm SEQUENCE của bảng 'notes' đã đồng bộ chưa nếu gặp lỗi trùng id.")
        return

    # 3. Đánh dấu Đã đọc / Chưa đọc thử nghiệm
    print(f"\n🔄 Thử nghiệm cập nhật trạng thái đọc của Note ID {new_note_id}...")
    try:
        NoteRepository.mark_as_read(new_note_id, test_user_id)
        print("✅ Đánh dấu ĐÃ ĐỌC thành công.")
        NoteRepository.mark_as_unread(new_note_id, test_user_id)
        print("✅ Đánh dấu CHƯA ĐỌC thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật trạng thái đọc: {e}")

    # 4. Kiểm tra hàm thống kê dữ liệu
    print("\n📊 Kiểm tra hàm thống kê (get_statistics)...")
    try:
        stats = NoteRepository.get_statistics(test_user_id, is_admin=False)
        print(f"✅ Thống kê thành công: Tổng số={stats['total']} | Đang xử lý={stats['in_progress']} | Chưa đọc={stats['unread']}")
    except Exception as e:
        print(f"❌ Lỗi hàm thống kê: {e}")

    # 5. Dọn dẹp dữ liệu test (Xóa Note vừa tạo)
    print(f"\n🗑️ Đang tiến hành xóa Note mẫu ID {new_note_id}...")
    try:
        deleted = NoteRepository.delete_note(new_note_id, test_user_id, is_admin=False)
        if deleted:
            print("✅ Xóa bản ghi thử nghiệm thành công! Cơ sở dữ liệu sạch sẽ.")
            print("\n🎉 CHÚC MỪNG! NOTE REPOSITORY HOẠT ĐỘNG HOÀN HẢO TRÊN POSTGRESQL!")
        else:
            print("❌ Bản ghi chưa được xóa.")
    except Exception as e:
        print(f"❌ Lỗi khi thực hiện xóa: {e}")

if __name__ == "__main__":
    run_note_test()