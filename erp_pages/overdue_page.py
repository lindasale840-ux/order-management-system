import streamlit as st
import pandas as pd
from services.finance_service import FinanceService
from utils.excel_export import dataframe_to_excel
from components.aggrid_table import render_aggrid

def show_overdue_page():
    st.title("Overdue")

    # 1. Lấy DataFrame đã được phân quyền chuẩn chỉnh theo từng user trước
    df = FinanceService.build_finance_dataframe(
        role=st.session_state.get("role"),
        username=st.session_state.get("username"),
        sale_owner=st.session_state.get("sale_owner")
    )

    # 2. Tạo bộ lọc đa dạng (Tìm kiếm nhanh toàn bộ bảng) bằng text input
    search_query = st.text_input("🔍 Quick Search (Order Number, Customer, Sale Owner, etc.)", "")

    if search_query:
        # Lọc mờ trên toàn bộ các cột dạng chuỗi của dataframe để tìm kiếm đa dạng
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    # 3. ĐÃ SỬA: Lấy danh sách khách hàng từ chính df đã phân quyền của user này để làm dropdown
    if not df.empty and "customer_name" in df.columns:
        # Lấy các giá trị duy nhất, loại bỏ giá trị trống (NaN) và sắp xếp theo thứ tự bảng chữ cái
        customer_options = ["ALL"] + sorted(df["customer_name"].dropna().unique().tolist())
    else:
        customer_options = ["ALL"]

    selected_customer = st.selectbox(
        "Filter Customer",
        customer_options
    )

    # 4. Áp dụng bộ lọc Dropdown Customer nếu người dùng chọn cụ thể
    if selected_customer != "ALL":
        df = df[df["customer_name"] == selected_customer]

    # 5. Lọc ra các đơn hàng Overdue / Missing Cert từ tập dữ liệu sau khi đã qua các bộ lọc trên
    overdue_df = df[
        (df["cert_overdue"] == "Overdue")
        | (df["payment_overdue"] == "Overdue")
        | (df["cert_workflow_status"] == "Missing Cert")
    ]

    # 6. Phần xuất Excel báo cáo
    excel_data = dataframe_to_excel({
        "Overdue": overdue_df
    })

    st.download_button(
        label="📥 Export Overdue Excel",
        data=excel_data,
        file_name="overdue_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 7. Hiển thị dữ liệu lên bảng AgGrid
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