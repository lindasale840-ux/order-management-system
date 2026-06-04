import streamlit as st
import pandas as pd

from services.dashboard_service import DashboardService
from repositories.order_repository import OrderRepository

from components.pagination import (
    paginate_dataframe
)

from utils.data_permission import (
    filter_by_sale_owner
)

from utils.auth_guard import (
    require_editor
)

def show_dashboard_page():

    require_editor()

    st.title("Dashboard")

    tab1, tab2 = st.tabs([
        "Manual Input",
        "Excel Import"
    ])

    with tab1:

        col1, col2 = st.columns(2)

        with col1:

            customer_name = st.text_input(
                "Customer Name"
            )

            order_number = st.text_input(
                "Order Number"
            )

        with col2:

            measurement_date = st.date_input(
                "Measurement Date"
            )

            no_cert = st.checkbox(
                "No Cert Yet"
            )

            if no_cert:

                cert_status = None

                st.info(
                    "Cert status will be empty"
                )

            else:

                cert_status = st.date_input(
                    "Cert Status"
                )

        if st.button("Sync Order"):

            if not customer_name:

                st.error("Customer required")
                st.stop()

            if not order_number:

                st.error("Order required")
                st.stop()

            DashboardService.sync_order(

                customer_name,

                order_number,

                measurement_date,

                cert_status,

                st.session_state["sale_owner"]
            )

            st.success("Order synced")

    with tab2:

        uploaded_file = st.file_uploader(
            "Upload Excel",
            type=["xlsx"]
        )

        if uploaded_file:

            excel_df = pd.read_excel(
                uploaded_file
            )

            st.dataframe(
                excel_df,
                width="stretch"
            )

            if st.button(
                "Bulk Sync Excel"
            ):

                for _, row in excel_df.iterrows():

                    DashboardService.sync_order(

                        row["customer_name"],

                        row["order_number"],

                        row["measurement_date"],

                        row.get(
                            "cert_status",
                            None
                        ),

                        st.session_state["sale_owner"]
                    )

                st.success(
                    "Excel synced"
                )

    st.divider()

    df = OrderRepository.get_all_orders()

    df = filter_by_sale_owner(df)

    st.metric(
        "Total Orders",
        len(df)
    )

    # =========================
    # SEARCH
    # =========================

    search_text = st.text_input(
        "🔍 Search Customer / Order / Invoice Group"
    )

    if search_text:

        search_text = (
            search_text
            .strip()
            .lower()
        )

        customer_match = (

            df["customer_name"]

            .astype(str)

            .str.lower()

            .str.contains(
                search_text,
                na=False
            )
        )

        order_match = (

            df["order_number"]

            .astype(str)

            .str.lower()

            .str.contains(
                search_text,
                na=False
            )
        )

        invoice_match = (

            df["invoice_group"]

            .astype(str)

            .str.lower()

            .str.contains(
                search_text,
                na=False
            )
        )

        df = df[

            customer_match

            |

            order_match

            |

            invoice_match
        ]

    from components.aggrid_table import (
    render_aggrid
    )

    page_size = st.selectbox(

        "Rows per page",

        [5, 10, 20, 50],

        index=0,

        key="dashboard_page_size"
    )

    render_aggrid(

        df,

        height=500,

        page_size=page_size
    )

    st.divider()

    st.subheader(
        "🗑 Delete Order"
    )

    order_options = (
        df["order_number"]
        .tolist()
    )

    if order_options:

        selected_delete_order = st.selectbox(

            "Select Order To Delete",

            order_options,

            key="delete_order_select"
        )

        if st.button(
            "🗑 Delete Order"
        ):

            DashboardService.delete_order(
                selected_delete_order
            )

            st.success(
                f"Deleted {selected_delete_order}"
            )

            st.rerun()

    else:

        st.info(
            "No orders available"
        )