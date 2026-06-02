import streamlit as st

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)

from utils.excel_export import (
    dataframe_to_excel
)

def show_overdue_page():

    st.title("Overdue")

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

    overdue_df = df[

        (df["cert_overdue"]
         == "Overdue")

        |

        (df["payment_overdue"]
         == "Overdue")

        |

        (df["cert_workflow_status"]
         == "Missing Cert")
    ]

    excel_data = dataframe_to_excel({

    "Overdue": overdue_df
    })

    st.download_button(

            label="📥 Export Overdue Excel",

            data=excel_data,

            file_name="overdue_report.xlsx",

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

    key="overdue_page_size"
    )

    render_aggrid(

        overdue_df,

        height=500,

        page_size=page_size
    )