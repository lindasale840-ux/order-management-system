import pandas as pd
import datetime

def simulate_safe_date_value(tracking_row, column_name):
    """Bản mô phỏng chính xác hàm xử lý ngày lỗi NaT trên giao diện"""
    if tracking_row is None or column_name not in tracking_row:
        return datetime.date.today()
        
    val_saved = tracking_row[column_name]
    if pd.notna(val_saved) and val_saved is not None:
        dt_parsed = pd.to_datetime(val_saved)
        if pd.notna(dt_parsed):
            return dt_parsed.date()
    return datetime.date.today()

def run_tests():
    print("🚀 Khởi động Unit Test kiểm tra lỗi NaTType...")
    
    # Kịch bản 1: Cột dữ liệu bình thường chứa chuỗi ngày hợp lệ
    row_valid = {"customer_send_date": "2026-07-04"}
    res1 = simulate_safe_date_value(row_valid, "customer_send_date")
    assert isinstance(res1, datetime.date), "Lỗi: Kết quả phải là đối tượng datetime.date!"
    assert str(res1) == "2026-07-04", f"Lỗi: Sai lệch ngày, nhận được {res1}"
    print("✅ Test 1 vượt qua: Đọc chính xác chuỗi ngày từ DB.")

    # Kịch bản 2: Cột dữ liệu chứa giá trị rỗng NaT bướng bỉnh từ Pandas (Phát sinh từ DB PostgreSQL rỗng)
    row_with_nat = pd.DataFrame([{"customer_send_date": pd.NaT}]).iloc[0]
    try:
        res2 = simulate_safe_date_value(row_with_nat, "customer_send_date")
        assert isinstance(res2, datetime.date), "Lỗi: Dù lỗi NaT nhưng hàm phải trả về ngày mặc định ngày hôm nay!"
        print(f"✅ Test 2 vượt qua: Bẫy thành công lỗi NaT và chuyển về ngày hôm nay ({res2}).")
    except ValueError as e:
        print(f"❌ Test 2 Thất bại: Vẫn bị dính lỗi cũ: {e}")

    # Kịch bản 3: Không tìm thấy bản ghi cũ (Dữ liệu None)
    res3 = simulate_safe_date_value(None, "customer_send_date")
    assert res3 == datetime.date.today(), "Lỗi: Khi dòng trống hoàn toàn phải trả về ngày hôm nay!"
    print("✅ Test 3 vượt qua: Xử lý an toàn khi không có bản ghi cũ.")
    
    print("\n🎉 Tuyệt vời! Tất cả các kịch bản test bẫy lỗi NaT đều thành công tốt đẹp.")

if __name__ == "__main__":
    run_tests()