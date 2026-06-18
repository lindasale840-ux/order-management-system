from datetime import datetime, timedelta
from repositories.user_repository import UserRepository
from utils.password_utils import verify_password

class AuthService:

    @staticmethod
    def login(username, password):
        user = UserRepository.get_user_by_username(username)
        if not user:
            return {"status": "NOT_FOUND", "message": "Invalid username or password"}

        is_admin = str(user["role"]).upper() == "ADMIN"
        login_attempts = user["login_attempts"] if user["login_attempts"] else 0
        locked_until_str = user["locked_until"]

        # 1. KIỂM TRA TRẠNG THÁI KHÓA (Bỏ qua nếu là ADMIN)
        if not is_admin and locked_until_str:
            try:
                locked_until = datetime.fromisoformat(locked_until_str)
                if datetime.now() < locked_until:
                    time_left = locked_until - datetime.now()
                    minutes_left = max(1, int(time_left.total_seconds() / 60))
                    return {
                        "status": "LOCKED", 
                        "message": f"Tài khoản bị khóa! Thử lại sau {minutes_left} phút hoặc báo Admin."
                    }
                else:
                    # Đã qua 30 phút phạt -> Tự động giải phóng trạng thái khóa
                    UserRepository.reset_security_status(username)
                    login_attempts = 0
            except Exception:
                pass

        # 2. XÁC THỰC MẬT KHẨU
        valid_password = verify_password(password, user["password_hash"])

        if valid_password:
            # Thành công -> Xóa hết các vết phạt trước đó
            UserRepository.reset_security_status(username)
            return {
                "status": "SUCCESS",
                "data": {
                    "username": user["username"],
                    "role": user["role"],
                    "sale_owner": user["sale_owner"]
                }
            }
        else:
            # Thất bại -> Xử lý đếm số lần sai
            if is_admin:
                # ĐẶC QUYỀN ADMIN: Sai mật khẩu thoải mái không lo bị khóa tài khoản trêu
                return {"status": "WRONG_PASSWORD", "message": "Mật khẩu Admin không chính xác!"}
            else:
                new_attempts = login_attempts + 1
                UserRepository.update_login_attempts(username, new_attempts)
                
                if new_attempts >= 5:
                    # Tính toán thời gian khóa 30 phút kể từ hiện tại
                    lock_time = datetime.now() + timedelta(minutes=30)
                    UserRepository.lock_user(username, lock_time.isoformat())
                    return {"status": "JUST_LOCKED", "message": "Bạn đã nhập sai 5 lần! Tài khoản bị khóa 30 phút."}
                else:
                    return {
                        "status": "WRONG_PASSWORD", 
                        "message": f"Sai mật khẩu! Bạn còn {5 - new_attempts} lần thử trước khi bị khóa."
                    }