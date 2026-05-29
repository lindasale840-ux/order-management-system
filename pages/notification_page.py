import streamlit as st

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)


def show_notification_page():

    st.title(
        "🔔 Notification Center"
    )

    customer_df = (
        OrderRepository.get_customers()
    )

    customer_options = [
        "ALL"
    ] + customer_df[
        "customer_name"
    ].tolist()

    selected_customer = st.selectbox(
        "Filter Customer",
        customer_options
    )

    df = (
        FinanceService
        .build_finance_dataframe()
    )

    if selected_customer != "ALL":

        df = df[
            df["customer_name"]
            == selected_customer
        ]

    # =========================
    # MISSING CERT
    # =========================

    missing_cert_df = df[
        df["cert_workflow_status"]
        == "Missing Cert"
    ]

    st.subheader(
        "📄 Missing Certificate"
    )

    if missing_cert_df.empty:

        st.success(
            "No missing certificate"
        )

    else:

        for _, row in (
            missing_cert_df.iterrows()
        ):

            st.markdown(f"""

            <div class="notification-card red-card">

            ❌ Customer:
            {row['customer_name']}

            <br>

            Order:
            {row['order_number']}

            <br>

            Measurement Date:
            {row['measurement_date']}

            </div>

            """, unsafe_allow_html=True)

    # =========================
    # PAYMENT OVERDUE
    # =========================

    payment_overdue_df = df[
        df["payment_overdue"]
        == "Overdue"
    ]

    st.subheader(
        "💰 Payment Overdue"
    )

    if payment_overdue_df.empty:

        st.success(
            "No overdue payment"
        )

    else:

        for _, row in (
            payment_overdue_df.iterrows()
        ):

            st.markdown(f"""

            <div class="notification-card orange-card">

            ⚠️ Customer:
            {row['customer_name']}

            <br>

            Order:
            {row['order_number']}

            <br>

            Invoice Date:
            {row['invoice_date']}

            </div>

            """, unsafe_allow_html=True)

    # =========================
    # DUE SOON
    # =========================

    due_soon_df = df[
        df["cert_due_soon"]
        == "Due Soon"
    ]

    st.subheader(
        "📅 Calibration Due Soon"
    )

    if due_soon_df.empty:

        st.success(
            "No due soon"
        )

    else:

        for _, row in (
            due_soon_df.iterrows()
        ):

            st.markdown(f"""

            <div class="notification-card blue-card">

            📌 Customer:
            {row['customer_name']}

            <br>

            Order:
            {row['order_number']}

            <br>

            Measurement Date:
            {row['measurement_date']}

            </div>

            """, unsafe_allow_html=True)

    # =========================
    # MISSING INVOICE
    # =========================

    missing_invoice_df = df[
        df["order_status"]
        == "Missing Invoice"
    ]

    st.subheader(
        "🧾 Missing Invoice"
    )

    if missing_invoice_df.empty:

        st.success(
            "No missing invoice"
        )

    else:

        for _, row in (
            missing_invoice_df.iterrows()
        ):

            st.markdown(f"""

            <div class="notification-card green-card">

            📥 Customer:
            {row['customer_name']}

            <br>

            Order:
            {row['order_number']}

            <br>

            Cert Date:
            {row['cert_status']}

            </div>

            """, unsafe_allow_html=True)