import streamlit as st
import traceback

# === CHÈN THÊM IMPORT NÀY ĐỂ ĐẾM SỐ USER ONLINE ===
from streamlit.runtime import get_instance

ENABLE_CHART_PAGE = True

from erp_pages.login_page import show_login_page
from erp_pages.dashboard_page import show_dashboard_page
from erp_pages.payment_page import show_payment_page
from erp_pages.overdue_page import show_overdue_page
from erp_pages.finance_page import show_finance_page
from erp_pages.notification_page import show_notification_page
from erp_pages.chart_customer_page import show_chart_customer_page
from erp_pages.logs_page import show_logs_page
from erp_pages.user_management_page import show_user_management_page
from erp_pages.error_logs_page import show_error_logs_page
from erp_pages.backup_page import show_backup_page
from erp_pages.document_tracking_page import show_document_tracking_page
from services.sidebar_notification_service import SidebarNotificationService
from database.init_db import initialize_database
from repositories.error_log_repository import ErrorLogRepository
from erp_pages.revenue_management_page import show_revenue_management_page
from erp_pages.equipment_tracking_page import show_equipment_tracking_page
from services.equipment_tracking_notification_service import EquipmentTrackingNotificationService
from erp_pages.historical_import_page import show_historical_import_page
from erp_pages.trash_bin_page import show_trash_bin_page
from erp_pages.ownership_transfer_page import show_ownership_transfer_page
from erp_pages.notes_page import show_notes_page

# =========================
# INIT DATABASE
# =========================
initialize_database()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Order Management ERP",
    page_icon="📊",
    layout="wide"
)

# ========================================================
# KST: 🔒 KIỂM TRA GIỚI HẠN SỐ LƯỢNG NGƯỜI TRUY CẬP (MAX 4)
# ========================================================
try:
    runtime = get_instance()
    if runtime:
        # Lấy danh sách toàn bộ các tab trình duyệt đang kết nối đến ERP
        active_sessions = runtime._session_mgr.list_active_sessions()
        
        # Nếu đã có từ 4 người đang kết nối TRỞ LÊN, và trình duyệt hiện tại CHƯA đăng nhập
        if len(active_sessions) > 4 and not st.session_state.get("logged_in", False):
            st.markdown("""
                <div style="text-align: center; margin-top: 100px; font-family: 'Inter', sans-serif;">
                    <h1 style="color: #ef4444; font-size: 50px;">⚠️ HỆ THỐNG QUÁ TẢI</h1>
                    <h3 style="color: #334155;">Hiện tại đã đạt giới hạn tối đa 4 người truy cập cùng lúc.</h3>
                    <p style="color: #64748b; font-size: 16px;">Vui lòng chờ đồng nghiệp thoát phiên làm việc hoặc quay lại sau ít phút.</p>
                    <hr style="width: 30%; margin: 20px auto; border-color: #cbd5e1;"/>
                    <p style="color: #94a3b8; font-size: 13px;">Hệ thống sẽ tự động mở cổng kết nối khi có vị trí trống.</p>
                </div>
            """, unsafe_allow_html=True)
            st.stop()  # Ngắt toàn bộ code phía dưới, không cho hiện màn hình Login
except Exception as e:
    pass # Nếu phát sinh lỗi đọc bộ nhớ runtime, bỏ qua để tránh sập app ERP

# =========================
# LOGIN CHECK
# =========================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    show_login_page()
    st.stop()
    
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "📊 Dashboard"    

