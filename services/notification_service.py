from services.finance_service import FinanceService

class NotificationService:

    @staticmethod
    def get_notifications():
        df = FinanceService.build_finance_dataframe()

        # ĐÃ CẬP NHẬT: Loại trừ các đơn hàng có disable_payment_notification == 1
        overdue_payment = df[
            (df["payment_overdue"] == "Overdue") 
            & (df["disable_payment_notification"] != 1)
        ]

        missing_invoice = df[
            df["order_status"] == "Missing Invoice"
        ]

        return (
            overdue_payment,
            missing_invoice
        )