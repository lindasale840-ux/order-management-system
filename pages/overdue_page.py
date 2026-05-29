import streamlit as st

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)

from components.pagination import (
    paginate_dataframe
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

    paginated_df = paginate_dataframe(
    overdue_df,
    "overdue",
    5
)

    st.dataframe(
        paginated_df,
        use_container_width=True
    )