import streamlit as st
import pandas as pd
import plotly.express as px

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


def show_revenue_management_page():

    st.title(
        "💵 Revenue Management"
    )

    # =========================
    # LOAD DATA
    # =========================

    df = (
        FinanceService
        .build_finance_dataframe()
    )

    if df.empty:

        st.warning(
            "No revenue data found"
        )

        return

    # =========================
    # FILTER
    # =========================

    customer_df = (
        OrderRepository
        .get_customers()
    )

    customer_options = [

        "ALL"

    ] + customer_df[
        "customer_name"
    ].tolist()

    selected_customer = st.selectbox(

        "Customer",

        customer_options
    )

    if selected_customer != "ALL":

        df = df[
            df["customer_name"]
            == selected_customer
        ]

    # =========================
    # KPI
    # =========================

    total_revenue = (
        df["total"]
        .fillna(0)
        .sum()
    )

    paid_revenue = (
        df[
            df[
                "payment_status_text"
            ]
            ==
            "Paid"
        ]["total"]
        .fillna(0)
        .sum()
    )

    pending_revenue = (
        df[
            df[
                "payment_status_text"
            ]
            ==
            "Pending"
        ]["total"]
        .fillna(0)
        .sum()
    )

    overdue_revenue = (
        df[
            df[
                "payment_overdue"
            ]
            ==
            "Overdue"
        ]["total"]
        .fillna(0)
        .sum()
    )

    total_commission = (
        df[
            "commission_actual"
        ]
        .fillna(0)
        .sum()
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(

            "Total Revenue",

            f"{total_revenue:,.0f}"
        )

    with col2:

        st.metric(

            "Paid Revenue",

            f"{paid_revenue:,.0f}"
        )

    with col3:

        st.metric(

            "Pending Revenue",

            f"{pending_revenue:,.0f}"
        )

    col4, col5 = st.columns(2)

    with col4:

        st.metric(

            "Overdue Revenue",

            f"{overdue_revenue:,.0f}"
        )

    with col5:

        st.metric(

            "Commission Revenue",

            f"{total_commission:,.0f}"
        )

    st.divider()

    # =========================
    # CHART
    # =========================

    chart_df = (

        df.groupby(
            "customer_name"
        )["total"]

        .sum()

        .reset_index()
    )

    if not chart_df.empty:

        fig = px.bar(

            chart_df,

            x="customer_name",

            y="total",

            title="Revenue By Customer"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

    st.divider()

    # =========================
    # TABLE
    # =========================

    display_df = df[

        [

            "customer_name",

            "order_number",

            "invoice_date",

            "payment_status",

            "payment_overdue",

            "total",

            "commission_percent",

            "commission_actual",

            "note"
        ]

    ].copy()

    render_aggrid(

        display_df,

        height=500,

        page_size=10
    )

    st.divider()

    # =========================
    # EXPORT
    # =========================

    excel_data = dataframe_to_excel({

        "Revenue Report": display_df

    })

    st.download_button(

        label="📥 Export Revenue Excel",

        data=excel_data,

        file_name="revenue_report.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )