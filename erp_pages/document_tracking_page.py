import streamlit as st
import pandas as pd
from repositories.order_repository import OrderRepository
from repositories.document_tracking_repository import DocumentTrackingRepository
from services.document_tracking_service import DocumentTrackingService
from components.aggrid_table import render_aggrid
from utils.excel_export import dataframe_to_excel
from utils.auth_guard import require_editor
from repositories.other_document_tracking_repository import OtherDocumentTrackingRepository
from services.other_document_tracking_service import OtherDocumentTrackingService
from utils.data_permission import filter_by_sale_owner
# Chỉ cần import đúng 1 dòng này từ file languages
from languages import t
def show_document_tracking_page():
    require_editor()

    st.title(t("document_tracking_logistics_hu"))
    
    st.header(t("order_document_tracking"))

    orders_df = OrderRepository.get_all_orders()
    orders_df = filter_by_sale_owner(orders_df)
    orders_df["cert_status"] = pd.to_datetime(orders_df["cert_status"], errors="coerce")
    orders_df = orders_df[orders_df["cert_status"].notna()]

    orders_df["display"] = (
        orders_df["order_number"] + " | " + 
        orders_df["customer_name"] + " | Cert: " + 
        orders_df["cert_status"].dt.strftime("%Y-%m-%d")
    )

    # --- SEARCH ORDER ---
    search_text = st.text_input(t("fast_filter_active_order_custo"))
    filtered_df = orders_df.copy()

    if search_text:
        filtered_df = filtered_df[
            filtered_df["display"].str.contains(search_text, case=False, na=False)
        ]

    filtered_order_map = {
        row["display"]: row["order_number"] for _, row in filtered_df.iterrows()
    }

    col1, col2 = st.columns(2)

    with col1:
        if filtered_order_map:
            selected_display = st.selectbox(t("target_order_pipeline"), list(filtered_order_map.keys()))
            selected_order = filtered_order_map[selected_display]

            latest_tracking = DocumentTrackingRepository.get_latest_by_order(selected_order)
            tracking_history_df = DocumentTrackingRepository.get_by_order(selected_order)

            existing_data = {}
            if not latest_tracking.empty:
                existing_data = latest_tracking.iloc[0].to_dict()
        else:
            st.warning(t("no_matching_valid_certified_or"))
            st.stop()

        sent_date_value = pd.Timestamp.today().date()
        if existing_data.get("sent_date") is not None:
            sent_date_value = pd.to_datetime(existing_data["sent_date"]).date()

        sent_date = st.date_input(t("dispatched_sent_date"), value=sent_date_value)

    with col2:
        received_date_saved = existing_data.get("received_date")
        not_received = pd.isna(received_date_saved)
        not_received = st.checkbox(t("pending_courier_delivery_not_r"), value=not_received)

        if not_received:
            received_date = None
            st.info(t("document_packet_flagged_as_cur"))
        else:
            received_date_value = pd.Timestamp.today().date()
            if pd.notna(received_date_saved):
                received_date_value = pd.to_datetime(received_date_saved).date()
            received_date = st.date_input("Consignee Received Date Stamp", value=received_date_value)

        note = st.text_input(t("logistics_remarks_notes"), value=str(existing_data.get("note", "") or ""))

    # --- VALIDATION NÚT ADD TRACKING ---
    is_tracking_invalid = not filtered_order_map

    if st.button(t("commit_tracking_entry"), use_container_width=True, disabled=is_tracking_invalid):
        DocumentTrackingService.add_tracking(
            filtered_order_map[selected_display],
            sent_date,
            received_date,
            note
        )
        st.success(t("tracking_baseline_successfully"))
        st.rerun()
        
    # --- BẢNG 1: TRACKING HISTORY (Phân trang Python thuần) ---
    st.divider()
    st.subheader(t("current_order_selected_trackin"))

    if not tracking_history_df.empty:
        history_display = tracking_history_df[["id", "sent_date", "received_date", "note"]].copy()
        
        # Thiết lập bộ chọn trang click chuột cho bảng lịch sử lẻ
        h_rows_per_page = 5
        h_total_rows = len(history_display)
        h_total_pages = max(1, (h_total_rows + h_rows_per_page - 1) // h_rows_per_page)
        
        col_h1, col_h2 = st.columns([3, 7])
        with col_h1:
            h_selected_page = st.selectbox(
                t("page_history"), 
                options=list(range(1, h_total_pages + 1)), 
                index=0, 
                key="track_hist_pure_page_select"
            )
        h_start = (h_selected_page - 1) * h_rows_per_page
        h_sliced_df = history_display.iloc[h_start : h_start + h_rows_per_page]
        
        render_aggrid(h_sliced_df, height=220, page_size=h_rows_per_page, pagination=False, key="tracking_history_grid")
    else:
        st.info(t("no_localized_operational_track"))
    
    # --- BẢNG 2: GLOBAL DATABASE MASTER LEDGER (Phân trang Python thuần) ---
    st.divider()
    st.subheader(t("global_document_tracking_ledge"))

    tracking_df = DocumentTrackingRepository.get_all()
    tracking_df = filter_by_sale_owner(tracking_df)
    if tracking_df.empty:
        st.info(t("system_master_tracking_log_dat"))
    else:
        search_text_global = st.text_input(t("search_master_database_order_c"))
        if search_text_global:
            keyword = search_text_global.lower()
            tracking_df = tracking_df[
                tracking_df.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(keyword, na=False)).any(axis=1)
            ]
        
        # Thiết lập bộ chọn trang click chuột nâng cao có chọn Rows per page cho bảng chính
        col_g1, col_g2, col_g3 = st.columns([2, 2, 6])
        with col_g1:
            g_rows_per_page = st.selectbox(
                "Rows per page (Master)",
                options=[5, 10, 20, 50, 100],
                index=1,
                key="global_track_pure_rows_per_page"
            )
        g_total_rows = len(tracking_df)
        g_total_pages = max(1, (g_total_rows + g_rows_per_page - 1) // g_rows_per_page)
        with col_g2:
            g_selected_page = st.selectbox(
                "Go to page (Master)",
                options=list(range(1, g_total_pages + 1)),
                index=0,
                key="global_track_pure_page_select"
            )
        g_start = (g_selected_page - 1) * g_rows_per_page
        g_sliced_df = tracking_df.iloc[g_start : g_start + g_rows_per_page]

        render_aggrid(g_sliced_df, height=400, page_size=g_rows_per_page, pagination=False, key="global_doc_tracking_grid")

        excel_data = dataframe_to_excel({"Document Tracking": tracking_df})
        st.download_button(
            t("export_master_excel_sheet"),
            data=excel_data,
            file_name="document_tracking.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.divider()
        # --- MÔ-ĐUN XÓA LOG BẢNG CHÍNH ---
        delete_options = {
            f"ID {row['id']} | {row['order_number']} | Sent: {row['sent_date']}": row["id"] for _, row in tracking_df.iterrows()
        }
        selected_delete = st.selectbox(t("select_target_master_tracking"), list(delete_options.keys()))
        
        if st.button(t("purge_selected_tracking_entry"), use_container_width=True):
            DocumentTrackingService.delete_tracking(delete_options[selected_delete])
            st.success(t("entry_safely_extracted_and_dro"))
            st.rerun()
        
    # --- PHẦN KHỐI NHẬP LIỆU AD-HOC ---
    st.divider()
    st.subheader(t("miscellaneous_ad_hoc_document"))

    col1, col2 = st.columns(2)
    with col1:
        other_customer = st.text_input(t("external_customer_name"))
        other_doc_type = st.text_input(t("document_type_class_name"))

    with col2:
        other_sent_date = st.date_input(t("external_dispatch_sent_date"), key="other_sent")
        other_received = st.checkbox(t("external_item_pending_not_rece"), key="other_receive_check")

        if other_received:
            other_received_date = None
        else:
            other_received_date = st.date_input(t("external_item_received_date_st"), key="other_received")

    other_note = st.text_area(t("ad_hoc_tracking_remarks"), key="other_note")

    # --- VALIDATION FORM TÀI LIỆU KHÁC ---
    is_other_invalid = (not other_customer.strip()) or (not other_doc_type.strip())
    
    if is_other_invalid:
        st.warning(t("ad_hoc_document_capture_fields"))

    if st.button(t("register_ad_hoc_document_entry"), use_container_width=True, disabled=is_other_invalid):
        OtherDocumentTrackingService.add_tracking(
            other_customer,
            other_doc_type,
            other_sent_date,
            other_received_date,
            other_note
        )
        st.success(t("miscellaneous_ad_hoc_tracking"))
        st.rerun()  
        
    # --- BẢNG 3: MISCELLANEOUS DOCUMENT HISTORY (Phân trang Python thuần) ---
    st.divider()
    st.subheader(t("miscellaneous_document_trackin"))   
    
    other_tracking_df = OtherDocumentTrackingRepository.get_all()

    if not other_tracking_df.empty:
        col_o1, col_o2, col_o3 = st.columns([2, 2, 6])
        with col_o1:
            o_rows_per_page = st.selectbox(
                "Rows per page (Ad-hoc)",
                options=[5, 10, 20, 50, 100],
                index=1,
                key="other_track_pure_rows_per_page"
            )
        o_total_rows = len(other_tracking_df)
        o_total_pages = max(1, (o_total_rows + o_rows_per_page - 1) // o_rows_per_page)
        with col_o2:
            o_selected_page = st.selectbox(
                "Go to page (Ad-hoc)",
                options=list(range(1, o_total_pages + 1)),
                index=0,
                key="other_track_pure_page_select"
            )
        o_start = (o_selected_page - 1) * o_rows_per_page
        o_sliced_df = other_tracking_df.iloc[o_start : o_start + o_rows_per_page]

        render_aggrid(o_sliced_df, height=250, page_size=o_rows_per_page, pagination=False, key="other_tracking_grid")
    else:
        st.info(t("no_external_miscellaneous_ad_h"))