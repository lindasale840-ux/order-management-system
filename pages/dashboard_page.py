import streamlit as st
import pandas as pd

from services.dashboard_service import DashboardService
from repositories.order_repository import OrderRepository

from components.pagination import (
    paginate_dataframe
)

from utils.auth_guard import (
    require_admin
)

def show_dashboard_page():

    require_admin()
    
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

                cert_status
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
                use_container_width=True
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
                        )
                    )

                st.success(
                    "Excel synced"
                )

    st.divider()

    df = OrderRepository.get_all_orders()

    st.metric(
        "Total Orders",
        len(df)
    )

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