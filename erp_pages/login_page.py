import streamlit as st
from services.auth_service import AuthService
from repositories.user_repository import UserRepository

def show_login_page():
    st.markdown("# 🔐 Login")

    with st.form("login_form"):
        username_input = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

    # SỬA LỖI TẠI ĐÂY: Giữ nguyên chữ hoa/thường, chỉ xóa khoảng trắng thừa ở đầu/cuối
    username = username_input.strip() if username_input else ""

    if login_btn:
        if not username or not password:
            st.error("Vui lòng điền đầy đủ Username và Password.")
            return

        result = AuthService.login(username, password)

        if result["status"] == "SUCCESS":
            user_data = result["data"]
            st.session_state["logged_in"] = True
            st.session_state["username"] = user_data["username"]
            st.session_state["role"] = user_data["role"]
            st.session_state["sale_owner"] = user_data["sale_owner"]
            # 👇 THÊM DÒNG NÀY (lấy user_id từ database)
            st.session_state["user_id"] = user_data.get("id")  # hoặc user_data["id"]
            st.success("🎉 Đăng nhập thành công!")
            st.rerun()
        else:
            st.error(result["message"])

    st.write("---")
    
    col1, col2 = st.columns([2, 3])
    with col1:
        forgot_btn = st.button("❓ Quên mật khẩu")
    
    if forgot_btn:
        if not username:
            st.warning("👉 Vui lòng điền Username của bạn vào ô đăng nhập phía trên trước rồi bấm nút này nhé.")
        else:
            user_check = UserRepository.get_user_by_username(username)
            if not user_check:
                st.error(f"❌ Tài khoản '{username}' không tồn tại trên hệ thống! Vui lòng kiểm tra chính xác từng chữ Hoa/Thường.")
            else:
                UserRepository.request_password_reset(username)
                st.info(f"📩 Đã gửi yêu cầu thành công! Hãy báo Admin cấp lại mật khẩu cho nick `{username}`.")