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

def show_chart_customer_page():


    st.title(
        "📈 Analytics Dashboard"
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
            "No data found"
        )

        return

    # =========================
    # CUSTOMER FILTER
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
    # DATE FORMAT
    # =========================

    df["invoice_date"] = pd.to_datetime(

        df["invoice_date"],

        errors="coerce"
    )

    # =========================
    # TABS
    # =========================

    tab1, tab2, tab3, tab4 = st.tabs([

        "📊 Revenue Trend",

        "🏆 Customer Analytics",

        "💰 Payment Analytics",

        "📜 Certificate Analytics"
    ])

    # ==================================================
    # TAB 1
    # ==================================================

    with tab1:

        st.subheader(
            "Revenue Trend By Month"
        )

        revenue_df = df.dropna(
            subset=["invoice_date"]
        ).copy()

        if not revenue_df.empty:

            revenue_df["year_month"] = (

                revenue_df["invoice_date"]

                .dt.strftime("%Y-%m")
            )

            monthly_revenue = (

                revenue_df

                .groupby(
                    "year_month"
                )["total"]

                .sum()

                .reset_index()
            )

            fig = px.line(

                monthly_revenue,

                x="year_month",

                y="total",

                markers=True,

                title="Monthly Revenue Trend"
            )

            st.plotly_chart(

                fig,

                use_container_width=True
            )

            render_aggrid(

                monthly_revenue,

                height=300,

                page_size=12
            )

        st.divider()

        st.subheader(
            "Monthly Paid Revenue"
        )

        paid_df = revenue_df[
            revenue_df[
                "payment_status_text"
            ]
            ==
            "Paid"
        ]

        if not paid_df.empty:

            paid_chart = (

                paid_df

                .groupby(
                    "year_month"
                )["total"]

                .sum()

                .reset_index()
            )

            paid_chart["year_month"] = (
                paid_chart["year_month"]
                .astype(str)
            )

            
            fig = px.bar(

                paid_chart,

                x="year_month",

                y="total",

                title="Paid Revenue By Month"
            )

            fig.update_xaxes(
                type="category"
            )

            st.plotly_chart(

                fig,

                use_container_width=True
            )

            

    # ==================================================
    # TAB 2
    # ==================================================

    with tab2:

        st.subheader(
            "Revenue By Customer"
        )

        customer_chart = (

            df.groupby(
                "customer_name"
            )["total"]

            .sum()

            .reset_index()

            .sort_values(
                "total",
                ascending=False
            )
        )

        fig = px.bar(

            customer_chart,

            x="customer_name",

            y="total",

            title="Revenue By Customer"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

        st.subheader(
            "Top 10 Customers"
        )

        top10 = customer_chart.head(10)

        render_aggrid(

            top10,

            height=350,

            page_size=10
        )

    # ==================================================
    # TAB 3
    # ==================================================

    with tab3:

        st.subheader(
            "Payment Status Distribution"
        )

        payment_summary = (

            df[
                "payment_status_text"
            ]

            .value_counts()

            .reset_index()
        )

        payment_summary.columns = [

            "status",

            "count"
        ]

        fig = px.pie(

            payment_summary,

            names="status",

            values="count",

            title="Payment Status"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

        st.divider()

        st.subheader(
            "Overdue Analysis"
        )

        overdue_df = (

            df[
                "payment_overdue"
            ]

            .value_counts()

            .reset_index()
        )

        overdue_df.columns = [

            "status",

            "count"
        ]

        fig = px.bar(

            overdue_df,

            x="status",

            y="count",

            title="Overdue Status"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

    # ==================================================
    # TAB 4
    # ==================================================

    with tab4:

        st.subheader(
            "Certificate Workflow Status"
        )

        cert_df = (

            df[
                "cert_workflow_status"
            ]

            .value_counts()

            .reset_index()
        )

        cert_df.columns = [

            "status",

            "count"
        ]

        fig = px.pie(

            cert_df,

            names="status",

            values="count",

            title="Certificate Workflow"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

        st.divider()

        st.subheader(
            "Calibration Due Soon"
        )

        due_soon_df = (

            df[
                "cert_due_soon"
            ]

            .value_counts()

            .reset_index()
        )

        due_soon_df.columns = [

            "status",

            "count"
        ]

        fig = px.bar(

            due_soon_df,

            x="status",

            y="count",

            title="Calibration Due Soon"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

        st.divider()

        st.subheader(
            "Calibration Overdue"
        )

        overdue_cert_df = (

            df[
                "cert_overdue"
            ]

            .value_counts()

            .reset_index()
        )

        overdue_cert_df.columns = [

            "status",

            "count"
        ]

        fig = px.bar(

            overdue_cert_df,

            x="status",

            y="count",

            title="Calibration Overdue"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

