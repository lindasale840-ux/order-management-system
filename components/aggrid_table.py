import streamlit as st
from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode
)
import math

def render_aggrid(
    dataframe,
    height=500,
    pagination=True,
    page_size=5,
    key=None,
    color_sla=False
):
    gb = GridOptionsBuilder.from_dataframe(dataframe)

    # =========================
    # DEFAULT COLUMN CONFIG (PREMIUM SLATE)
    # =========================
    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        editable=False,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        wrapText=True,
        autoHeight=True,
        minWidth=130
    )

    # =========================
    # PAGINATION
    # =========================
    if pagination:
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=page_size
        )

    # =========================
    # SELECTION
    # =========================
    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=False
    )

    grid_options = gb.build()

    # Tinh chỉnh thiết kế cho các dòng trạng thái SLA (Màu pastel mịn màng chuyên nghiệp)
    if color_sla and "sla_status" in dataframe.columns:
        sla_style = JsCode(
            """
            function(params) {
                if (params.value == "OK") {
                    return {
                        'backgroundColor': '#e2f5ea',
                        'color': '#146c43',
                        'fontWeight': '600',
                        'borderRadius': '4px'
                    };
                }
                if (params.value == "WARNING") {
                    return {
                        'backgroundColor': '#fff3cd',
                        'color': '#a18105',
                        'fontWeight': '600',
                        'borderRadius': '4px'
                    };
                }
                if (params.value == "OVER SLA") {
                    return {
                        'backgroundColor': '#fce8e6',
                        'color': '#c53929',
                        'fontWeight': '600',
                        'borderRadius': '4px'
                    };
                }
                return null;
            }
            """
        )

        grid_options["columnDefs"] = [{"field": col} for col in dataframe.columns]

        for col in grid_options["columnDefs"]:
            if col["field"] == "sla_status":
                col["cellStyle"] = sla_style

    grid_options["enableRangeSelection"] = True
    grid_options["enableCellTextSelection"] = True
    grid_options["ensureDomOrder"] = True

    # ========================================================
    # CHỨC NĂNG PHÂN TRANG CHUYÊN NGHIỆP (NHẬP SỐ ĐỂ NHẢY TRANG)
    # ========================================================
    if pagination and not dataframe.empty:
        total_rows = len(dataframe)
        max_pages = math.ceil(total_rows / page_size)
        
        # Tạo giao diện ô nhập số gọn gàng ngay trên bảng dữ liệu
        col1, col2 = st.columns([2, 8])
        with col1:
            # Tạo một khóa duy nhất cho ô nhập số để không bị trùng lặp giữa các trang
            target_page = st.number_input(
                "Đến trang:", 
                min_value=1, 
                max_value=max_pages, 
                value=1, 
                step=1, 
                key=f"input_page_{key}" if key else "input_page_default"
            )
        with col2:
            st.markdown(f"<p style='margin-top:28px; color:#64748b;'>Tổng số: {max_pages} trang ({total_rows} dòng)</p>", unsafe_allow_html=True)
            
        # Thêm đoạn mã JavaScript điều hướng API của AgGrid nhảy trang theo thời gian thực
        grid_options["onGridReady"] = JsCode(f"""
            function(params) {{
                params.api.paginationGoToPage({target_page - 1});
            }}
        """)

    # Ép bảng AgGrid sử dụng theme thiết kế Alpine hiện đại
    return AgGrid(
        dataframe,
        gridOptions=grid_options,
        height=height,
        width="100%",
        key=key,
        theme="alpine",
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=False,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True # Kích hoạt để thực thi tính năng nhảy trang JsCode
    )