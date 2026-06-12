from repositories.order_repository import (
    OrderRepository
)

from repositories.payment_repository import (
    PaymentRepository
)

from repositories.log_repository import (
    LogRepository
)


class OwnershipTransferService:

    @staticmethod
    def transfer_assistant(
        old_assistant,
        new_assistant
    ):

        PaymentRepository.bulk_transfer_invoice_owner(

            old_assistant,

            new_assistant

        )

        LogRepository.add_log(

            "TRANSFER_ASSISTANT",

            "",

            "",

            f"{old_assistant} -> {new_assistant}"

        )

    @staticmethod
    def transfer_sale(
        old_sale,
        new_sale
    ):

        OrderRepository.bulk_transfer_sale_owner(

            old_sale,

            new_sale

        )

        LogRepository.add_log(

            "TRANSFER_SALE",

            "",

            "",

            f"{old_sale} -> {new_sale}"

        )