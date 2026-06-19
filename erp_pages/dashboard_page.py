import streamlit as st
import pandas as pd
from services.dashboard_service import DashboardService
from repositories.order_repository import OrderRepository
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor
from components.aggrid_table import render_aggrid  # Thay thế bộ phân trang cũ bằng AgGrid thông minh

def show_dashboard_page():
    require_editor()

    st.title("📊 Dashboard Center")

    tab1, tab2 = st.tabs([
        "📥 Manual Input Entry",
        "📂 Excel Batch Import"
    ])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            order_number = st.text_input("Order Number (*)")
            existing_order = {}

            if order_number.strip():
                existing_df = OrderRepository.get_by_order_number(order_number.strip())
                if not existing_df.empty:
                    existing_order = existing_df.iloc[0].to_dict()

            customer_name = st.text_input(
                "Customer Name (*)",
                value=str(existing_order.get("customer_name", "") or "")
            )

        with col2:
            measurement_value = pd.Timestamp.today().date()
            if existing_order.get("measurement_date") is not None:
                measurement_value = pd.to_datetime(existing_order["measurement_date"]).date()

            measurement_date = st.date_input("Measurement Date", value=measurement_value)

            cert_saved = existing_order.get("cert_status")
            default_no_cert = pd.isna(cert_saved)

            no_cert = st.checkbox("No Cert Yet", value=default_no_cert)

            if no_cert:
                cert_status = None
                st.info("💡 Cert status will be kept empty.")
            else:
                cert_value = pd.Timestamp.today().date()
                if pd.notna(cert_saved):
                    cert_value = pd.to_datetime(cert_saved).date()
                cert_status = st.date_input("Cert Status Date", value=cert_value)
                
            disable_calibration_notification = st.checkbox(
                "Disable Calibration Notification",
                value=bool(existing_order.get("disable_calibration_notification", 0))
            )
            
            disable_document_notification = st.checkbox(
                "Disable Document Notification",
                value=bool(existing_order.get("disable_document_notification", 0))
            ) 
            
            disable_payment_notification = st.checkbox(
                "Disable Payment Notification",
                value=bool(existing_order.get("disable_payment_notification", 0))
            )

        # --- VALIDATION FORM NHẬP TAY ---
        is_form_invalid = (not order_number.strip()) or (not customer_name.strip())
        
        if is_form_invalid:
            st.warning("⚠️ Please fill in all required fields marked with (*) to activate Sync.")

        if st.button("Sync Order Data", use_container_width=True, disabled=is_form_invalid):
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

    # Data Processing & Filtration
    df = OrderRepository.get_all_orders()
    df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")
    df["next_calibration_date"] = df["measurement_date"] + pd.DateOffset(months=11)
    df = filter_by_sale_owner(df)

    st.metric("Total Operational Orders", len(df))

    # Search Bar Section
    search_text = st.text_input("🔍 Filter Customer / Order / Invoice Group Global Data")
    if search_text:
        search_text = search_text.strip().lower()
        customer_match = df["customer_name"].astype(str).str.lower().str.contains(search_text, na=False)
        order_match = df["order_number"].astype(str).str.lower().str.contains(search_text, na=False)
        invoice_match = df["invoice_group"].astype(str).str.lower().str.contains(search_text, na=False)
        df = df[customer_match | order_match | invoice_match]

    # Bảng hiển thị thông minh: Loại bỏ hoàn toàn selectbox Rows per page cũ kĩ!
    render_aggrid(df, height=450, page_size=10, key="dashboard_grid_main")

    st.divider()

    # --- SECTION MÔ-ĐUN XÓA HÀNG LOẠT ---
    st.subheader("🗑️ Bulk Move To Trash Actions")
    selected_orders = st.multiselect("Select Orders for Disposal Queue", options=df["order_number"].tolist())
    confirm_bulk_delete = st.checkbox("I verify moving the chosen logs to system trash bin")

    is_bulk_delete_disabled = (not selected_orders) or (not confirm_bulk_delete)

    if st.button("🗑️ Move Selected Rows To Trash", disabled=is_bulk_delete_disabled):
        DashboardService.bulk_move_to_trash(selected_orders, st.session_state["username"])
        st.success(f"Successfully moved {len(selected_orders)} items to system trash.")
        st.rerun()
            
    st.divider()

    # --- SECTION XÓA ĐƠN LẺ ---
    st.subheader("🗑️ Delete Single Order Entry")
    order_options = df["order_number"].tolist()

    if order_options:
        selected_delete_order = st.selectbox("Select Target Order Number to Erase", order_options, key="delete_order_select")
        confirm_delete = st.checkbox("Confirm move this exact entry to trash storage")

        is_single_delete_disabled = not confirm_delete

        if st.button("🗑️ Proceed Single Trash Action", disabled=is_single_delete_disabled):
            DashboardService.move_to_trash(selected_delete_order, st.session_state["username"])
            st.success(f"Item {selected_delete_order} shifted into trash partition.")
            st.rerun()
    else:
        st.info("No orders currently active and available for clear operations.")