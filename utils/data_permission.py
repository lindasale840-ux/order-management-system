import streamlit as st
from repositories.assistant_sale_repository import AssistantSaleRepository

from repositories.assistant_sale_repository import (
    AssistantSaleRepository
)


def filter_by_sale_owner(df, role=None, username=None, sale_owner=None):
    # Nếu không truyền vào thì mới lấy từ session_state làm mặc định
    # Dùng "is None" chuẩn PEP 8 cho các biến rỗng
    if role is None:
        role = st.session_state.get("role")
    if username is None:
        username = st.session_state.get("username")
    if sale_owner is None:
        sale_owner = st.session_state.get("sale_owner")

    # Dùng "==" cho các giá trị chuỗi (String) để đảm bảo logic phân quyền
    if role == "ADMIN":
        return df

    if role == "SALE":
        if not sale_owner:
            return df.iloc[0:0]
        return df[df["sale_owner"] == sale_owner]
        
    if role == "ASSISTANT":
        return df[df["created_by"] == username]    

    return df.iloc[0:0]

    
