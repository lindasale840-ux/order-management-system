import streamlit as st
import traceback

from pages.login_page import (
    show_login_page
)

from pages.dashboard_page import (
    show_dashboard_page
)

from pages.payment_page import (
    show_payment_page
)

from pages.overdue_page import (
    show_overdue_page
)

from pages.finance_page import (
    show_finance_page
)

from pages.notification_page import (
    show_notification_page
)

from pages.chart_customer_page import (
    show_chart_customer_page
)

from pages.logs_page import (
    show_logs_page
)

from pages.user_management_page import (
    show_user_management_page
)

from pages.error_logs_page import (
    show_error_logs_page
)

from database.init_db import (
    initialize_database
)

from repositories.error_log_repository import (
    ErrorLogRepository
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

if st.session_state["role"] == "ADMIN":

    menu_options = [

        "📊 Dashboard",

        "💰 Payment",

        "⚠️ Overdue",

        "📑 Finance",

        "🔔 Notification Center",

        "📈 Chart Customer",

        "📝 Logs",

        "👥 User Management",

        "🚨 Error Logs"
    ]

else:

    menu_options = [

        "⚠️ Overdue",

        "📑 Finance",

        "🔔 Notification Center",

        "📈 Chart Customer",

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

    elif page == "🔔 Notification Center":

        show_notification_page()

    elif page == "📈 Chart Customer":

        show_chart_customer_page()

    elif page == "📝 Logs":

        show_logs_page()

    elif page == "👥 User Management":

        show_user_management_page()

    elif page == "🚨 Error Logs":

        show_error_logs_page()

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