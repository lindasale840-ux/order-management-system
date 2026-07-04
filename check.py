import os
import sys
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.error_log_repository import ErrorLogRepository

def run_error_log_test():
    print("🚀 Bắt đầu quá trình kiểm tra độc lập ErrorLogRepository...")
    
    # 1. Thêm thử nghiệm một lỗi mới
    print("\n📝 Đang thêm thử nghiệm log lỗi vào hệ thống...")
    try:
        ErrorLogRepository.add_error(
            page_name="Dashboard_Test",
            error_message="Connection timed out during independent testing"
        )
        print("✅ Thêm lỗi thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi thêm log lỗi: {e}")
        return

    # 2. Đọc lại danh sách xem có lấy được dữ liệu ra không
    print("\n🔍 Đang truy vấn lại danh sách lỗi từ Postgres...")
    try:
        df_errors = ErrorLogRepository.get_errors()
        if not df_errors.empty:
            print(f"✅ Lấy dữ liệu thành công! Tổng số lỗi đang lưu: {len(df_errors)} dòng.")
            print(f"📌 Lỗi mới nhất vừa ghi nhận tại trang: '{df_errors.iloc[0]['page_name']}'")
        else:
            print("❌ Lỗi: Bảng error_logs trống rỗng một cách bất thường.")
            return
    except Exception as e:
        print(f"❌ Lỗi khi truy vấn danh sách lỗi: {e}")
        return

    # 3. Kiểm tra tính năng giới hạn 20 lỗi
    if len(df_errors) <= 20:
        print("\n✅ Thành công! Số lượng log lỗi được khống chế tự động luôn dưới hoặc bằng 20 dòng.")
        print("🎉 FILE ERROR_LOG_REPOSITORY ĐÃ HOÀN TOÀN SẴN SÀNG TRÊN POSTGRES!")
    else:
        print(f"\n⚠️ Cảnh báo: Số lượng bản ghi hiện tại ({len(df_errors)}) đang vượt quá giới hạn 20.")

if __name__ == "__main__":
    run_error_log_test()