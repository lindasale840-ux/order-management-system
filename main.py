import streamlit as st
import traceback

ENABLE_CHART_PAGE = True

from erp_pages.login_page import (
    show_login_page
)

from erp_pages.dashboard_page import (
    show_dashboard_page
)

from erp_pages.payment_page import (
    show_payment_page
)

from erp_pages.overdue_page import (
    show_overdue_page
)

from erp_pages.finance_page import (
    show_finance_page
)

from erp_pages.notification_page import (
    show_notification_page
)

from erp_pages.chart_customer_page import (
    show_chart_customer_page
)

from erp_pages.logs_page import (
    show_logs_page
)

from erp_pages.user_management_page import (
    show_user_management_page
)

from erp_pages.error_logs_page import (
    show_error_logs_page
)

from erp_pages.error_logs_page import (
    show_error_logs_page
)

from erp_pages.backup_page import (
    show_backup_page
)

from erp_pages.document_tracking_page import (
    show_document_tracking_page
)

from services.sidebar_notification_service import (
    SidebarNotificationService
)

from database.init_db import (
    initialize_database
)

from repositories.error_log_repository import (
    ErrorLogRepository
)


from erp_pages.revenue_management_page import (
    show_revenue_management_page
)

from erp_pages.equipment_tracking_page import (
    show_equipment_tracking_page
)

from services.equipment_tracking_notification_service import (
    EquipmentTrackingNotificationService
)

from erp_pages.historical_import_page import (
    show_historical_import_page
)
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

# =========================
# LOGIN CHECK
# =========================

if "logged_in" not in st.session_state:

    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:

    show_login_page()

    st.stop()

# =========================
# CUSTOM CSS
# =========================

st.markdown("""

<style>

.block-container {
    padding-top: 1rem;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] * {
    color: white;
}

.sidebar-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
}

.notification-card {
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 12px;
    color: white;
    font-weight: 600;
}

.red-card {
    background-color: #dc2626;
}

.orange-card {
    background-color: #ea580c;
}

.blue-card {
    background-color: #2563eb;
}

.green-card {
    background-color: #16a34a;
}

</style>

""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================

st.sidebar.markdown(

    '<div class="sidebar-title">📦 ERP MENU</div>',

    unsafe_allow_html=True
)

st.sidebar.success(

    f"👤 {st.session_state['username']}"
)

st.sidebar.info(

    f"Role: {st.session_state['role']}"
)

# =========================
# MENU BY ROLE
# =========================
alert_summary = (
    SidebarNotificationService
    .get_alert_summary()
)

alert_count = (
    alert_summary["total"]
)

equipment_alert_count = (

    EquipmentTrackingNotificationService
    .get_alert_count()

)

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

        "📝 Logs",

        "👥 User Management",

        "🚨 Error Logs",

        "📥 Historical Import",

        "💾 Backup Database"
    ]

    if ENABLE_CHART_PAGE:

        menu_options.insert(
                5,
                "📈 Analytics Dashboard"
    )
        
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

        "📝 Logs"
    ]        

elif role == "SALE":

    menu_options = [

        "⚠️ Overdue",

        "📑 Finance",

        f"🔔 Notification Center ({alert_count})",

        "📈 Analytics Dashboard",

        "💵 Revenue Management",

        "📝 Logs"
    ]

page = st.sidebar.radio(

    "Navigation",

    menu_options
)

st.sidebar.divider()

st.sidebar.info(
    "Order Management System v3"
)

if alert_count > 0:

    st.sidebar.warning(

        f"⚠️ Total Alerts: {alert_count}"
    )

    if alert_summary["missing_cert"] > 0:

        st.sidebar.write(
            f"📄 Missing Cert: "
            f"{alert_summary['missing_cert']}"
        )

    if alert_summary["payment_overdue"] > 0:

        st.sidebar.write(
            f"💰 Payment Overdue: "
            f"{alert_summary['payment_overdue']}"
        )

    if alert_summary["due_soon"] > 0:

        st.sidebar.write(
            f"📅 Due Soon: "
            f"{alert_summary['due_soon']}"
        )

    if alert_summary["missing_invoice"] > 0:

        st.sidebar.write(
            f"🧾 Missing Invoice: "
            f"{alert_summary['missing_invoice']}"
        )

    if alert_summary["missing_send"] > 0:

        st.sidebar.write(
            f"📨 Missing Send: "
            f"{alert_summary['missing_send']}"
        )

    if alert_summary["pending_return"] > 0:

        st.sidebar.write(
            f"📬 Pending Return: "
            f"{alert_summary['pending_return']}"
        )

# =========================
# LOGOUT
# =========================

st.sidebar.divider()

if st.sidebar.button(

    "🚪 Logout"
):

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

    elif (

        page == "📈 Analytics Dashboard"

        and

        ENABLE_CHART_PAGE

    ):

        show_chart_customer_page()

    elif page == "📨 Document Tracking":

        show_document_tracking_page()    


    elif page.startswith("📦 Equipment Tracking"):

        show_equipment_tracking_page()   

    elif page == "💵 Revenue Management":

        show_revenue_management_page()    

    elif page == "📝 Logs":

        show_logs_page()

    elif page == "👥 User Management":

        show_user_management_page()

    elif page == "🚨 Error Logs":

        show_error_logs_page()

    elif page == "📥 Historical Import":

        show_historical_import_page()    

    elif page == "💾 Backup Database":

        show_backup_page()   

except Exception:

    error_text = traceback.format_exc()

    try:

        ErrorLogRepository.add_error(

            page_name=page,

            error_message=error_text
        )

    except Exception:

        pass

    st.error(

        "Unexpected error occurred. "
        "Error saved to Error Logs."
    )

    with st.expander(

        "Technical Details"
    ):

        st.code(error_text)