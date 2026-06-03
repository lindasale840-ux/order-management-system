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

            f"""
            Sync order:
            customer={customer_name},
            order={order_number},
            measurement_date={measurement_date},
            cert_status={cert_status},
            sale_owner={sale_owner}
            """
        )