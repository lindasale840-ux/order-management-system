from services.finance_service import FinanceService
import streamlit as st
class NotificationService:

    @staticmethod
    def get_notifications():
        df = FinanceService.build_finance_dataframe(
            role=st.session_state.get("role"),
            username=st.session_state.get("username"),
            sale_owner=st.session_state.get("sale_owner")
        )

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