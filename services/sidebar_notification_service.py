from services.finance_service import FinanceService
from repositories.document_tracking_repository import DocumentTrackingRepository
import pandas as pd
from config.app_config import DOCUMENT_WARNING_DAYS
import streamlit as st
class SidebarNotificationService:

    @staticmethod
    def get_alert_summary(username: str):
        # Truyền username vào build_finance_dataframe để làm mới bộ đệm (cache key) theo từng user
        # Lấy thông tin định danh phân quyền hiện tại từ session_state
        current_role = st.session_state.get("role")
        current_owner = st.session_state.get("sale_owner")
        
        # Gọi hàm lần 1: Đã truyền đủ tham số
        df = FinanceService.build_finance_dataframe(role=current_role, username=username, sale_owner=current_owner)

        missing_cert = len(
            df[df["cert_workflow_status"] == "Missing Cert"]
        )

        # ĐÃ CẬP NHẬT: Thêm điều kiện loại trừ các đơn hàng có disable_payment_notification == 1
        payment_overdue = len(
            df[
                (df["payment_overdue"] == "Overdue")
                & (df["disable_payment_notification"] != 1)
            ]
        )

        due_soon = len(
            df[df["cert_due_soon"] == "Due Soon"]
        )

        missing_invoice = len(
            df[df["order_status"] == "Missing Invoice"]
        )

        missing_send = 0
        pending_return = 0

        tracking_df = DocumentTrackingRepository.get_latest_tracking()
        df = FinanceService.build_finance_dataframe(role=current_role, username=username, sale_owner=current_owner)
        allowed_orders = set(
            df["order_number"].astype(str)
        )

        tracking_df = tracking_df[
            tracking_df["order_number"].astype(str)
            .isin(allowed_orders)
        ]
        today = pd.Timestamp.today()

        # =========================
        # Missing Send
        # =========================
        sent_orders = set()
        if not tracking_df.empty:
            sent_orders = set(tracking_df["order_number"].astype(str))

        cert_orders_df = df[df["cert_status"].notna()].copy()
        cert_orders_df["cert_status"] = pd.to_datetime(
            cert_orders_df["cert_status"],
            errors="coerce"
        )

        ignore_orders = set(
            df[df["disable_document_notification"] == 1]["order_number"]
        )

        missing_send_df = cert_orders_df[
            (today - cert_orders_df["cert_status"]).dt.days.gt(DOCUMENT_WARNING_DAYS)
            & ~cert_orders_df["order_number"].astype(str).isin(sent_orders)
            & ~cert_orders_df["order_number"].astype(str).isin(ignore_orders)
        ]

        missing_send = len(missing_send_df)

        # =========================
        # Pending Return
        # =========================
        if not tracking_df.empty:
            tracking_df["sent_date"] = pd.to_datetime(
                tracking_df["sent_date"],
                errors="coerce"
            )
            tracking_df["received_date"] = pd.to_datetime(
                tracking_df["received_date"],
                errors="coerce"
            )

            pending_return_df = tracking_df[
                tracking_df["received_date"].isna()
                & (today - tracking_df["sent_date"]).dt.days.gt(DOCUMENT_WARNING_DAYS)
            ]
            
            pending_return_df = pending_return_df[
                ~pending_return_df["order_number"].astype(str).isin(ignore_orders)
            ]

            pending_return = len(pending_return_df)

        total_alert = (
            missing_cert
            + payment_overdue
            + due_soon
            + missing_invoice
            + missing_send
            + pending_return
        )

        return {
            "total": total_alert,
            "missing_cert": missing_cert,
            "payment_overdue": payment_overdue,
            "due_soon": due_soon,
            "missing_invoice": missing_invoice,
            "missing_send": missing_send,
            "pending_return": pending_return
        }