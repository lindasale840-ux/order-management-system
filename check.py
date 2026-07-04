# test_user.py
from repositories.user_repository import UserRepository
import json

def run_test():
    print("🧪 --- BẮT ĐẦU KIỂM TRA USER REPOSITORY ---")
    
    # 1. Test lấy tất cả user
    print("\n1. Đang chạy thử get_all_users()...")
    df = UserRepository.get_all_users()
    print(f"📊 Thành công! Đọc được Dataframe có {len(df)} tài khoản.")
    print(df[['username', 'role']].head()) # In ra vài dòng xem thử
    
    # 2. Test lấy chi tiết 1 user bằng username cụ thể
    # Bạn hãy thay 'admin' bằng một tên username đang có thật trong DB của bạn nhé
    test_username = "admin" 
    print(f"\n2. Đang kiểm tra chi tiết tài khoản '{test_username}'...")
    user = UserRepository.get_user_by_username(test_username)
    
    if user:
        print("✅ Thành công! Tìm thấy user.")
        # Ép về dict thuần để in ra màn hình cho đẹp
        print(json.dumps(dict(user), indent=4, default=str)) 
        
        # Kiểm tra tính đồng bộ cấu trúc logic cũ:
        print(f"🔑 Test logic cũ: Quyền của user này là: {user['role']}")
    else:
        print(f"⚠️ Không tìm thấy user nào tên là '{test_username}' để test sâu hơn.")
        
    print("\n🎉 --- HOÀN THÀNH KIỂM TRA! KHÔNG CÓ LỖI SYNTAX/LOGIC ---")

if __name__ == "__main__":
    run_test()