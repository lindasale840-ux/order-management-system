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