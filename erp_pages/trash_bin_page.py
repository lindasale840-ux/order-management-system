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

    selected_restore_order = st.selectbox(

        "Select Order To Restore",

        order_options

    )

    st.divider()

    st.subheader(
        "☠ Permanent Delete"
    )

    selected_permanent_order = st.selectbox(

        "Select Order To Permanently Delete",

        order_options,

        key="permanent_delete_order"

    )

    confirm_permanent_delete = st.checkbox(

        "I understand this action cannot be undone",

        key="confirm_permanent_delete"

    )

    if st.button(

        "☠ Permanent Delete"

    ):

        if not confirm_permanent_delete:

            st.error(

                "Please confirm first"

            )

        else:

            DashboardService.permanent_delete_order(

                selected_permanent_order

            )

            st.success(

                f"Permanently deleted {selected_permanent_order}"

            )

            st.rerun()

    confirm_restore = st.checkbox(

        "I confirm restore this order"

    )

    if st.button(

        "♻ Restore Order"

    ):

        if not confirm_restore:

            st.error(

                "Please confirm first"

            )

        else:

            DashboardService.restore_order(

                selected_restore_order

            )

            st.success(

                f"Restored {selected_restore_order}"

            )

            st.rerun()