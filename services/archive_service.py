from repositories.order_repository import (
    OrderRepository
)

from repositories.payment_repository import (
    PaymentRepository
)

from repositories.document_tracking_repository import (
    DocumentTrackingRepository
)

from repositories.log_repository import (
    LogRepository
)

from repositories.error_log_repository import (
    ErrorLogRepository
)

from repositories.user_repository import (
    UserRepository
)

from utils.excel_export import (
    dataframe_to_excel
)


class ArchiveService:

    @staticmethod
    def export_full_archive():

        orders_df = (
            OrderRepository.get_all_orders()
        )

        payments_df = (
            PaymentRepository.get_all_payments()
        )

        tracking_df = (
            DocumentTrackingRepository.get_all()
        )

        logs_df = (
            LogRepository.get_logs()
        )

        error_logs_df = (
            ErrorLogRepository.get_errors()
        )

        users_df = (
            UserRepository.get_all_users()
        )

        return dataframe_to_excel({

            "Orders": orders_df,

            "Payments": payments_df,

            "Document Tracking": tracking_df,

            "Logs": logs_df,

            "Error Logs": error_logs_df,

            "Users": users_df
        })