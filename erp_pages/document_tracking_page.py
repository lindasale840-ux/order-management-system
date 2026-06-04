import streamlit as st

import pandas as pd

from repositories.order_repository import (
    OrderRepository
)

from repositories.document_tracking_repository import (
    DocumentTrackingRepository
)

from services.document_tracking_service import (
    DocumentTrackingService
)

from components.aggrid_table import (
    render_aggrid
)

from utils.excel_export import (
    dataframe_to_excel
)

from utils.auth_guard import (
    require_editor
)


def show_document_tracking_page():

    require_editor()

    st.title(
        "📨 Document Tracking"
    )

    orders_df = (
        OrderRepository.get_all_orders()
    )

    orders_df["cert_status"] = pd.to_datetime(
        orders_df["cert_status"],
        errors="coerce"
    )

    orders_df = orders_df[
        orders_df["cert_status"].notna()
    ]

    orders_df["display"] = (

        orders_df["order_number"]

        +

        " | "

        +

        orders_df["customer_name"]

        +

        " | Cert: "

        +

        orders_df["cert_status"].dt.strftime(
            "%Y-%m-%d"
        )
    )

    order_map = {

        row["display"]:
        row["order_number"]

        for _, row in orders_df.iterrows()
    }

    col1, col2 = st.columns(2)

    with col1:

        selected_display = st.selectbox(

            "Order",

            list(order_map.keys())
        )

        sent_date = st.date_input(
            "Sent Date"
        )

    with col2:

        not_received = st.checkbox(
            "Not Received Yet"
        )

        if not_received:

            received_date = None

            st.info(
                "Received date will be empty"
            )

        else:

            received_date = st.date_input(
                "Received Date"
            )

        note = st.text_input(
            "Note"
        )

    if st.button(
        "💾 Add Tracking"
    ):

        DocumentTrackingService.add_tracking(

            order_map[
                selected_display
            ],

            sent_date,

            received_date,

            note
        )

        st.success(
            "Tracking added"
        )

        st.rerun()

    st.divider()

    tracking_df = (

        DocumentTrackingRepository
        .get_all()
    )

    if tracking_df.empty:

        st.info(
            "No tracking data"
        )

        return
    

    # =========================
    # SEARCH
    # =========================

    search_text = st.text_input(
    "🔍 Search Order / Customer / Note"
    )

    if search_text:

        keyword = search_text.lower()

        tracking_df = tracking_df[

            tracking_df.astype(str)

            .apply(
                lambda col:
                col.str.lower()
            )

            .apply(
                lambda col:
                col.str.contains(
                    keyword,
                    na=False
                )
            )

            .any(axis=1)
        ]
    render_aggrid(

        tracking_df,

        height=400,

        page_size=10
    )

    excel_data = dataframe_to_excel({

        "Document Tracking":
        tracking_df

    })

    st.download_button(

        "📥 Export Excel",

        data=excel_data,

        file_name="document_tracking.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    st.divider()

    delete_options = {

        f"ID {row['id']} | "
        f"{row['order_number']} | "
        f"{row['sent_date']}":

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

        DocumentTrackingService.delete_tracking(

            delete_options[
                selected_delete
            ]
        )

        st.success(
            "Deleted"
        )

        st.rerun()