import os
import sys
import warnings

# Tắt cảnh báo phiền phức từ Pandas
warnings.filterwarnings("ignore", category=UserWarning)

# Khởi tạo đường dẫn module dự án
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Giả lập các hàm Streamlit cache
import streamlit as st
st.cache_data = lambda *args, **kwargs: lambda func: func
st.cache_data.clear = lambda: None

from repositories.order_repository import OrderRepository

def run_order_test():
    print("🚀 Bắt đầu quá trình kiểm tra độc lập OrderRepository...")
    
    # 1. Đồng bộ và kiểm tra số lượng bản ghi hiện tại
    try:
        df_init = OrderRepository.get_all_orders()
        print(f"✅ Kết nối và lấy danh sách đơn hàng thành công! Số lượng hiện tại: {len(df_init)} đơn.")
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách đơn hàng ban đầu: {e}")
        return

    # Mẫu dữ liệu kiểm thử độc lập
    test_order_num = "TEST-POSTGRES-2026"
    
    # 2. Thử nghiệm hàm Upsert (Thêm mới)
    print(f"\n📝 Đang thực hiện Upsert đơn hàng kiểm thử: {test_order_num}...")
    try:
        OrderRepository.upsert_order(
            customer_name="Công Ty Thử Nghiệm Thiết Bị",
            order_number=test_order_num,
            measurement_date="2026-07-04",
            cert_status="Chưa cấp",
            sale_owner="Sale Test Postgres",
            created_by="Hệ thống Test",
            disable_calibration_notification=0,
            disable_document_notification=1,
            disable_payment_notification=0
        )
        print("✅ Upsert (Thêm mới) đơn hàng thành công!")
    except Exception as e:
        print(f"❌ Lỗi trong quá trình Upsert: {e}")
        print("💡 Gợi ý: Khả năng cao cột 'order_number' chưa được set ràng buộc UNIQUE trên Postgres.")
        return  # Dừng chương trình luôn nếu lỗi, không chạy xuống dưới nữa

    # 3. Tìm kiếm chính xác đơn hàng vừa tạo để chứng minh dữ liệu đã ghi thực tế
    print(f"\n🔍 Tìm kiếm đơn hàng mã {test_order_num}...")
    df_check = OrderRepository.get_by_order_number(test_order_num)
    if not df_check.empty:
        print("✅ Đã tìm thấy đơn hàng trong cơ sở dữ liệu Postgres!")
        print(f"   Khách hàng: {df_check.iloc[0]['customer_name']} | Sale: {df_check.iloc[0]['sale_owner']}")
    else:
        print("❌ Lỗi: Không tìm thấy dữ liệu trong Database dù không crash!")
        return

    # 4. Thử nghiệm chức năng chuyển nhượng chủ sở hữu theo danh sách (IN clause)
    print(f"\n🔄 Thử nghiệm tính năng bàn giao đơn hàng (mệnh đề IN)...")
    try:
        OrderRepository.transfer_sale_owner_by_orders([test_order_num], "Bàn Giao Thao Tác")
        df_check_transferred = OrderRepository.get_by_order_number(test_order_num)
        print(f"✅ Bàn giao thành công! Sale hiện tại: {df_check_transferred.iloc[0]['sale_owner']}")
    except Exception as e:
        print(f"❌ Lỗi khi thực hiện bàn giao đơn hàng: {e}")
        return

    # 5. Dọn dẹp dữ liệu kiểm thử (Xóa Cascade) để khôi phục DB sạch sẽ
    print(f"\n🗑️ Tiến hành xóa Cascade dữ liệu mẫu {test_order_num}...")
    try:
        OrderRepository.delete_order_cascade(test_order_num)
        df_final_check = OrderRepository.get_by_order_number(test_order_num)
        if df_final_check.empty:
            print("✅ Xóa dữ liệu mẫu Cascade thành công! Cơ sở dữ liệu sạch sẽ.")
            print("\n🎉 CHÚC MỪNG! ORDER REPOSITORY HOẠT ĐỘNG HOÀN HẢO TRÊN POSTGRESQL!")
        else:
            print("❌ Lỗi: Bản ghi kiểm thử vẫn tồn tại sau khi chạy lệnh xóa.")
    except Exception as e:
        print(f"❌ Lỗi trong quá trình xóa dữ liệu mẫu: {e}")

if __name__ == "__main__":
    run_order_test()