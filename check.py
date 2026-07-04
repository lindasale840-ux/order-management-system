import os
import sys
import warnings

# Khóa các cảnh báo phiền phức của Pandas để log hiển thị sạch sẽ
warnings.filterwarnings("ignore", category=UserWarning)

# Đảm bảo Python tìm thấy các module trong dự án của bạn
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Giả lập streamlit cache
import streamlit as st
st.cache_data = lambda *args, **kwargs: lambda func: func
st.cache_data.clear = lambda: None

from repositories.other_document_tracking_repository import OtherDocumentTrackingRepository

def test_repository_logic():
    print("🚀 Bắt đầu quá trình kiểm tra độc lập OtherDocumentTrackingRepository...")
    
    # 1. Thử lấy dữ liệu hiện tại
    try:
        df_before = OtherDocumentTrackingRepository.get_all()
        print(f"✅ Đọc thành công! Hiện tại đang có {len(df_before)} dòng tài liệu trong database.")
    except Exception as e:
        print(f"❌ Lỗi khi đọc dữ liệu ban đầu: {e}")
        return

    # 2. Thử thêm mới một bản ghi mẫu
    print("\n📝 Đang thử thêm một bản ghi kiểm thử...")
    success = False
    try:
        OtherDocumentTrackingRepository.add_tracking(
            customer_name="Khách Hàng Test Postgres",
            document_type="Hợp đồng mẫu",
            sent_date="2026-07-01",
            received_date="2026-07-04",
            note="Bản ghi test tự động từ file script ngoài",
            created_by="Hệ thống Test",
            sale_owner="Admin Test"
        )
        print("✅ Thêm bản ghi mới thành công!")
        success = True
    except Exception as e:
        print(f"❌ KHÔNG THỂ THÊM DỮ LIỆU: Thất bại ở tầng cơ sở dữ liệu.\nChi tiết lỗi: {e}")
        print("💡 Gợi ý: Hãy kiểm tra xem bảng 'other_document_tracking' đã được thêm cột 'created_by' và 'sale_owner' chưa.")
        return

    # Nếu thêm thành công thì mới chạy tiếp logic kiểm tra xem có lưu và xóa được không
    if success:
        df_after = OtherDocumentTrackingRepository.get_all()
        print(f"📈 Số lượng dòng sau khi thêm: {len(df_after)} dòng.")
        
        if not df_after.empty and len(df_after) > len(df_before):
            new_record_id = int(df_after.iloc[0]['id'])
            print(f"🔑 Tìm thấy ID của bản ghi mới tạo: {new_record_id}")
            
            print(f"\n🗑️ Đang tiến hành xóa bản ghi test ID {new_record_id} để hoàn trả database...")
            try:
                OtherDocumentTrackingRepository.delete_tracking(new_record_id)
                print("✅ Xóa bản ghi test thành công!")
            except Exception as e:
                print(f"❌ Lỗi khi xóa dữ liệu: {e}")
                return
                
            df_final = OtherDocumentTrackingRepository.get_all()
            print(f"🏁 Số lượng dòng cuối cùng: {len(df_final)}")
            if len(df_before) == len(df_final):
                print("\n🎉 CHÚC MỪNG! REPOSITORY NÀY ĐÃ HOẠT ĐỘNG HOÀN HẢO TRÊN POSTGRESQL!")
            else:
                print("\n⚠️ Số lượng dòng cuối cùng bị lệch so với ban đầu.")
        else:
            print("❌ Bản ghi mới chưa thực sự được ghi vào Database dù không báo lỗi crash.")

if __name__ == "__main__":
    test_repository_logic()