from repositories.order_repository import (
    OrderRepository
)

from repositories.log_repository import (
    LogRepository
)


class DashboardService:

    @staticmethod
    def sync_order(
        customer_name,
        order_number,
        measurement_date,
        cert_status,
        sale_owner
    ):

        OrderRepository.upsert_order(

            customer_name,

            order_number,

            measurement_date,

            cert_status,

            sale_owner
        )

        LogRepository.add_log(

            "SYNC_ORDER",

            customer_name,

            order_number,

            f"{customer_name} | {order_number}"
        )

    @staticmethod
    def move_to_trash(

        order_number,

        deleted_by

    ):

        OrderRepository.soft_delete_order(

            order_number,

            deleted_by

        )

        LogRepository.add_log(

            "MOVE_TO_TRASH",

            "",

            order_number,

            f"Move order {order_number} to trash"

        )

    @staticmethod
    def restore_order(

        order_number

    ):

        OrderRepository.restore_order(

            order_number

        )

        LogRepository.add_log(

            "RESTORE_ORDER",

            "",

            order_number,

            f"Restore order {order_number}"

        ) 

    @staticmethod
    def permanent_delete_order(

        order_number

    ):

        OrderRepository.delete_order_cascade(

            order_number

        )

        LogRepository.add_log(

            "PERMANENT_DELETE",

            "",

            order_number,

            f"Permanent delete order {order_number}"

        )  


    @staticmethod
    def bulk_move_to_trash(

        order_numbers,

        deleted_by

    ):

        for order_number in order_numbers:

            OrderRepository.soft_delete_order(

                order_number,

                deleted_by

            )

            LogRepository.add_log(

                "MOVE_TO_TRASH",

                "",

                order_number,

                f"Move order {order_number} to trash"

            )         