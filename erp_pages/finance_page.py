import streamlit as st
import pandas as pd
from services.finance_service import FinanceService
from utils.formatter import format_currency
from utils.excel_export import dataframe_to_excel
from components.aggrid_table import render_aggrid

def show_finance_page():
    st.title("Finance")

    # 1. ĐÃ SỬA: Đảo hàm lấy DataFrame phân quyền lên đầu trang trước
    df = FinanceService.build_finance_dataframe(
        role=st.session_state.get("role"),
        username=st.session_state.get("username"),
        sale_owner=st.session_state.get("sale_owner")
    )

    # 2. BỔ SUNG: Ô tìm kiếm nhanh đa dạng (Quick Search) quét trên toàn bộ các cột
    search_query = st.text_input("🔍 Quick Search (Order Number, Customer, Sale Owner, etc.)", "")

    if search_query:
        # Lọc mờ trên toàn bộ các cột dạng chuỗi của dataframe
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    # 3. ĐÃ SỬA: Chỉ bốc các khách hàng thuộc quyền quản lý của user từ df để làm Dropdown
    if not df.empty and "customer_name" in df.columns:
        customer_options = ["ALL"] + sorted(df["customer_name"].dropna().unique().tolist())
    else:
        customer_options = ["ALL"]

    selected_customer = st.selectbox(
        "Filter Customer",
        customer_options
    )

    # 4. Áp dụng bộ lọc Dropdown Customer nếu người dùng chọn cụ thể một khách hàng
    if selected_customer != "ALL":
        df = df[df["customer_name"] == selected_customer]

    # 5. GIỮ NGUYÊN LOGIC CŨ: Tạo dataframe hiển thị và format định dạng tiền tệ
    display_df = df.copy()

    if "total" in display_df.columns:
        display_df["total"] = display_df["total"].apply(format_currency)

    if "commission_actual" in display_df.columns:
        display_df["commission_actual"] = display_df["commission_actual"].apply(format_currency)

    # ========================================================
    # EXPORT EXCEL & KPI (GIỮ NGUYÊN LOGIC TÍNH TOÁN CŨ CỦA BẠN)
    # ========================================================
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
            len(df[df["payment_status_text"] == "Paid"]),
            len(df[df["payment_status_text"] == "Pending"])
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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 6. GIỮ NGUYÊN LOGIC CŨ: Hiển thị AgGrid phân trang
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