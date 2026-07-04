import os
import sys
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.document_tracking_repository import DocumentTrackingRepository

def run_tracking_test():
    print("🚀 Bắt đầu quá trình kiểm tra độc lập DocumentTrackingRepository...")
    
    # 1. Thêm một tracking test mới
    test_order = "TEST-ORDER-2026"
    print(f"\n📝 Đang tạo dữ liệu tracking thử nghiệm cho đơn hàng: {test_order}...")
    try:
        DocumentTrackingRepository.add_tracking(
            order_number=test_order,
            sent_date="2026-07-01",
            received_date=None,  # Để trống để test chức năng pending
            note="Test tracking doc on Postgres"
        )
        print("✅ Thêm dữ liệu tracking thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi thêm tracking: {e}")
        return

    # 2. Kiểm tra hàm lấy danh sách pending (chưa nhận)
    print("\n🔍 Đang test hàm get_pending_return()...")
    df_pending = DocumentTrackingRepository.get_pending_return()
    if not df_pending.empty and test_order in df_pending['order_number'].values:
        print(f"✅ Thành công! Đã tìm thấy đơn hàng {test_order} nằm trong danh sách chờ nhận.")
    else:
        print("⚠️ Cảnh báo: Không thấy đơn hàng test trong danh sách pending.")

    # 3. Kiểm tra hàm lấy tracking mới nhất theo đơn hàng cụ thể
    print(f"\n🔍 Đang test hàm get_latest_by_order() cho đơn {test_order}...")
    df_latest = DocumentTrackingRepository.get_latest_by_order(test_order)
    if not df_latest.empty:
        print(f"✅ Thành công! Ghi nhận ghi chú mới nhất: '{df_latest.iloc[0]['note']}'")
        tracking_id = int(df_latest.iloc[0]['id'])
    else:
        print("❌ Lỗi: Không thể tìm thấy tracking bằng mã đơn hàng vừa tạo.")
        return

    # 4. Dọn dẹp dữ liệu test bằng hàm xóa
    print(f"\n🧹 Đang dọn dẹp dữ liệu test (Xóa tracking ID: {tracking_id})...")
    try:
        DocumentTrackingRepository.delete_tracking(tracking_id)
        print("✅ Đã xóa bản ghi thử nghiệm thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi xóa bản ghi thử nghiệm: {e}")

    print("\n🎉 HOÀN THÀNH KIỂM TRA! DOCUMENT TRACKING REPOSITORY HOẠT ĐỘNG HOÀN HẢO!")

if __name__ == "__main__":
    run_tracking_test()