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
        
    @staticmethod
    def transfer_assistant_orders(
        order_numbers,
        new_assistant
    ):

        PaymentRepository.transfer_invoice_owner_by_orders(

            order_numbers,

            new_assistant

        )

        LogRepository.add_log(

            "TRANSFER_ASSISTANT_ORDER",

            "",

            "",

            f"{len(order_numbers)} orders -> {new_assistant}"

        )


    @staticmethod
    def transfer_sale_orders(
        order_numbers,
        new_sale
    ):

        OrderRepository.transfer_sale_owner_by_orders(

            order_numbers,

            new_sale

        )

        LogRepository.add_log(

            "TRANSFER_SALE_ORDER",

            "",

            "",

            f"{len(order_numbers)} orders -> {new_sale}"

        )    