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
        cert_status
    ):

        OrderRepository.upsert_order(

            customer_name,

            order_number,

            measurement_date,

            cert_status
        )

        LogRepository.add_log(

            "SYNC_ORDER",

            customer_name,

            order_number,

            f"""
            Sync order:
            customer={customer_name},
            order={order_number},
            measurement_date={measurement_date},
            cert_status={cert_status}
            """
        )