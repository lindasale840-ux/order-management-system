import streamlit as st
import plotly.express as px

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)

from components.pagination import (
    paginate_dataframe
)

def show_chart_customer_page():

    st.title("Chart Customer")

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

    if df.empty:

        st.warning("No data")

        return

    chart_df = (

        df.groupby(
            "customer_name"
        )["total"]

        .sum()

        .reset_index()
    )

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

    paginated_df = paginate_dataframe(
    df,
    "chart_customer",
    5
)

    st.dataframe(
        paginated_df,
        use_container_width=True
    )