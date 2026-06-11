import streamlit as st

from repositories.payment_repository import (
    PaymentRepository
)

from repositories.log_repository import (
    LogRepository
)

from repositories.order_repository import (
    OrderRepository
)


class PaymentService:

    @staticmethod
    def save_invoice(
        order_number,
        invoice_date,
        invoice_group,
        payment_terms,
        payment_status,
        total,
        commission_percent,
        note
    ):

        commission_actual = (
            total * commission_percent / 100
        )

        PaymentRepository.upsert_payment(

            order_number,

            invoice_date,

            invoice_group,

            payment_terms,

            payment_status,

            total,

            commission_percent,

            commission_actual,

            note,
            
            st.session_state["username"]
        )

        OrderRepository.update_invoice_group(

            order_number,

            invoice_group
        )

        LogRepository.add_log(

            "SAVE_INVOICE",

            "",

            order_number,

            f"{invoice_group} | {total:,.0f}"
        )