from repositories.payment_repository import (
    PaymentRepository
)

from repositories.log_repository import (
    LogRepository
)


class PaymentService:

    @staticmethod
    def save_invoice(
        order_number,
        invoice_date,
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

            payment_terms,

            payment_status,

            total,

            commission_percent,

            commission_actual,

            note
        )

        LogRepository.add_log(

            "SAVE_INVOICE",

            "",

            order_number,

            f"""
            Save invoice:
            order={order_number},
            invoice_date={invoice_date},
            payment_terms={payment_terms},
            payment_status={payment_status},
            total={total},
            commission_percent={commission_percent},
            commission_actual={commission_actual},
            note={note}
            """
        )