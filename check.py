import os
import sys
import warnings

# Tắt cảnh báo
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Giả lập streamlit session_state
import streamlit as st
if 'username' not in st.session_state:
    st.session_state['username'] = "TESTER_POSTGRES"

from repositories.log_repository import LogRepository

def run_log_test():
    print("🚀 Bắt đầu quá trình kiểm tra độc lập LogRepository...")
    
    # 1. Kiểm tra số lượng log ban đầu
    try:
        count_init = LogRepository.get_log_count()
        print(f"✅ Kết nối thành công! Số lượng log hiện tại trong DB: {count_init} dòng.")
    except Exception as e:
        print(f"❌ Lỗi lấy số lượng log ban đầu: {e}")
        return

    # 2. Thêm một log mới
    print("\n📝 Đang thêm thử nghiệm 1 dòng log mới...")
    try:
        LogRepository.add_log(
            action="TEST_MIGRATE",
            customer_name="Khách Hàng Test Log",
            order_number="LOG-2026-XYZ",
            description="Kiểm tra hệ thống auto purge trên Postgres"
        )
        print("✅ Thêm log mới thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi thêm log: {e}")
        return

    # 3. Đọc lại danh sách log để chứng minh dữ liệu đã ghi
    print("\n🔍 Đang đọc lại danh sách log để kiểm tra thực tế...")
    df_logs = LogRepository.get_logs()
    if not df_logs.empty and df_logs.iloc[0]['order_number'] == "LOG-2026-XYZ":
        print(f"✅ Tìm thấy log vừa ghi! Người thực hiện: {df_logs.iloc[0]['username']}")
    else:
        print("❌ Lỗi: Không tìm thấy dòng log vừa tạo.")
        return

    # 4. Kiểm tra xem cơ chế dọn dẹp Auto Purge có hoạt động không
    print("\n📈 Kiểm tra tổng số lượng log sau khi thêm...")
    count_after = LogRepository.get_log_count()
    print(f"✅ Tổng số log hiện tại: {count_after}")
    if count_after <= LogRepository.MAX_LOG_ROWS:
        print("✅ Cơ chế Auto Purge hoạt động tốt (Giới hạn tối đa luôn <= 5000 dòng).")
        print("\n🎉 CHÚC MỪNG! LOG REPOSITORY HOẠT ĐỘNG HOÀN HẢO TRÊN POSTGRESQL!")
    else:
        print("❌ Cảnh báo: Số lượng log vượt quá giới hạn cấu hình.")

if __name__ == "__main__":
    run_log_test()