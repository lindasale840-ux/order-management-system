import streamlit as st
import pandas as pd
from datetime import date

from repositories.order_repository import (
    OrderRepository
)

from repositories.payment_repository import (
    PaymentRepository
)

from services.payment_service import (
    PaymentService
)

from utils.data_permission import (
    filter_by_sale_owner
)

from utils.auth_guard import (
    require_editor
)


def show_payment_page():

    require_editor()

    st.title("Payment")
    
    if st.session_state.get("invoice_saved"):

        st.success("Invoice saved")

        st.session_state["invoice_saved"] = False

    customer_df = (
        OrderRepository.get_customers()
    )

    customer_options = [
        "ALL"
    ] + customer_df[
        "customer_name"
    ].tolist()
    
    # =========================
    # GLOBAL SEARCH
    # =========================

    search_keyword = st.text_input(
        "🔍 Search Customer / Order Number"
    ).strip()
    
    # =========================
    # SEARCH CUSTOMER
    # =========================

    # search_customer = st.text_input(
       #  "🔍 Search Customer"
    # )

    # if search_customer:

        # filtered_customers = [

        #     c for c in customer_options

         #    if search_customer.lower() in c.lower()

       #  ]

   #  else:

      #   filtered_customers = customer_options

    order_df = (
        OrderRepository.get_all_orders()
    )

    order_df = filter_by_sale_owner(
        order_df
    )

    # =========================
    # SEARCH FILTER
    # =========================

    if search_keyword:

        order_df = order_df[

            order_df["customer_name"]
            .astype(str)
            .str.contains(
                search_keyword,
                case=False,
                na=False
            )

            |

            order_df["order_number"]
            .astype(str)
            .str.contains(
                search_keyword,
                case=False,
                na=False
            )

        ]

    order_list = (
        order_df["order_number"]
        .tolist()
    )

    if not order_list:

        st.warning("No orders")
        return

    if order_df.empty:

        st.warning(
            "No matching customer or order found"
        )

        return
    
    selected_order = st.selectbox(
        "Order Number",
        order_list
    )

    payment_df = (
        PaymentRepository
        .get_all_payments()
    )

    existing = payment_df[
        payment_df["order_number"]
        == selected_order
    ]

    existing_data = {}

    if not existing.empty:

        existing_data = (
            existing.iloc[0]
            .to_dict()
        )

    invoice_group = st.text_input(
        "Invoice Group",
        value=str(
            existing_data.get(
                "invoice_group",
                ""
            ) or ""
        )
    )
    

    # =========================
    # LOAD SAVED DATES
    # =========================

    invoice_date_value = date.today()

    invoice_date_raw = (
        existing_data.get(
            "invoice_date"
        )
    )

    if pd.notna(
        invoice_date_raw
    ):

        invoice_date_value = (
            pd.to_datetime(
                invoice_date_raw
            ).date()
        )

    payment_status_saved = (
    existing_data.get(
        "payment_status"
    )
)

    if pd.isna(
        payment_status_saved
    ):

        unpaid_default = True

        payment_status_value = (
            date.today()
        )

    else:

        unpaid_default = False

        payment_status_value = (
            pd.to_datetime(
                payment_status_saved
            ).date()
        )

    col1, col2 = st.columns(2)

    with col1:

        invoice_date = st.date_input(
            "Invoice Date",
            value=invoice_date_value
        )

        payment_terms = st.number_input(
            "Payment Terms",
            min_value=0,
            max_value=365,
            value=min(
                int(
                    existing_data.get(
                        "payment_terms",
                        0
                    ) or 0
                ),
                365
            ),
            step=1
        )

        total = st.number_input(
            "Total",
            min_value=0.0,
            value=float(
                existing_data.get(
                    "total",
                    0
                ) or 0
            )
        )

    with col2:

        unpaid = st.checkbox(
            "Not Paid Yet",
            value=unpaid_default
        )

        if unpaid:

            payment_status = None

            st.info(
                "Payment status empty"
            )

        else:

            payment_status = (
                st.date_input(
                    "Payment Status",
                    value=payment_status_value
                )
            )

        commission_percent = st.number_input(
            "Commission %",
            min_value=0.0,
            value=float(
                existing_data.get(
                    "commission_percent",
                    0
                ) or 0
            )
        )

        note = st.text_area(
            "Note",
            value=str(
                existing_data.get(
                    "note",
                    ""
                ) or ""
            )
        )

    commission_actual = (
        total
        * commission_percent
        / 100
    )

    st.metric(
        "Commission Actual",
        f"{commission_actual:,.2f}"
    )

    if st.button(
        "Save Invoice"
    ):

        PaymentService.save_invoice(

            selected_order,

            invoice_date,

            invoice_group,

            payment_terms,

            payment_status,

            total,

            commission_percent,

            note
        )

        st.session_state["invoice_saved"] = True

        st.rerun()