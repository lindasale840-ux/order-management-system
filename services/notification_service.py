from services.finance_service import FinanceService

class NotificationService:

    @staticmethod
    def get_notifications():

        df = (
            FinanceService
            .build_finance_dataframe()
        )

        overdue_payment = df[
            df["payment_overdue"] == "Overdue"
        ]

        missing_invoice = df[
            df["order_status"] == "Missing Invoice"
        ]

        return (
            overdue_payment,
            missing_invoice
        )