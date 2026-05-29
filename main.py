import streamlit as st

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

from database.init_db import (
    init_database
)

# =========================
# INIT DATABASE
# =========================

init_database()

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(

    page_title="Order Management ERP",

    page_icon="📊",

    layout="wide"
)

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

page = st.sidebar.radio(

    "Navigation",

    [

        "📊 Dashboard",

        "💰 Payment",

        "⚠️ Overdue",

        "📑 Finance",

        "🔔 Notification Center",

        "📈 Chart Customer",

        "📝 Logs"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    "Order Management System v3"
)

# =========================
# ROUTING
# =========================

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