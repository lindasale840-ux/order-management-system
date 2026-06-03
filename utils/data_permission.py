import streamlit as st


def filter_by_sale_owner(df):

    role = st.session_state.get("role")

    sale_owner = st.session_state.get(
        "sale_owner"
    )

    if role == "ADMIN":

        return df

    if not sale_owner:

        return df.iloc[0:0]

    return df[
        df["sale_owner"] == sale_owner
    ]