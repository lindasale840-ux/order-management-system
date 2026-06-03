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

    customer_df = (
        OrderRepository.get_customers()
    )

    customer_options = [
        "ALL"
    ] + customer_df[
        "customer_name"
    ].tolist()

    selected_customer = st.selectbox(
        "Filter Customer",
        customer_options
    )

    if selected_customer == "ALL":

        order_df = (
            OrderRepository.get_all_orders()
        )

        order_df = filter_by_sale_owner(
            order_df
        )

    else:

        order_df = (
            OrderRepository
            .get_orders_by_customer(
                selected_customer
            )
        )

    order_list = (
        order_df["order_number"]
        .tolist()
    )

    if not order_list:

        st.warning("No orders")
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

    if existing_data.get(
        "invoice_date"
    ):

        invoice_date_value = (
            pd.to_datetime(
                existing_data[
                    "invoice_date"
                ]
            ).date()
        )

    payment_status_saved = (
        existing_data.get(
            "payment_status"
        )
    )

    unpaid_default = pd.isna(
        payment_status_saved
    )

    if unpaid_default:

        payment_status_value = (
            date.today()
        )

    else:

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
            value=int(
                existing_data.get(
                    "payment_terms",
                    0
                ) or 0
            )
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

            invoice_group,

            invoice_date,

            payment_terms,

            payment_status,

            total,

            commission_percent,

            note
        )

        st.success(
            "Invoice saved"
        )

        st.rerun()