import streamlit as st

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)

from components.aggrid_table import (
    render_aggrid
)

from utils.excel_export import (
    dataframe_to_excel
)


def export_button(
    df,
    filename
):

    excel_data = dataframe_to_excel({

        "Data": df

    })

    st.download_button(

        label="📥 Export Excel",

        data=excel_data,

        file_name=filename,

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
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

            ==

            selected_customer

        ]

    missing_cert_df = df[

        df["cert_workflow_status"]

        ==

        "Missing Cert"

    ]

    payment_overdue_df = df[

        df["payment_overdue"]

        ==

        "Overdue"

    ]

    due_soon_df = df[

        df["cert_due_soon"]

        ==

        "Due Soon"

    ]

    missing_invoice_df = df[

        df["order_status"]

        ==

        "Missing Invoice"

    ]

    # =========================
    # KPI SUMMARY
    # =========================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(

            "📄 Missing Cert",

            len(missing_cert_df)
        )

    with col2:

        st.metric(

            "💰 Payment Overdue",

            len(payment_overdue_df)
        )

    with col3:

        st.metric(

            "📅 Due Soon",

            len(due_soon_df)
        )

    with col4:

        st.metric(

            "🧾 Missing Invoice",

            len(missing_invoice_df)
        )

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([

        f"📄 Missing Cert ({len(missing_cert_df)})",

        f"💰 Payment Overdue ({len(payment_overdue_df)})",

        f"📅 Due Soon ({len(due_soon_df)})",

        f"🧾 Missing Invoice ({len(missing_invoice_df)})"

    ])

    # =========================
    # TAB 1
    # =========================

    with tab1:

        st.metric(

            "Missing Certificate",

            len(missing_cert_df)
        )

        if missing_cert_df.empty:

            st.success(
                "No missing certificate"
            )

        else:

            render_aggrid(

                missing_cert_df,

                height=500,

                page_size=10
            )

            export_button(

                missing_cert_df,

                "missing_certificate.xlsx"
            )

    # =========================
    # TAB 2
    # =========================

    with tab2:

        st.metric(

            "Payment Overdue",

            len(payment_overdue_df)
        )

        if payment_overdue_df.empty:

            st.success(
                "No overdue payment"
            )

        else:

            render_aggrid(

                payment_overdue_df,

                height=500,

                page_size=10
            )

            export_button(

                payment_overdue_df,

                "payment_overdue.xlsx"
            )

    # =========================
    # TAB 3
    # =========================

    with tab3:

        st.metric(

            "Calibration Due Soon",

            len(due_soon_df)
        )

        if due_soon_df.empty:

            st.success(
                "No due soon"
            )

        else:

            render_aggrid(

                due_soon_df,

                height=500,

                page_size=10
            )

            export_button(

                due_soon_df,

                "calibration_due_soon.xlsx"
            )

    # =========================
    # TAB 4
    # =========================

    with tab4:

        st.metric(

            "Missing Invoice",

            len(missing_invoice_df)
        )

        if missing_invoice_df.empty:

            st.success(
                "No missing invoice"
            )

        else:

            render_aggrid(

                missing_invoice_df,

                height=500,

                page_size=10
            )

            export_button(

                missing_invoice_df,

                "missing_invoice.xlsx"
            )