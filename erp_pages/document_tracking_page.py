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

def show_document_tracking_page():
    require_editor()

    st.title("📨 Document Tracking & Logistics Hub")
    
    st.header("📋 Order Document Tracking")

    orders_df = OrderRepository.get_all_orders()
    orders_df["cert_status"] = pd.to_datetime(orders_df["cert_status"], errors="coerce")
    orders_df = orders_df[orders_df["cert_status"].notna()]

    orders_df["display"] = (
        orders_df["order_number"] + " | " + 
        orders_df["customer_name"] + " | Cert: " + 
        orders_df["cert_status"].dt.strftime("%Y-%m-%d")
    )

    # --- SEARCH ORDER ---
    search_text = st.text_input("🔍 Fast Filter Active Order / Customer Record Pipeline")
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
            selected_display = st.selectbox("Target Order Pipeline (*)", list(filtered_order_map.keys()))
            selected_order = filtered_order_map[selected_display]

            latest_tracking = DocumentTrackingRepository.get_latest_by_order(selected_order)
            tracking_history_df = DocumentTrackingRepository.get_by_order(selected_order)

            existing_data = {}
            if not latest_tracking.empty:
                existing_data = latest_tracking.iloc[0].to_dict()
        else:
            st.warning("⚠️ No matching valid certified order records located.")
            st.stop()

        sent_date_value = pd.Timestamp.today().date()
        if existing_data.get("sent_date") is not None:
            sent_date_value = pd.to_datetime(existing_data["sent_date"]).date()

        sent_date = st.date_input("Dispatched Sent Date", value=sent_date_value)

    with col2:
        received_date_saved = existing_data.get("received_date")
        not_received = pd.isna(received_date_saved)
        not_received = st.checkbox("Pending Courier Delivery (Not Received Yet)", value=not_received)

        if not_received:
            received_date = None
            st.info("ℹ️ Document packet flagged as currently transit-bound.")
        else:
            received_date_value = pd.Timestamp.today().date()
            if pd.notna(received_date_saved):
                received_date_value = pd.to_datetime(received_date_saved).date()
            received_date = st.date_input("Consignee Received Date Stamp", value=received_date_value)

        note = st.text_input("Logistics Remarks & Notes", value=str(existing_data.get("note", "") or ""))

    # --- VALIDATION NÚT ADD TRACKING ---
    is_tracking_invalid = not filtered_order_map

    if st.button("💾 Commit Tracking Entry", use_container_width=True, disabled=is_tracking_invalid):
        DocumentTrackingService.add_tracking(
            filtered_order_map[selected_display],
            sent_date,
            received_date,
            note
        )
        st.success("🎉 Tracking baseline successfully updated!")
        st.rerun()
        
    # --- TRACKING HISTORY ---
    st.divider()
    st.subheader("📜 Current Order Selected Tracking History")

    if not tracking_history_df.empty:
        history_display = tracking_history_df[["id", "sent_date", "received_date", "note"]].copy()
        # Đã loại bỏ selectbox hàng thừa, cấu hình gọn gàng trực tiếp
        render_aggrid(history_display, height=220, page_size=5, key="tracking_history_grid")
    else:
        st.info("No localized operational tracking history available for this item.")
    
    st.divider()
    st.subheader("📊 Global Document Tracking Ledger Master")

    tracking_df = DocumentTrackingRepository.get_all()

    if tracking_df.empty:
        st.info("System master tracking log data repository empty.")
    else:
        search_text_global = st.text_input("🔍 Search Master Database (Order / Customer / Note Keywords)")
        if search_text_global:
            keyword = search_text_global.lower()
            tracking_df = tracking_df[
                tracking_df.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(keyword, na=False)).any(axis=1)
            ]
        
        # Bảng AgGrid Tổng quản lý gọn 10 dòng
        render_aggrid(tracking_df, height=400, page_size=10, key="global_doc_tracking_grid")

        excel_data = dataframe_to_excel({"Document Tracking": tracking_df})
        st.download_button(
            "📥 Export Master Excel Sheet",
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
        selected_delete = st.selectbox("Select Target Master Tracking Entry to Void", list(delete_options.keys()))
        
        if st.button("🗑️ Purge Selected Tracking Entry", use_container_width=True):
            DocumentTrackingService.delete_tracking(delete_options[selected_delete])
            st.success("Entry safely extracted and dropped from database branch.")
            st.rerun()
        
    st.divider()
    st.subheader("📦 Miscellaneous Ad-hoc Document Tracking")

    col1, col2 = st.columns(2)
    with col1:
        other_customer = st.text_input("External Customer Name (*)")
        other_doc_type = st.text_input("Document Type / Class Name (*)")

    with col2:
        other_sent_date = st.date_input("External Dispatch Sent Date", key="other_sent")
        other_received = st.checkbox("External Item Pending (Not Received)", key="other_receive_check")

        if other_received:
            other_received_date = None
        else:
            other_received_date = st.date_input("External Item Received Date Stamp", key="other_received")

    other_note = st.text_area("Ad-hoc Tracking Remarks", key="other_note")

    # --- VALIDATION FORM TÀI LIỆU KHÁC ---
    is_other_invalid = (not other_customer.strip()) or (not other_doc_type.strip())
    
    if is_other_invalid:
        st.warning("⚠️ Ad-hoc document capture fields marked (*) must be completed to initialize storage sync.")

    if st.button("➕ Register Ad-hoc Document Entry", use_container_width=True, disabled=is_other_invalid):
        OtherDocumentTrackingService.add_tracking(
            other_customer,
            other_doc_type,
            other_sent_date,
            other_received_date,
            other_note
        )
        st.success("🎉 Miscellaneous ad-hoc tracking entry recorded.")
        st.rerun()  
        
    st.divider()
    st.subheader("📦 Miscellaneous Document Tracking History Database")   
    
    other_tracking_df = OtherDocumentTrackingRepository.get_all()

    if not other_tracking_df.empty:
        render_aggrid(other_tracking_df, height=250, page_size=10, key="other_tracking_grid")
    else:
        st.info("No external miscellaneous ad-hoc history logs located.")