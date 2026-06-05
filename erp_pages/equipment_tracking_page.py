import streamlit as st

from repositories.order_repository import (
    OrderRepository
)

from repositories.equipment_tracking_repository import (
    EquipmentTrackingRepository
)

from services.equipment_tracking_service import (
    EquipmentTrackingService
)

from components.aggrid_table import (
    render_aggrid
)

def show_equipment_tracking_page():

    st.title(
        "📦 Equipment Tracking"
    )

    orders_df = (
        OrderRepository.get_all_orders()
    )

    order_number = st.selectbox(

        "Order",

        orders_df[
            "order_number"
        ].tolist()
    )

    service_type = st.selectbox(

        "Service Type",

        [

            "LAB",

            "SUBCONTRACT_LAB"

        ]
    )

    direct_to_customer = st.checkbox(
        "Subcontract Direct To Customer"
    )

    subcontract_name = st.text_input(
        "Subcontract Name"
    )

    customer_send_date = st.date_input(
        "Customer Send Date"
    )

    gst_receive_date = st.date_input(
        "GST Receive Date"
    )

    gst_send_sub_date = st.date_input(
        "GST Send To Subcontract"
    )

    sub_receive_date = st.date_input(
        "Subcontract Receive"
    )

    sub_send_date = st.date_input(
        "Subcontract Send Back"
    )

    gst_receive_back_date = st.date_input(
        "GST Receive Back"
    )

    gst_send_customer_date = st.date_input(
        "GST Send Customer"
    )

    customer_receive_date = st.date_input(
        "Customer Receive"
    )

    note = st.text_area(
        "Note"
    )

    if st.button(
        "Save Tracking"
    ):

        EquipmentTrackingService.add_tracking(

            order_number,

            service_type,

            int(
                direct_to_customer
            ),

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

        st.success(
            "Tracking saved"
        )

        st.rerun()

    st.divider()

    tracking_df = (
        EquipmentTrackingRepository
        .get_all()
    )

    render_aggrid(

        tracking_df,

        height=500,

        page_size=10
    )