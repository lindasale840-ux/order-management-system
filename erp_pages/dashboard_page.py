import streamlit as st
import pandas as pd
from services.dashboard_service import DashboardService
from repositories.order_repository import OrderRepository
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor
from components.aggrid_table import render_aggrid
from io import BytesIO
# Chỉ cần import đúng 1 dòng này từ file languages
from languages import t

def export_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Orders"
        )

    return output.getvalue()
def show_dashboard_page():
    require_editor()

    st.title(t("dashboard_center"))

    tab1, tab2 = st.tabs([
        "📥 Manual Input Entry",
        "📂 Excel Batch Import"
    ])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            order_number = st.text_input(t("order_number"))
            existing_order = {}

            if order_number.strip():
                existing_df = OrderRepository.get_by_order_number(order_number.strip())
                if not existing_df.empty:
                    existing_order = existing_df.iloc[0].to_dict()

            customer_name = st.text_input(t("customer_name")
                ,
                value=str(existing_order.get("customer_name", "") or "")
            )

        with col2:
            measurement_value = pd.Timestamp.today().date()
            if existing_order.get("measurement_date") is not None:
                measurement_value = pd.to_datetime(existing_order["measurement_date"]).date()

            measurement_date = st.date_input(t("measurement_date"), value=measurement_value)

            cert_saved = existing_order.get("cert_status")
            default_no_cert = pd.isna(cert_saved)

            no_cert = st.checkbox(t("no_cert_yet"), value=default_no_cert)

            if no_cert:
                cert_status = None
                st.info(t("cert_status_will_be_kept_empty"))
            else:
                cert_value = pd.Timestamp.today().date()
                if pd.notna(cert_saved):
                    cert_value = pd.to_datetime(cert_saved).date()
                cert_status = st.date_input("Cert Status Date", value=cert_value)
                
            disable_calibration_notification = st.checkbox(
                t("disable_calibration_notificati"),
                value=bool(existing_order.get("disable_calibration_notification", 0))
            )
            
            disable_document_notification = st.checkbox(
                t("disable_document_notification"),
                value=bool(existing_order.get("disable_document_notification", 0))
            ) 
            
            disable_payment_notification = st.checkbox(
                t("disable_payment_notification"),
                value=bool(existing_order.get("disable_payment_notification", 0))
            )

        # --- VALIDATION FORM NHẬP TAY ---
        is_form_invalid = (not order_number.strip()) or (not customer_name.strip())
        
        if is_form_invalid:
            st.warning(t("please_fill_in_all_required_fi"))

        if st.button(t("sync_order_data"), use_container_width=True, disabled=is_form_invalid):
            DashboardService.sync_order(
                customer_name,
                order_number,
                measurement_date,
                cert_status,
                st.session_state["sale_owner"],
                st.session_state["username"],
                disable_calibration_notification,
                disable_document_notification,
                disable_payment_notification
            )
            st.success("🎉 Order successfully synced!")
            st.rerun()

    with tab2:
        uploaded_file = st.file_uploader("Upload Excel File Structure", type=["xlsx"])

        if uploaded_file:
            excel_df = pd.read_excel(uploaded_file)
            st.dataframe(excel_df, use_container_width=True)

            if st.button("🚀 Bulk Sync From Excel", use_container_width=True):
                for _, row in excel_df.iterrows():
                    DashboardService.sync_order(
                        row["customer_name"],
                        row["order_number"],
                        row["measurement_date"],
                        row.get("cert_status", None),
                        st.session_state["sale_owner"],
                        st.session_state["username"],
                        row.get("disable_calibration_notification", 0),
                        row.get("disable_document_notification", 0),
                        row.get("disable_payment_notification", 0)
                    )
                st.success("🎉 Excel dataset processing complete!")
                st.rerun()

    st.divider()

    # --- DATA PROCESSING & FILTRATION ---
    all_df = OrderRepository.get_all_orders()

    all_df["measurement_date"] = pd.to_datetime(
        all_df["measurement_date"],
        errors="coerce"
    )

    all_df["next_calibration_date"] = (
        all_df["measurement_date"]
        + pd.DateOffset(months=11)
    )

    all_df = filter_by_sale_owner(all_df)

    df = all_df.copy()

    #st.metric("Total Operational Orders", len(df))

    # --- SEARCH BAR SECTION ---
    search_text = st.text_input(t("filter_customer_order_invoice"))
    if search_text:
        search_text = search_text.strip().lower()
        customer_match = df["customer_name"].astype(str).str.lower().str.contains(search_text, na=False)
        order_match = df["order_number"].astype(str).str.lower().str.contains(search_text, na=False)
        invoice_match = df["invoice_group"].astype(str).str.lower().str.contains(search_text, na=False)
        df = df[customer_match | order_match | invoice_match]

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.metric(
            t("total_operational_orders"),
            len(df)
        )

    with col2:
        st.download_button(
            t("download_all_orders"),
            data=export_excel(all_df),
            file_name="all_orders.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col3:
        st.download_button(
            t("download_filtered_orders"),
            data=export_excel(df),
            file_name="filtered_orders.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    # --- ĐÃ SỬA: BỘ ĐIỀU HƯỚNG PHÂN TRANG THUỒN PYTHON CAO CẤP ---
    st.subheader(t("data_viewer"))
    
    # Tạo 2 ô chọn song song: Một ô chọn số dòng/trang, một ô chọn số trang
    col_p1, col_p2, col_p3 = st.columns([2, 2, 6])
    
    with col_p1:
        rows_per_page = st.selectbox(
            "Rows per page",
            options=[5, 10, 20, 50, 100],
            index=1, # Mặc định hiển thị 10 dòng
            key="dashboard_pure_rows_per_page"
        )
        
    total_rows = len(df)
    # Tính toán động tổng số trang dựa trên số dòng được chọn (ví dụ chọn 20 dòng thì tổng số trang tự giảm xuống)
    total_pages = max(1, (total_rows + rows_per_page - 1) // rows_per_page)
    
    with col_p2:
        selected_page = st.selectbox(
            "Go to page", 
            options=list(range(1, total_pages + 1)), 
            index=0, 
            key="dashboard_pure_click_page_select"
        )
    
    # Cắt chính xác dữ liệu theo cấu hình đã click chọn
    start_idx = (selected_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    sliced_df = df.iloc[start_idx:end_idx]
    
    # Hiển thị bảng AgGrid tĩnh cố định dữ liệu đã cắt, đồng thời ẩn thanh phân trang cũ thừa thãi đi
    # (Nếu hàm render_aggrid của anh có nhận custom_options, anh có thể truyền suppressPaginationPanel=True vào gridOptions bên trong component đó)
    render_aggrid(sliced_df, height=450, page_size=rows_per_page, pagination=False, key="dashboard_grid_pure_sliced")

    st.divider()

    order_options_list = df["order_number"].tolist()

    # --- SECTION MÔ-ĐUN XÓA HÀNG LOẠT ---
    st.subheader(t("bulk_move_to_trash_actions"))
    selected_orders = st.multiselect(t("select_orders_for_disposal_que"), options=order_options_list, key="bulk_delete_orders_select")
    confirm_bulk_delete = st.checkbox(t("i_verify_moving_the_chosen_log"), key="bulk_delete_confirm_chk")

    is_bulk_delete_disabled = (not selected_orders) or (not confirm_bulk_delete)

    if st.button(t("move_selected_rows_to_trash"), disabled=is_bulk_delete_disabled, use_container_width=True):
        DashboardService.bulk_move_to_trash(selected_orders, st.session_state["username"])
        st.success(f"Successfully moved {len(selected_orders)} items to system trash.")
        st.rerun()
            
    st.divider()

    # --- SECTION XÓA ĐƠN LẺ ---
    st.subheader(t("delete_single_order_entry"))

    if order_options_list:
        selected_delete_order = st.selectbox(t("select_target_order_number_to"), order_options_list, key="delete_order_single_select")
        confirm_delete = st.checkbox(t("confirm_move_this_exact_entry"), key="single_delete_confirm_chk")

        is_single_delete_disabled = not confirm_delete

        if st.button(t("proceed_single_trash_action"), disabled=is_single_delete_disabled, use_container_width=True):
            DashboardService.move_to_trash(selected_delete_order, st.session_state["username"])
            st.success(f"Item {selected_delete_order} shifted into trash partition.")
            st.rerun()
    else:
        st.info(t("no_orders_currently_active_and"))