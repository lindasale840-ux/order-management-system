import streamlit as st
import pandas as pd
import plotly.express as px

from services.finance_service import (
FinanceService
)

from repositories.order_repository import (
OrderRepository
)

from repositories.external_expense_repository import (
ExternalExpenseRepository
)

from services.external_expense_service import (
ExternalExpenseService
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
    # YEAR / MONTH FILTER
    # =========================

    df["invoice_date"] = pd.to_datetime(

        df["invoice_date"],

        errors="coerce"
    )

    available_years = sorted(

        df["invoice_date"]
        .dropna()
        .dt.year
        .unique()
        .tolist(),

        reverse=True
    )

    if available_years:

        year_options = [

            "ALL"

        ] + available_years

    else:

        year_options = ["ALL"]

    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:

        selected_year = st.selectbox(

            "Year",

            year_options
        )

    with col_filter2:

        selected_month = st.selectbox(

            "Month",

            [

                "ALL",

                1, 2, 3, 4, 5, 6,

                7, 8, 9, 10, 11, 12

            ]
        )

    if selected_year != "ALL":

        df = df[

            df["invoice_date"]
            .dt.year

            ==

            selected_year
        ]

    if selected_month != "ALL":

        df = df[

            df["invoice_date"]
            .dt.month

            ==

            selected_month
        ]

    # =========================
    # EXTERNAL EXPENSE INPUT
    # =========================

    st.divider()

    st.subheader(
        "💸 External Expense"
    )

    col_exp1, col_exp2, col_exp3 = (
        st.columns(3)
    )

    with col_exp1:

        expense_date = st.date_input(
            "Expense Date"
        )

    with col_exp2:

        expense_amount = st.number_input(

            "Amount",

            min_value=0.0,

            value=0.0
        )

    with col_exp3:

        expense_note = st.text_input(
            "Note"
        )

    if st.button(
        "Add Expense"
    ):

        if expense_amount <= 0:

            st.error(
                "Amount must > 0"
            )

        else:

            ExternalExpenseService.add_expense(

                expense_date,

                expense_amount,

                expense_note
            )

            st.success(
                "Expense added"
            )

            st.rerun()

    # =========================
    # LOAD EXPENSE DATA
    # =========================

    expense_df = (
        ExternalExpenseRepository
        .get_all_expenses()
    )

    if not expense_df.empty:

        expense_df["expense_date"] = (
            pd.to_datetime(
                expense_df["expense_date"],
                errors="coerce"
            )
        )

        if selected_year != "ALL":

            expense_df = expense_df[

                expense_df[
                    "expense_date"
                ]
                .dt.year

                ==

                selected_year
            ]

        if selected_month != "ALL":

            expense_df = expense_df[

                expense_df[
                    "expense_date"
                ]
                .dt.month

                ==

                selected_month
            ]

    # =========================
    # KPI
    # =========================

    # =========================
    # KPI
    # =========================

    calibration_revenue = (
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

    external_revenue = (

        expense_df["amount"]

        .fillna(0)

        .sum()

        if not expense_df.empty

        else 0
    )

    total_revenue = (

        calibration_revenue

        +

        external_revenue
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(

            "Calibration Revenue",

            f"{calibration_revenue:,.0f}"
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

    col4, col5, col6 = st.columns(3)

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

    with col6:

        st.metric(

            "Other Revenue",

            f"{external_revenue:,.0f}"
        )

    st.metric(

        "Total Revenue",

        f"{total_revenue:,.0f}"
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
    # =========================
    # EXPENSE MANAGEMENT
    # =========================

    st.divider()

    st.subheader(
        "📋 Expense Management"
    )

    if expense_df.empty:

        st.info(
            "No expense found"
        )

    else:

        render_aggrid(

            expense_df,

            height=300,

            page_size=10
        )

        expense_excel = dataframe_to_excel({

            "Expenses": expense_df

        })

        st.download_button(

            label="📥 Export Expense Excel",

            data=expense_excel,

            file_name="external_expenses.xlsx",

            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )
        )

        st.divider()

        expense_options = {

            f"ID {row['id']} | "
            f"{row['expense_date']} | "
            f"{row['amount']:,.0f}":

            row["id"]

            for _, row in expense_df.iterrows()
        }

        selected_expense = st.selectbox(

            "Select Expense To Delete",

            list(expense_options.keys())
        )

        if st.button(
            "🗑 Delete Expense"
        ):

            expense_id = expense_options[
                selected_expense
            ]

            ExternalExpenseService.delete_expense(
                expense_id
            )

            st.success(
                "Expense deleted"
            )

            st.rerun()
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

