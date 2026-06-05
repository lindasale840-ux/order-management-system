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

from utils.business_day import (
    working_days_between
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

    customer_options = [

        "ALL"

    ] + sorted(

        orders_df[
            "customer_name"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_customer = st.selectbox(

        "Customer",

        customer_options
    )

    if selected_customer != "ALL":

        orders_df = orders_df[

            orders_df[
                "customer_name"
            ]
            == selected_customer
        ]


    order_number = st.selectbox(

        "Order",

        orders_df[
            "order_number"
        ].tolist()
    )

    existing_tracking = (

        EquipmentTrackingRepository
        .get_by_order_number(
            order_number
        )

    )

    if not existing_tracking.empty:

        tracking = existing_tracking.iloc[0]

    else:

        tracking = None

    service_default = "LAB"

    if tracking is not None:

        service_default = tracking[
            "service_type"
        ]

    service_type = st.selectbox(

        "Service Type",

        [

            "LAB",

            "SUBCONTRACT_LAB"

        ],

        index=[

            "LAB",

            "SUBCONTRACT_LAB"

        ].index(
            service_default
        )
    )

    direct_to_customer = st.checkbox(
        "Subcontract Direct To Customer"
    )


    customer_send_date = st.date_input(
        "Customer Send Date"
    )

    gst_receive_date = st.date_input(
        "GST Receive Date"
    )

    subcontract_name = ""

    gst_send_sub_date = None
    sub_receive_date = None
    sub_send_date = None
    gst_receive_back_date = None

    if service_type == "SUBCONTRACT_LAB":

        subcontract_name = st.text_input(

            "Subcontract Name",

            value=(

                tracking[
                    "subcontract_name"
                ]

                if tracking is not None

                else ""

            )
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

        if not direct_to_customer:

            gst_receive_back_date = st.date_input(
                "GST Receive Back"
            )

    if (

        service_type == "LAB"

        or

        (
            service_type == "SUBCONTRACT_LAB"
            and
            not direct_to_customer
        )

    ):

        gst_send_customer_date = st.date_input(
            "GST Send Customer"
        )

    else:

        gst_send_customer_date = None

    not_receive_yet = st.checkbox(
        "Not Receive Yet"
    )

    if not_receive_yet:

        customer_receive_date = None

    else:

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

    working_days_list = []

    for _, row in tracking_df.iterrows():

        working_days_list.append(

            working_days_between(

                row["customer_send_date"],

                row["customer_receive_date"]

            )

        )

    tracking_df["working_days"] = working_days_list

    def calculate_sla(row):

        if row["working_days"] is None:

            return "In Progress"

        if row["service_type"] == "LAB":

            if row["working_days"] > 3:

                return "OVER SLA"

            return "OK"

        if row["service_type"] == "SUBCONTRACT_LAB":

            if row["working_days"] > 7:

                return "OVER SLA"

            return "OK"

        return ""

    tracking_df["sla_status"] = (

        tracking_df.apply(

            calculate_sla,

            axis=1
        )
    )
    render_aggrid(

        tracking_df,

        height=500,

        page_size=10
    )

    st.divider()

    delete_options = {

        f"ID {row['id']} | "
        f"{row['order_number']}":

        row["id"]

        for _, row in tracking_df.iterrows()
    }

    selected_delete = st.selectbox(

        "Delete Tracking",

        list(delete_options.keys())
    )

    if st.button(
        "🗑 Delete Tracking"
    ):

        EquipmentTrackingService.delete_tracking(

            delete_options[
                selected_delete
            ]
        )

        st.success(
            "Tracking deleted"
        )

        st.rerun()