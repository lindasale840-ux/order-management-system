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
    # === ĐOẠN CHÈN MỚI: CHUẨN HÓA CỘT NGÀY THÁNG THÀNH TEXT ===
    # Tạo một bản sao để tránh làm ảnh hưởng đến dữ liệu gốc của ứng dụng
    dataframe = dataframe.copy()
    # Tự động quét toàn bộ các cột, nếu thấy cột nào là ngày tháng hoặc có tên liên quan, ta ép về dạng chuỗi chỉ có Ngày
    for col in dataframe.columns:
        col_lower = col.lower()
        if "date" in col_lower or "ngay" in col_lower or "created" in col_lower or "updated" in col_lower:
            try:
                import pandas as pd
                # BỔ SUNG: errors='coerce' để tự động biến các ô lỗi/trống thành NaT (không gây crash)
                # và mixed='infer' để Pandas tự quét nhanh định dạng hỗn hợp mà không đưa ra cảnh báo
                datetime_col = pd.to_datetime(dataframe[col], errors='coerce', mixed='infer')
                dataframe.loc[:, col] = datetime_col.dt.strftime('%Y-%m-%d')
            except Exception:
                pass
    # ========================================================
    # DEFAULT COLUMN CONFIG (BẬT SAO CHÉP TEXT, BÔI ĐEN RANGE)
    # ========================================================
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

    # ========================================================
    # PAGINATION
    # ========================================================
    if pagination:
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=page_size
        )

    # ========================================================
    # SELECTION
    # ========================================================
    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=False
    )

    grid_options = gb.build()

    # ========================================================
    # COLOR SLA STYLE (TỐI ƯU: KHÔNG GHI ĐÈ ĐÈ COLUMN DEFINITIONS)
    # ========================================================
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

        # ✅ ĐÃ SỬA: Duyệt trực tiếp qua cấu hình cột có sẵn thay vì khởi tạo lại mảng mới
        if "columnDefs" in grid_options:
            for col in grid_options["columnDefs"]:
                if col.get("field") == "sla_status":
                    col["cellStyle"] = sla_style
    
    # Kích hoạt toàn diện tính năng bôi đen chọn vùng và copy dữ liệu thô từ bảng
    grid_options["enableRangeSelection"] = True
    grid_options["enableCellTextSelection"] = True
    grid_options["ensureDomOrder"] = True

    # ========================================================
    # CHỨC NĂNG PHÂN TRANG CHUYÊN NGHIỆP (NHẬP SỐ ĐỂ NHẢY TRANG)
    # ========================================================
    if pagination and not dataframe.empty:
        total_rows = len(dataframe)
        max_pages = math.ceil(total_rows / page_size)
        
        col1, col2 = st.columns([2, 8])
        with col1:
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
            
        grid_options["onGridReady"] = JsCode(f"""
            function(params) {{
                params.api.paginationGoToPage({target_page - 1});
            }}
        """)
    else:
        grid_options["suppressPaginationPanel"] = True

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
        allow_unsafe_jscode=True
    )