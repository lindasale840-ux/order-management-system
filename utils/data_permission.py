import streamlit as st

from repositories.assistant_sale_repository import (
    AssistantSaleRepository
)


def filter_by_sale_owner(df):

    role = st.session_state.get(
        "role"
    )

    username = st.session_state.get(
        "username"
    )

    sale_owner = st.session_state.get(
        "sale_owner"
    )

    if role == "ADMIN":
        return df

    if role == "SALE":

        if not sale_owner:
            return df.iloc[0:0]

        return df[
            df["sale_owner"]
            == sale_owner
        ]

    if role == "ASSISTANT":

        sales = (
            AssistantSaleRepository
            .get_sales_by_assistant(
                username
            )
        )

        if sales:

            return df[
                df["sale_owner"]
                .isin(sales)
            ]

        if sale_owner:

            return df[
                df["sale_owner"]
                == sale_owner
            ]

        return df.iloc[0:0]

    return df.iloc[0:0]