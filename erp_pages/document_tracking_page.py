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

    

    # =========================
    # SEARCH ORDER
    # =========================

    search_text = st.text_input(
        "🔍 Search Order / Customer"
    )

    filtered_df = orders_df.copy()

    if search_text:

        filtered_df = filtered_df[

            filtered_df["display"]

            .str.contains(
                search_text,
                case=False,
                na=False
            )
        ]

    filtered_order_map = {

        row["display"]:
        row["order_number"]

        for _, row in filtered_df.iterrows()
    }

    col1, col2 = st.columns(2)

    with col1:

        if filtered_order_map:

            selected_display = st.selectbox(

                "Order",

                list(filtered_order_map.keys())
            )
            
            selected_order = filtered_order_map[
                selected_display
            ]

            latest_tracking = (

                DocumentTrackingRepository
                .get_latest_by_order(
                    selected_order
                )

            )

            existing_data = {}

            if not latest_tracking.empty:

                existing_data = (
                    latest_tracking.iloc[0]
                    .to_dict()
                )

        else:

            st.warning(
                "No matching order found"
            )

            st.stop()

        sent_date_value = pd.Timestamp.today().date()

        if existing_data.get("sent_date") is not None:

            sent_date_value = pd.to_datetime(
                existing_data["sent_date"]
            ).date()

        sent_date = st.date_input(

            "Sent Date",

            value=sent_date_value

        )

    with col2:

        received_date_saved = (
            existing_data.get(
                "received_date"
            )
        )

        not_received = pd.isna(
            received_date_saved
        )

        not_received = st.checkbox(

            "Not Received Yet",

            value=not_received

        )

        if not_received:

            received_date = None

        else:

            received_date_value = (
                pd.Timestamp.today().date()
            )

            if pd.notna(received_date_saved):

                received_date_value = (
                    pd.to_datetime(
                        received_date_saved
                    ).date()
                )

            received_date = st.date_input(

                "Received Date",

                value=received_date_value

            )

        note = st.text_input(

            "Note",

            value=str(

                existing_data.get(
                    "note",
                    ""
                ) or ""

            )

        )

    if st.button(
        "💾 Add Tracking"
    ):

        DocumentTrackingService.add_tracking(

            filtered_order_map[
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