# =========================
# ULTRA PREMIUM CUSTOM CSS
# =========================
st.markdown("""
<style>
/* 1. Nhúng Font chữ cao cấp Inter từ Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Áp dụng font mới cho toàn bộ ứng dụng */
html, body, [data-testid="stAppViewContainer"], .main * {
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* Đổi màu nền chính của ứng dụng sang màu xám dịu mắt, cao cấp */
[data-testid="stAppViewContainer"] {
    background-color: #f8fafc !important;
}

/* Reset khoảng cách container chính */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
    background-color: #f8fafc !important;
}

/* 2. Sidebar Dark Slate & Navy Blend với hiệu ứng chuyển màu nền nhẹ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
    border-right: 1px solid #334155;
    box-shadow: 4px 0px 20px rgba(0, 0, 0, 0.3);
}

section[data-testid="stSidebar"] * {
    color: #f1f5f9 !important;
}

/* 3. Hiệu ứng chữ tiêu đề Menu phát sáng nhẹ (Glow Effect) */
.sidebar-title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 25px;
    color: #38bdf8 !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
    border-bottom: 1px solid #334155;
    padding-bottom: 12px;
}

/* 4. Thẻ Profile người dùng đổ bóng vật lý (Box Shadow) & Bo góc mượt */
.user-profile-box {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(8px);
    padding: 14px 16px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease;
}
.user-profile-box:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.4);
    box-shadow: 0 6px 16px rgba(56, 189, 248, 0.1);
}

.user-profile-box .user-name {
    font-weight: 600;
    font-size: 15px;
    color: #f8fafc;
}
.user-profile-box .user-role {
    font-size: 12px;
    color: #38bdf8;
    font-weight: 500;
    margin-top: 4px;
}

/* 5. Hiệu ứng Animation lướt mượt cho các nút Radio Menu mặc định của Streamlit */
div[data-testid="stSidebarUserContent"] div[role="radiogroup"] label {
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 4px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
div[data-testid="stSidebarUserContent"] div[role="radiogroup"] label:hover {
    background-color: rgba(56, 189, 248, 0.1) !important;
    padding-left: 18px !important;
    color: #38bdf8 !important;
}

/* 6. Thẻ Cảnh báo (Alert Cards) dạng Glassmorphism mềm mại */
.notification-card {
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: #ffffff !important;
    font-weight: 600;
    font-size: 13px;
    border-left: 4px solid rgba(0, 0, 0, 0.2);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    animation: fadeIn 0.5s ease-in-out;
}
.red-card { background: linear-gradient(135deg, #ef4444, #dc2626); }
.orange-card { background: linear-gradient(135deg, #f97316, #ea580c); }
.blue-card { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.green-card { background: linear-gradient(135deg, #10b981, #16a34a); }

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}

/* 7. Tinh chỉnh các nút bấm và trạng thái CẤM (Disabled/Validation) */
div.stButton > button {
    border-radius: 8px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(255, 255, 255, 0.05) !important;
    transition: all 0.3s ease !important;
    font-weight: 500 !important;
}
div.stButton > button:hover {
    background: #ef4444 !important;
    color: white !important;
    border-color: #ef4444 !important;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.4) !important;
    transform: translateY(-1px);
}

/* Hiệu ứng hiển thị trực quan cho các nút bấm bị chặn/cấm đi kèm thuộc tính disabled trong Streamlit */
button:disabled {
    cursor: not-allowed !important;
    opacity: 0.5 !important;
    background-color: #cbd5e1 !important;
    color: #64748b !important;
    border-color: #cbd5e1 !important;
    box-shadow: none !important;
    transform: none !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR HEADER
# =========================
st.sidebar.markdown(
    '<div class="sidebar-title">📦 ERP ENTERPRISE</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown(f"""
<div class="user-profile-box">
    <div class="user-name">👤 {st.session_state['username']}</div>
    <div class="user-role">Role: {st.session_state['role']}</div>
</div>
""", unsafe_allow_html=True)

# Lấy dữ liệu alert từ Service
alert_summary = SidebarNotificationService.get_alert_summary()
alert_count = alert_summary["total"]
equipment_alert_count = EquipmentTrackingNotificationService.get_alert_count()

# ========================================================
# ĐÃ DI CHUYỂN: KHU VỰC THÔNG BÁO TỔNG HỢP LÊN NGAY DƯỚI PROFILE
# ========================================================
if alert_count > 0:
    with st.sidebar.expander(f"🔔 Quick Notification Center ({alert_count})", expanded=False):
        st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
        
        alert_items = [
            ("missing_cert", "📄 Missing Cert", "#ef4444"),
            ("payment_overdue", "💰 Payment Overdue", "#f97316"),
            ("due_soon", "📅 Due Soon", "#3b82f6"),
            ("missing_invoice", "🧾 Missing Invoice", "#dc2626"),
            ("missing_send", "📨 Missing Send", "#ea580c"),
            ("pending_return", "📬 Pending Return", "#2563eb")
        ]
        
        for key, label, color in alert_items:
            count = alert_summary.get(key, 0)
            if count > 0:
                st.markdown(f"""
                <div style="
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    padding: 8px 10px; 
                    background: rgba(255,255,255,0.05); 
                    border-radius: 6px; 
                    margin-bottom: 6px;
                    border-left: 3px solid {color};
                ">
                    <span style="font-size: 13px; color: #e2e8f0;">{label}</span>
                    <span style="
                        background: {color}; 
                        color: white; 
                        font-size: 11px; 
                        font-weight: bold; 
                        padding: 2px 8px; 
                        border-radius: 10px;
                    ">{count}</span>
                </div>
                """, unsafe_allow_html=True)

st.sidebar.divider() # Vạch ngăn cách giữa Thông báo và Menu hệ thống

# =========================
# NOTIFICATION BADGE (Notes)  <--- THÊM PHẦN NÀY VÀO ĐÂY
# =========================
from components.note_components import render_notification_badge

# Hiển thị badge chuông ở góc phải màn hình
render_notification_badge()
# =========================
# MENU BY ROLE
# =========================
role = st.session_state["role"]

if role == "ADMIN":
    menu_options = [
        "📊 Dashboard",
        "💰 Payment",
        "⚠️ Overdue",
        "📑 Finance",
        f"🔔 Notification Center ({alert_count})",
        "📨 Document Tracking",
        f"📦 Equipment Tracking ({equipment_alert_count})",
        "💵 Revenue Management",
        "📝 Notes Management",
        "📝 Logs",
        "👥 User Management",
        "🔄 Ownership Transfer",
        "🗑 Trash Bin",
        "🚨 Error Logs",
        "📥 Historical Import",
        "💾 Backup Database"
    ]
    if ENABLE_CHART_PAGE:
        menu_options.insert(5, "📈 Analytics Dashboard")
        
elif role == "ASSISTANT":
    menu_options = [
        "📊 Dashboard",
        "💰 Payment",
        "⚠️ Overdue",
        "📑 Finance",
        f"🔔 Notification Center ({alert_count})",
        "📨 Document Tracking",
        f"📦 Equipment Tracking ({equipment_alert_count})",
        "💵 Revenue Management",
        "📝 Notes Management",
        "📝 Logs"
    ]        

elif role == "SALE":
    menu_options = [
        "⚠️ Overdue",
        "📑 Finance",
        f"🔔 Notification Center ({alert_count})",
        "📈 Analytics Dashboard",
        "💵 Revenue Management",
        "📝 Notes Management",
        "📝 Logs"
    ]

try:
    default_index = menu_options.index(st.session_state["current_page"])
except ValueError:
    default_index = 0

page = st.sidebar.radio(
    "Navigation System",
    menu_options,
    index=default_index,
    key="navigation_radio"
)

st.session_state["current_page"] = page

# =========================
# LOGOUT
# =========================
st.sidebar.divider()
if st.sidebar.button("🚪 Leave Session", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# =========================
# ROUTING + ERROR CAPTURE
# =========================
try:
    if page == "📊 Dashboard":
        show_dashboard_page()
    elif page == "💰 Payment":
        show_payment_page()
    elif page == "⚠️ Overdue":
        show_overdue_page()
    elif page == "📑 Finance":
        show_finance_page()
    elif page.startswith("🔔 Notification Center"):
        show_notification_page()
    elif page == "📈 Analytics Dashboard" and ENABLE_CHART_PAGE:
        show_chart_customer_page()
    elif page == "📨 Document Tracking":
        show_document_tracking_page()    
    elif page.startswith("📦 Equipment Tracking"):
        show_equipment_tracking_page()   
    elif page == "💵 Revenue Management":
        show_revenue_management_page()  
    elif page == "📝 Notes Management":  # <--- THÊM DÒNG NÀY
        show_notes_page()      
    elif page == "📝 Logs":
        show_logs_page()
    elif page == "👥 User Management":
        show_user_management_page()
    elif page == "🔄 Ownership Transfer":
        show_ownership_transfer_page()    
    elif page == "🗑 Trash Bin":
        show_trash_bin_page()
    elif page == "🚨 Error Logs":
        show_error_logs_page()
    elif page == "📥 Historical Import":
        show_historical_import_page()    
    elif page == "💾 Backup Database":
        show_backup_page()   
except Exception:
    error_text = traceback.format_exc()
    try:
        ErrorLogRepository.add_error(page_name=page, error_message=error_text)
    except Exception:
        pass
    st.error("Unexpected error occurred. Error saved to Error Logs.")
    with st.expander("Technical Details"):
        st.code(error_text)