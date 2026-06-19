import streamlit as st
import pandas as pd
from repositories.order_repository import OrderRepository
from repositories.equipment_tracking_repository import EquipmentTrackingRepository
from services.equipment_tracking_service import EquipmentTrackingService
from utils.business_day import working_days_between
from components.aggrid_table import render_aggrid

def show_equipment_tracking_page():
    st.title("📦 Equipment & Asset Lifecycle Tracking")

    orders_df = OrderRepository.get_all_orders()

    customer_options = ["ALL"] + sorted(orders_df["customer_name"].dropna().unique().tolist())
    selected_customer = st.selectbox("Filter Master Corporate Customer", customer_options)

    if selected_customer != "ALL":
        orders_df = orders_df[orders_df["customer_name"] == selected_customer]

    order_numbers_list = orders_df["order_number"].tolist()
    
    if not order_numbers_list:
        st.warning("⚠️ No available orders detected under current parameters.")
        return

    order_number = st.selectbox("Target Order Pipeline ID (*)", order_numbers_list)

    existing_tracking = EquipmentTrackingRepository.get_by_order_number(order_number)
    tracking = existing_tracking.iloc[0] if not existing_tracking.empty else None

    service_default = "LAB"
    if tracking is not None:
        service_default = tracking["service_type"]

    service_type = st.selectbox(
        "Operational Service Routing Architecture",
        ["LAB", "SUBCONTRACT_LAB"],
        index=["LAB", "SUBCONTRACT_LAB"].index(service_default)
    )

    direct_to_customer = st.checkbox("Subcontract Vendor Dispatches Directly To End Client")

    customer_send_date = st.date_input("Client Unit Outbound Dispatch Date")
    gst_receive_date = st.date_input("GST Operations Intake Receipt Date")

    subcontract_name = ""
    gst_send_sub_date = None
    sub_receive_date = None
    sub_send_date = None
    gst_receive_back_date = None

    if service_type == "SUBCONTRACT_LAB":
        subcontract_name = st.text_input(
            "Subcontract Vendor Organization Name (*)",
            value=(tracking["subcontract_name"] if tracking is not None else "")
        )
        gst_send_sub_date = st.date_input("GST Handover To Subcontractor Date")
        sub_receive_date = st.date_input("Subcontractor Facility Ingestion Date")
        sub_send_date = st.date_input("Subcontractor Fulfillment Release Date")

        if not direct_to_customer:
            gst_receive_back_date = st.date_input("GST Intake Back From Subcontractor")

    if service_type == "LAB" or (service_type == "SUBCONTRACT_LAB" and not direct_to_customer):
        gst_send_customer_date = st.date_input("GST Final Delivery Release Outbound")
    else:
        gst_send_customer_date = None

    not_receive_yet = st.checkbox("Consignee Client Asset In Transit (Not Received Yet)")

    if not_receive_yet:
        customer_receive_date = None
    else:
        customer_receive_date = st.date_input("Client Ultimate Confirmed Intake Date")

    note = st.text_area("Asset Operational History Notes & Remarks")

    # --- VALIDATION FORM THEO DÕI THIẾT BỊ ---
    is_asset_invalid = (service_type == "SUBCONTRACT_LAB" and not subcontract_name.strip())

    if is_asset_invalid:
        st.warning("⚠️ Please provide the Subcontract Vendor Organization Name (*) to authorize save execution.")

    if st.button("Save Tracking Status", use_container_width=True, disabled=is_asset_invalid):
        EquipmentTrackingService.add_tracking(
            order_number,
            service_type,
            int(direct_to_customer),
            subcontract_name,
            customer_send_date,
            gst_receive_date,
            gst_send_sub_date,
            sub_receive_date,
            sub_send_date,
            gst_receive_back_date,
            gst_send_customer_date,
            customer_receive_date,
            note
        )
        st.success("🎉 Asset lifecycle operational matrices updated.")
        st.rerun()

    st.divider()

    # --- SLA CALCULATION DATA PIPELINE ---
    tracking_df = EquipmentTrackingRepository.get_all()
    working_days_list = []

    for _, row in tracking_df.iterrows():
        working_days_list.append(
            working_days_between(row["customer_send_date"], row["customer_receive_date"])
        )

    tracking_df["working_days"] = working_days_list

    def calculate_sla(row):
        if row["working_days"] is None:
            return "In Progress"
        if row["service_type"] == "LAB":
            if row["working_days"] > 3: return "OVER SLA"
            if row["working_days"] == 2: return "WARNING"
            return "OK"
        if row["service_type"] == "SUBCONTRACT_LAB":
            if row["working_days"] > 7: return "OVER SLA"
            if row["working_days"] == 6: return "WARNING"
            return "OK"

    tracking_df["sla_status"] = tracking_df.apply(calculate_sla, axis=1)

    ok_count = len(tracking_df[tracking_df["sla_status"] == "OK"])
    warning_count = len(tracking_df[tracking_df["sla_status"] == "WARNING"])
    over_sla_count = len(tracking_df[tracking_df["sla_status"] == "OVER SLA"])
    in_progress_count = len(tracking_df[tracking_df["sla_status"] == "In Progress"])

    st.subheader("📊 Operational SLA Matrix Performance Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🟢 SLA Compliant (OK)", ok_count)
    with col2: st.metric("🟡 Threshold Alert (Warning)", warning_count)
    with col3: st.metric("🔴 Critical Breach (Over SLA)", over_sla_count)
    with col4: st.metric("⚪ Pipeline Active (In Progress)", in_progress_count)

    st.divider()
    
    # Bảng hiển thị thông minh tích hợp bộ định màu SLA (Loại bỏ selectbox Rows per page cũ kĩ)
    render_aggrid(tracking_df, height=500, page_size=10, color_sla=True, key="equipment_tracking_main_grid")

    st.divider()
    
    # --- MÔ-ĐUN XÓA LOG THIẾT BỊ ---
    delete_options = {
        f"ID {row['id']} | Order: {row['order_number']}": row["id"] for _, row in tracking_df.iterrows()
    }
    
    if delete_options:
        selected_delete = st.selectbox("Select Target Lifecycle Record to Void", list(delete_options.keys()))

        if st.button("🗑️ Void Selected Asset Lifecycle Log", use_container_width=True):
            EquipmentTrackingService.delete_tracking(delete_options[selected_delete])
            st.success("Target asset operational footprint successfully scrubbed.")
            st.rerun()