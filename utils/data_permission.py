import streamlit as st

from repositories.assistant_sale_repository import (
    AssistantSaleRepository
)


def filter_by_sale_owner(df, role=None, username=None, sale_owner=None):
    # Nếu không truyền vào thì mới lấy từ session_state làm mặc định
    if role == None:
        role = st.session_state.get("role")
    if username == None:
        username = st.session_state.get("username")
    if sale_owner == None:
        sale_owner = st.session_state.get("sale_owner")

    if role == "ADMIN":
        return df

    if role == "SALE":
        if not sale_owner:
            return df.iloc[0:0]
        return df[df["sale_owner"] == sale_owner]
        
    if role == "ASSISTANT":
        return df[df["created_by"] == username]    

    return df.iloc[0:0]

    