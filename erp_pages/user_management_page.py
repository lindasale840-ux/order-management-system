import streamlit as st
from repositories.user_repository import UserRepository
from utils.password_utils import hash_password
from utils.auth_guard import require_admin
from repositories.assistant_sale_repository import (
    AssistantSaleRepository
)

def show_user_management_page():
    require_admin()
    
    st.title("👥 User Management")

    users_df = UserRepository.get_all_users()
    user_list = users_df["username"].tolist() if not users_df.empty else []
    
    # =========================================================
    # PHẦN 1: BẢNG THEO DÕI YÊU CẦU CẤP LẠI MẬT KHẨU & KHÓA (CỦA USER THƯỜNG)
    # =========================================================
    st.subheader("⚠️ Security Alerts & Requests")
    
    active_alerts = False
    for _, u in users_df.iterrows():
        uname = u["username"]
        role = str(u["role"]).upper()
        
        # Bỏ qua tài khoản ADMIN ở khu vực cảnh báo bị khóa
        if role == "ADMIN":
            continue
            
        is_locked = bool(u["locked_until"])
        is_requested = u["reset_requested"] == 1
        
        if is_locked or is_requested:
            active_alerts = True
            status_tags = []
            if is_locked: status_tags.append("🔴 ĐANG BỊ KHÓA")
            if is_requested: status_tags.append("🟡 YÊU CẦU ĐỔI MẬT KHẨU")
            
            with st.expander(f"👤 {uname} ({role}) - {' | '.join(status_tags)}"):
                if is_locked:
                    st.write(f"Thời gian khóa đến: `{u['locked_until']}`")
                    if st.button(f"🔓 Mở khóa khẩn cấp nick {uname}", key=f"unlock_{uname}"):
                        UserRepository.reset_security_status(uname)
                        st.success(f"Đã kích hoạt lại tài khoản {uname}!")
                        st.rerun()
                        
                if is_requested:
                    new_pass = st.text_input(f"Nhập mật khẩu mới cho {uname}", type="password", key=f"newpass_{uname}")
                    if st.button(f"💾 Cấp mật khẩu mới cho {uname}", key=f"save_{uname}"):
                        if not new_pass:
                            st.error("Chưa nhập mật khẩu mới")
                        else:
                            UserRepository.update_password(uname, hash_password(new_pass))
                            st.success(f"Đã đổi mật khẩu mới cho nick {uname} thành công!")
                            st.rerun()

    if not active_alerts:
        st.success("✅ Trạng thái an toàn. Không có tài khoản nhân viên nào bị khóa hoặc yêu cầu reset.")

    st.divider()

    # =========================================================
    # PHẦN MỚI: 🔒 CHỦ ĐỘNG CẬP NHẬT MẬT KHẨU (CHO ADMIN & USER)
    # =========================================================
    st.subheader("🔒 Update User Password")
    if user_list:
        with st.form("update_password_form"):
            selected_user_to_update = st.selectbox(
                "Select User to change password", 
                user_list,
                # Tự động trỏ sẵn vào tên của admin đang đăng nhập để tiện đổi mật khẩu cho chính mình
                index=user_list.index(st.session_state["username"]) if st.session_state["username"] in user_list else 0
            )
            update_pwd = st.text_input("Enter New Password", type="password")
            confirm_update_pwd = st.text_input("Confirm New Password", type="password")
            
            submit_update = st.form_submit_button("Update Password")
            
        if submit_update:
            if not update_pwd:
                st.error("❌ Please enter a new password.")
            elif update_pwd != confirm_update_pwd:
                st.error("❌ Passwords do not match! Please check again.")
            else:
                # Mã hóa mật khẩu và lưu xuống cơ sở dữ liệu
                UserRepository.update_password(selected_user_to_update, hash_password(update_pwd))
                st.success(f"🎉 Successfully updated password for user `{selected_user_to_update}`!")
                import time
                time.sleep(1)
                st.rerun()
    else:
        st.info("No users available to update password.")

    st.divider()

    # =========================================================
    # PHẦN 2: CHỨC NĂNG TẠO USER GỐC (ĐÃ THÊM ROLE ACCOUNTANT)
    # =========================================================
    st.subheader("Create User")
    username = st.text_input("Username", key="create_uname")
    password = st.text_input("Password", type="password", key="create_pwd")
    
    # BƯỚC 1: Thêm ACCOUNTANT vào danh sách lựa chọn
    role = st.selectbox("Role", ["ADMIN", "SALE", "ASSISTANT", "ACCOUNTANT"])
    sale_owner = st.text_input("Sale Owner")

    if st.button("Create User"):
        if not username:
            st.error("Username required")
        elif not password:
            st.error("Password required")
        else:
            clean_username = username.strip()
            existing = UserRepository.get_user_by_username(clean_username)
            if existing:
                st.error("User already exists")
            else:
                # BƯỚC 2: Định nghĩa phân quyền tự động cho từng Role
                if role == "ADMIN":
                    final_sale_owner = "ALL"
                elif role == "ACCOUNTANT":
                    # Kế toán sẽ giữ nhãn riêng biệt, né hoàn toàn luồng xử lý của SALE
                    final_sale_owner = "ACCOUNTANT"
                elif role == "SALE":
                    final_sale_owner = (
                        sale_owner.strip()
                        if sale_owner.strip()
                        else clean_username
                    )
                else:
                    final_sale_owner = sale_owner

                UserRepository.create_user(clean_username, hash_password(password), role, final_sale_owner)
                st.success(f"User with role {role} created successfully!")
                st.rerun()

    st.divider()
    st.subheader("Existing Users")
    st.dataframe(users_df, use_container_width=True)
    
    st.divider()
    st.subheader("🤝 Assistant - Sale Mapping")
    
    assistant_df = users_df[
    users_df["role"] == "ASSISTANT"
    ]

    assistant_list = (
        assistant_df["username"]
        .tolist()
    )
    
    sale_list = (
        users_df["sale_owner"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    sale_list.sort()
    
    if assistant_list:

        selected_assistant = st.selectbox(
            "Select Assistant",
            assistant_list
        )

        current_sales = (
            AssistantSaleRepository
            .get_sales_by_assistant(
                selected_assistant
            )
        )

        selected_sales = st.multiselect(
            "Supported Sales",
            options=sale_list,
            default=current_sales
        )

        if st.button(
            "💾 Save Mapping"
        ):

            AssistantSaleRepository\
                .delete_by_assistant(
                    selected_assistant
                )

            for sale in selected_sales:

                AssistantSaleRepository\
                    .add_mapping(
                        selected_assistant,
                        sale
                    )

            st.success(
                "Mapping saved."
            )

            st.rerun()
            
    mapping_df = (
        AssistantSaleRepository
        .get_all()
    )

    if not mapping_df.empty:
        st.dataframe(
            mapping_df,
            use_container_width=True
        )        

    st.divider()
    st.subheader("Delete User")
    if user_list:
        delete_user = st.selectbox("Select User", user_list, key="del_user_select")
        if st.button("Delete User"):
            if delete_user == "admin":
                st.error("Cannot delete admin")
            else:
                UserRepository.delete_user(delete_user)
                st.success("User deleted")
                st.rerun()