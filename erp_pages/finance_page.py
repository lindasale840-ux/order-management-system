import streamlit as st

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)

from utils.formatter import (
    format_currency
)

from utils.excel_export import (
    dataframe_to_excel
)

import pandas as pd

def show_finance_page():

    st.title("Finance")

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

    display_df = df.copy()

    if "total" in display_df.columns:

        display_df["total"] = (
            display_df["total"]
            .apply(format_currency)
        )

    if "commission_actual" in display_df.columns:

        display_df["commission_actual"] = (
            display_df["commission_actual"]
            .apply(format_currency)
        )

    # =========================
    # EXPORT EXCEL
    # =========================

    kpi_df = pd.DataFrame({

    "Metric": [

        "Total Orders",

        "Total Revenue",

        "Paid Orders",

        "Pending Orders"
    ],

    "Value": [

        len(df),

        df["total"].fillna(0).sum(),

        len(
            df[
                df[
                    "payment_status_text"
                ] == "Paid"
            ]
        ),

        len(
            df[
                df[
                    "payment_status_text"
                ] == "Pending"
            ]
        )
    ]
})

    excel_data = dataframe_to_excel({

        "KPI": kpi_df,

        "Finance": df
    })

    st.download_button(

        label="📥 Export Finance Excel",

        data=excel_data,

        file_name="finance_report.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    from components.aggrid_table import (
        render_aggrid
    )

    page_size = st.selectbox(

        "Rows per page",

        [5, 10, 20, 50],

        index=0,

        key="finance_page_size"
    )

    render_aggrid(

        display_df,

        height=500,

        page_size=page_size
    )