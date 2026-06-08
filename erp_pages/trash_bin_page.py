import streamlit as st

from repositories.order_repository import (
    OrderRepository
)

from components.aggrid_table import (
    render_aggrid
)

from utils.auth_guard import (
    require_editor
)

from services.dashboard_service import (
    DashboardService
)

def show_trash_bin_page():

    require_editor()

    st.title(
        "🗑 Trash Bin"
    )

    deleted_df = (
        OrderRepository
        .get_deleted_orders()
    )

    if deleted_df.empty:

        st.success(
            "Trash bin is empty"
        )

        return

    display_df = deleted_df[

        [

            "customer_name",

            "order_number",

            "deleted_at",

            "deleted_by"

        ]

    ].copy()

    render_aggrid(

        display_df,

        height=500,

        page_size=20

    )

    st.info(

        f"Deleted Orders: {len(display_df)}"

    )

    st.divider()

    order_options = (

        deleted_df["order_number"]

        .tolist()

    )

    st.subheader(
    "♻ Restore Order"
    )

    selected_restore_orders = st.multiselect(

        "Select Orders To Restore",

        options=order_options,

        key="restore_orders"

    )

    confirm_restore = st.checkbox(

        "I confirm restore selected orders",

        key="confirm_restore"

    )

    if st.button(

        "♻ Restore Selected"

    ):

        if not selected_restore_orders:

            st.error(

                "Please select at least one order"

            )

        elif not confirm_restore:

            st.error(

                "Please confirm first"

            )

        else:

            DashboardService.bulk_restore_orders(

                selected_restore_orders

            )

            st.success(

                f"Restored {len(selected_restore_orders)} orders"

            )

            st.rerun()

    st.divider()

    st.subheader(
    "☠ Permanent Delete"
    )

    selected_permanent_orders = st.multiselect(

        "Select Orders To Permanently Delete",

        options=order_options,

        key="permanent_delete_orders"

    )

    confirm_permanent_delete = st.checkbox(

        "I understand this action cannot be undone",

        key="confirm_permanent_delete"

    )

    if st.button(

        "☠ Permanent Delete Selected"

    ):

        if not selected_permanent_orders:

            st.error(

                "Please select at least one order"

            )

        elif not confirm_permanent_delete:

            st.error(

                "Please confirm first"

            )

        else:

            DashboardService.bulk_permanent_delete_orders(

                selected_permanent_orders

            )

            st.success(

                f"Permanently deleted {len(selected_permanent_orders)} orders"

            )

            st.rerun()