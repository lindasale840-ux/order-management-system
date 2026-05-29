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

    paginated_df = paginate_dataframe(
    df,
    "finance",
    5
)

    st.dataframe(
        paginated_df,
        use_container_width=True
    )